"""Windows SendInput backend with foreground and physical-input interlocks.

Hooks are temporary, never log keys, never swallow physical input, and ignore
injected events (including UniKey's replacement strokes). No clipboard writes.
"""
import ctypes as C
from ctypes import wintypes as W
from dataclasses import dataclass
from pathlib import PureWindowsPath
import threading
import os

ULONG_PTR = C.c_size_t
LRESULT = C.c_ssize_t
HOOKPROC = C.WINFUNCTYPE(LRESULT, C.c_int, W.WPARAM, W.LPARAM)
MARKER = 0x47565431

class MOUSEINPUT(C.Structure):
    _fields_ = [("dx", W.LONG), ("dy", W.LONG), ("mouseData", W.DWORD), ("dwFlags", W.DWORD), ("time", W.DWORD), ("dwExtraInfo", ULONG_PTR)]

class KEYBDINPUT(C.Structure):
    _fields_ = [("wVk", W.WORD), ("wScan", W.WORD), ("dwFlags", W.DWORD), ("time", W.DWORD), ("dwExtraInfo", ULONG_PTR)]

class HARDWAREINPUT(C.Structure):
    _fields_ = [("uMsg", W.DWORD), ("wParamL", W.WORD), ("wParamH", W.WORD)]

class INPUTUNION(C.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]

class INPUT(C.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", W.DWORD), ("data", INPUTUNION)]

class KBDHOOK(C.Structure):
    _fields_ = [("vkCode", W.DWORD), ("scanCode", W.DWORD), ("flags", W.DWORD), ("time", W.DWORD), ("dwExtraInfo", ULONG_PTR)]

class MOUSEHOOK(C.Structure):
    _fields_ = [("pt", W.POINT), ("mouseData", W.DWORD), ("flags", W.DWORD), ("time", W.DWORD), ("dwExtraInfo", ULONG_PTR)]

class GUITHREADINFO(C.Structure):
    _fields_ = [("cbSize", W.DWORD), ("flags", W.DWORD), ("hwndActive", W.HWND), ("hwndFocus", W.HWND), ("hwndCapture", W.HWND), ("hwndMenuOwner", W.HWND), ("hwndMoveSize", W.HWND), ("hwndCaret", W.HWND), ("rcCaret", W.RECT)]

@dataclass(frozen=True)
class Target:
    hwnd: int
    focus: int
    title: str
    process: str
    layout: int
    pid: int = 0

    def same_destination(self, other):
        # Editors change their title as soon as the first character is typed.
        # Compare the actual window/focus identity, not that display label.
        return (self.hwnd, self.focus, self.process, self.layout, self.pid) == (other.hwnd, other.focus, other.process, other.layout, other.pid)

class WindowsKeyboard:
    def __init__(self, mode="telex"):
        if mode not in ("telex", "unicode"):
            raise ValueError("Chế độ gõ không hợp lệ.")
        self.mode = mode
        self.user = C.WinDLL("user32", use_last_error=True)
        self.kernel = C.WinDLL("kernel32", use_last_error=True)
        self._configure()
        self.armed = False
        self.target = None
        self.thread = None
        self._thread_id = None
        self._ready = threading.Event()
        self._shutdown = threading.Event()
        self._failure = None
        self._signal = threading.Event()
        self._reason = ""

    def _configure(self):
        signatures = {
            "GetForegroundWindow": ([], W.HWND),
            "GetWindowTextW": ([W.HWND, W.LPWSTR, C.c_int], C.c_int),
            "GetClassNameW": ([W.HWND, W.LPWSTR, C.c_int], C.c_int),
            "GetWindowThreadProcessId": ([W.HWND, C.POINTER(W.DWORD)], W.DWORD),
            "GetGUIThreadInfo": ([W.DWORD, C.POINTER(GUITHREADINFO)], W.BOOL),
            "GetKeyboardLayout": ([W.DWORD], W.HANDLE),
            "GetAsyncKeyState": ([C.c_int], C.c_short),
            "GetKeyState": ([C.c_int], C.c_short),
            "VkKeyScanExW": ([W.WCHAR, W.HANDLE], C.c_short),
            "MapVirtualKeyExW": ([W.UINT, W.UINT, W.HANDLE], W.UINT),
            "SendInput": ([W.UINT, C.POINTER(INPUT), C.c_int], W.UINT),
            "SetWindowsHookExW": ([C.c_int, HOOKPROC, W.HINSTANCE, W.DWORD], W.HANDLE),
            "CallNextHookEx": ([W.HANDLE, C.c_int, W.WPARAM, W.LPARAM], LRESULT),
            "UnhookWindowsHookEx": ([W.HANDLE], W.BOOL),
            "GetMessageW": ([C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT], C.c_int),
            "PeekMessageW": ([C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT], W.BOOL),
            "TranslateMessage": ([C.POINTER(W.MSG)], W.BOOL),
            "DispatchMessageW": ([C.POINTER(W.MSG)], LRESULT),
            "PostThreadMessageW": ([W.DWORD, W.UINT, W.WPARAM, W.LPARAM], W.BOOL),
        }
        for name, (args, restype) in signatures.items():
            fn = getattr(self.user, name)
            fn.argtypes, fn.restype = args, restype
        for name, args, restype in [
            ("GetCurrentThreadId", [], W.DWORD),
            ("GetModuleHandleW", [W.LPCWSTR], W.HMODULE),
            ("OpenProcess", [W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
            ("QueryFullProcessImageNameW", [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)], W.BOOL),
            ("CloseHandle", [W.HANDLE], W.BOOL),
        ]:
            fn = getattr(self.kernel, name)
            fn.argtypes, fn.restype = args, restype

    def _snapshot(self):
        hwnd = self.user.GetForegroundWindow()
        if not hwnd:
            raise ValueError("Không tìm thấy cửa sổ đích.")
        title = C.create_unicode_buffer(1024)
        self.user.GetWindowTextW(hwnd, title, len(title))
        pid = W.DWORD()
        thread_id = self.user.GetWindowThreadProcessId(hwnd, C.byref(pid))
        handle = self.kernel.OpenProcess(0x1000, False, pid.value)
        if not handle:
            raise ValueError("Không kiểm tra được cửa sổ đích. Mở ứng dụng đích ở chế độ thông thường.")
        try:
            name, size = C.create_unicode_buffer(32768), W.DWORD(32768)
            if not self.kernel.QueryFullProcessImageNameW(handle, 0, name, C.byref(size)):
                raise ValueError("Không xác định được ứng dụng đích.")
            process = PureWindowsPath(name.value).name.lower()
        finally:
            self.kernel.CloseHandle(handle)
        info = GUITHREADINFO()
        info.cbSize = C.sizeof(info)
        if not self.user.GetGUIThreadInfo(thread_id, C.byref(info)):
            raise ValueError("Không xác định được vị trí nhập văn bản.")
        return Target(hwnd, info.hwndFocus or 0, title.value, process, self.user.GetKeyboardLayout(thread_id), pid.value)

    def arm(self):
        target = self._snapshot()
        if target.pid == os.getpid():
            raise ValueError("Bạn vẫn đang ở Gõ Việt. Trong lúc đếm ngược, bấm ô nhập chữ ở ứng dụng cần gõ.")
        if not target.focus:
            raise ValueError("Chưa có vùng nhập được chọn. Hãy bấm vào chỗ cần gõ ở ứng dụng đích.")
        if self.mode == "telex" and self.user.GetKeyState(0x14) & 1:
            raise ValueError("Hãy tắt Caps Lock rồi thử lại.")
        if any(self.user.GetAsyncKeyState(vk) & 0x8000 for vk in (0x10, 0x11, 0x12, 0x5B, 0x5C)):
            raise ValueError("Hãy thả Shift/Ctrl/Alt/Windows trước khi bắt đầu.")
        # Validate layout once rather than discovering missing punctuation mid-run.
        for value in range(32, 127) if self.mode == "telex" else ():
            mapped = self.user.VkKeyScanExW(chr(value), target.layout)
            if mapped == -1 or ((mapped >> 8) & 0xFE):
                raise ValueError("Hãy chọn bàn phím Windows English (US), còn UniKey để Unicode + Telex.")
        self.target = target
        self.armed = True

    def target_is_safe(self):
        if self._signal.is_set() or self._failure or not self.thread or not self.thread.is_alive():
            return False
        try:
            return self.target is not None and self.target.same_destination(self._snapshot())
        except (OSError, ValueError):
            return False

    def _input(self, vk, up=False):
        item = INPUT()
        item.type = 1
        # Supply scan codes as physical keyboards do. Some input methods ignore
        # events with scanCode=0 even though a plain Edit control accepts them.
        scan = self.user.MapVirtualKeyExW(vk, 0, self.target.layout) if self.target else 0
        item.ki = KEYBDINPUT(vk, scan, 0x0002 if up else 0, 0, MARKER)
        return item

    def _unicode_events(self, char):
        raw = char.encode("utf-16-le")
        events = []
        for offset in range(0, len(raw), 2):
            unit = int.from_bytes(raw[offset:offset+2], "little")
            for up in (False, True):
                item = INPUT()
                item.type = 1
                item.ki = KEYBDINPUT(0, unit, 0x0004 | (0x0002 if up else 0), 0, MARKER)
                events.append(item)
        return events

    def send(self, key):
        if not self.armed or not self.target_is_safe():
            raise ValueError("Đã dừng: tiêu điểm đích thay đổi hoặc bạn vừa dùng bàn phím/chuột.")
        if self.mode == "unicode" and key not in ("\b", "\n"):
            events = self._unicode_events(key)
            batch = (INPUT * len(events))(*events)
            if self.user.SendInput(len(events), batch, C.sizeof(INPUT)) != len(events):
                raise OSError("Ứng dụng đích không nhận Unicode. Hãy thử chế độ Telex hoặc kiểm tra quyền chạy ứng dụng.")
            return
        mapped = 0x08 if key == "\b" else 0x0D if key == "\n" else self.user.VkKeyScanExW(key, self.target.layout)
        if mapped == -1 or ((mapped >> 8) & 0xFE):
            raise ValueError("Bàn phím Windows không hỗ trợ ký tự này.")
        vk, shifted = mapped & 0xFF, (mapped >> 8) & 1
        events = ([self._input(0x10)] if shifted else []) + [self._input(vk), self._input(vk, True)] + ([self._input(0x10, True)] if shifted else [])
        batch = (INPUT * len(events))(*events)
        if self.user.SendInput(len(events), batch, C.sizeof(INPUT)) != len(events):
            # Release only keys this failed batch could have pressed.
            releases = (INPUT * (2 if shifted else 1))(*([self._input(vk, True)] + ([self._input(0x10, True)] if shifted else [])))
            self.user.SendInput(len(releases), releases, C.sizeof(INPUT))
            raise OSError("Windows không nhận phím. Kiểm tra ứng dụng và trình duyệt chạy cùng quyền người dùng.")

    def start_monitor(self, stop):
        def signal(reason):
            # Never block the low-level hook; Windows can silently remove slow hooks.
            self._reason = reason
            self._signal.set()

        def keyboard_hook(code, wparam, lparam):
            if code >= 0 and wparam in (0x100, 0x104):
                event = C.cast(lparam, C.POINTER(KBDHOOK)).contents
                if not event.flags & 0x10:
                    if event.vkCode == 0x77:
                        signal("Đã dừng bằng F8. Nội dung đã gõ được giữ nguyên.")
                    elif self.armed:
                        signal("Đã dừng vì bạn vừa dùng bàn phím.")
            return self.user.CallNextHookEx(None, code, wparam, lparam)

        def mouse_hook(code, wparam, lparam):
            if code >= 0 and self.armed and wparam in (0x201, 0x204, 0x207, 0x20B, 0x20A, 0x20E):
                event = C.cast(lparam, C.POINTER(MOUSEHOOK)).contents
                if not event.flags & 1:
                    signal("Đã dừng vì bạn vừa bấm hoặc cuộn chuột.")
            return self.user.CallNextHookEx(None, code, wparam, lparam)

        self._keyboard_callback, self._mouse_callback = HOOKPROC(keyboard_hook), HOOKPROC(mouse_hook)

        def hook_loop():
            hooks = []
            try:
                self._thread_id = self.kernel.GetCurrentThreadId()
                message = W.MSG()
                self.user.PeekMessageW(C.byref(message), None, 0, 0, 0)
                module = self.kernel.GetModuleHandleW(None)
                for kind, callback in ((13, self._keyboard_callback), (14, self._mouse_callback)):
                    hook = self.user.SetWindowsHookExW(kind, callback, module, 0)
                    if not hook:
                        raise C.WinError(C.get_last_error())
                    hooks.append(hook)
                self._ready.set()
                while not self._shutdown.is_set():
                    result = self.user.GetMessageW(C.byref(message), None, 0, 0)
                    if result <= 0:
                        if result == -1:
                            self._failure = "Windows không duy trì được bộ theo dõi dừng."
                        break
                    self.user.TranslateMessage(C.byref(message))
                    self.user.DispatchMessageW(C.byref(message))
            except Exception as error:
                self._failure = str(error)
                signal("Không bật được phím dừng F8; chưa gõ nội dung.")
            finally:
                for hook in hooks:
                    self.user.UnhookWindowsHookEx(hook)
                self._ready.set()

        self.thread = threading.Thread(target=hook_loop, daemon=True)
        self.thread.start()
        if not self._ready.wait(3) or self._failure:
            self.close()
            raise OSError("Không bật được bộ dừng an toàn F8. " + (self._failure or ""))

        def watch():
            while not self._shutdown.wait(0.01):
                if self._signal.is_set():
                    stop(self._reason)
                    return
                if not self.thread.is_alive():
                    stop("Bộ theo dõi bàn phím đã dừng; hủy gõ để tránh mất kiểm soát.")
                    return
        self._watcher = threading.Thread(target=watch, daemon=True)
        self._watcher.start()

    def close(self):
        self.armed = False
        self._shutdown.set()
        if self._thread_id:
            self.user.PostThreadMessageW(self._thread_id, 0x12, 0, 0)
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=2)
