"""Vietnamese desktop interface. Worker threads communicate only via a queue."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .engine import prepare, Settings, Playback, Cancelled, Plan, Stroke, correction_keys, render_unicode, break_seconds
from .telex import TextError, normalize, Encoder, SUPPORTED
from .importers import read_file, read_google_doc, checked_text
from .keyboard import WindowsKeyboard
from . import __version__

SAMPLE = (
    "Đoàng. Tiếng Việt và TIẾNG VIỆT.\n"
    "á à ả ã ạ | ắ ằ ẳ ẵ ặ | ấ ầ ẩ ẫ ậ\n"
    "é è ẻ ẽ ẹ | ế ề ể ễ ệ | í ì ỉ ĩ ị\n"
    "ó ò ỏ õ ọ | ố ồ ổỗ ộ | ớ ờ ở ỡ ợ\n"
    "ú ù ủ ũ ụ | ứ ừ ử ữ ự | ý ỳ ỷ ỹ ỵ\n"
    "coffee, address, success, Windows; 0123456789!\n\n"
    "Tôi yêu tiếng Việt."
).replace("ổỗ", "ổ ỗ")

SETUP = """Dùng được với ô nhập chữ trong Word, Notepad, trình duyệt và ứng dụng Windows.
Không cần kiểm tra mẫu để mở nút Bắt đầu.

CHẾ ĐỘ TELEX (mô phỏng phím gõ qua UniKey)
1. UniKey: chọn Bảng mã Unicode, Kiểu gõ Telex, bật chế độ V.
2. Trong Mở rộng: bật 'Cho phép gõ tự do'; tắt kiểm tra chính tả,
   tự khôi phục phím với từ sai và gõ tắt/macro. Không dùng Simple Telex.
3. Kiểu đặt dấu trong ứng dụng phải giống UniKey:
   mặc định cũ: hòa, thủy; kiểu mới: hoà, thuỷ.
4. Bàn phím Windows: English (US). Tắt Caps Lock.
5. Nếu ứng dụng tự sửa từ/dấu, hãy tắt tính năng đó trước khi gõ.

CHẾ ĐỘ UNICODE TRỰC TIẾP (nếu Telex không hoạt động)
Gửi từng ký tự Unicode, không dùng clipboard và không cần UniKey chuyển dấu.
Giữ nguyên tiếng Việt, dấu ngoặc cong và nhiều ký tự khác.
Tự chuyển sang Unicode nếu nội dung có ký tự Telex không gõ được (ví dụ: η).

THỬ TRƯỚC KHI GÕ DÀI (không bắt buộc)
6. Nhấn 'Gõ mẫu thử', rồi bấm vào một ô nhập chữ trống khi đang đếm ngược.
   Không chọn sẵn chữ. Thả các phím Ctrl/Alt/Shift.
7. Nếu muốn đối chiếu, sao chép mẫu vừa gõ từ ứng dụng đích vào ô đối chiếu.

F8 dừng ngay cả khi cửa sổ ứng dụng đang ở phía sau.
Bấm chuột, cuộn chuột, dùng bàn phím hoặc đổi cửa sổ sẽ dừng gõ.
Chỉ gõ vào ô văn bản. Phím Enter có thể gửi tin nhắn trong một số ứng dụng.
Ứng dụng đích cần có cùng quyền chạy với Gõ Việt; không hỗ trợ màn hình bảo mật.
Ứng dụng không thay đổi cài đặt UniKey và không tạo lịch sử giả.
"""

def duration(seconds):
    seconds = max(0, int(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours} giờ {minutes:02d} phút" if hours else f"{minutes} phút {seconds:02d} giây"

class App:
    def __init__(self, root):
        self.root = root
        root.title(f"Gõ Việt {__version__} — Gõ vào mọi ứng dụng")
        root.geometry(f"{min(1060, root.winfo_screenwidth()-60)}x{min(700, root.winfo_screenheight()-100)}")
        root.minsize(760, 520)
        root.configure(bg="#edf2f7")
        self.messages = queue.Queue()
        self.busy = False
        self.playback = None
        self.preparing_cancel = threading.Event()
        self.verified_profile = None
        self.completed_test = None
        self.test_run = False
        self.has_started = False
        self.closing = False
        self.speed = tk.DoubleVar(value=1.0)
        self.corrections = tk.BooleanVar(value=False)
        self.rate = tk.DoubleVar(value=2.0)
        self.modern = tk.BooleanVar(value=False)
        self.mode = tk.StringVar(value="Telex qua UniKey")
        self.countdown = tk.StringVar(value="5")
        self.source_name = tk.StringVar(value="Nội dung của bạn · Chưa nhập tệp")
        self.status = tk.StringVar(value="Nhập nội dung → Bắt đầu → bấm ô cần gõ trong ứng dụng đích.")
        self.meta = tk.StringVar(value="0 ký tự")
        self.eta = tk.StringVar(value="Thời gian: —")
        self.profile = tk.StringVar(value="Thử mẫu là tùy chọn; không khóa Bắt đầu.")
        self._widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(40, self.poll)

    def _widgets(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#edf2f7")
        style.configure("Card.TFrame", background="white")
        style.configure("TLabel", background="#edf2f7", foreground="#172c45", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="white")
        style.configure("Muted.TLabel", foreground="#53667d", background="white", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 10), padding=(13, 9), background="#e8eef6", borderwidth=0)
        style.map("TButton", background=[("active", "#dce7f6"), ("disabled", "#eef0f4")])
        style.configure("Accent.TButton", background="#1963d3", foreground="white", font=("Segoe UI Semibold", 11))
        style.map("Accent.TButton", background=[("disabled", "#bdcde3"), ("active", "#124fb0")], foreground=[("disabled", "white")])
        style.configure("Stop.TButton", background="#fff0ef", foreground="#a72a24")
        style.configure("TCheckbutton", background="white", font=("Segoe UI", 10), foreground="#172c45")
        style.configure("Horizontal.TScale", background="white", troughcolor="#e6edf5")
        style.configure("Horizontal.TProgressbar", background="#1963d3", troughcolor="#e1e8f1", borderwidth=0)

        header = tk.Frame(self.root, bg="#122b48", padx=26, pady=18)
        header.pack(fill="x")
        tk.Label(header, text="Gõ Việt", font=("Segoe UI Semibold", 25), fg="white", bg="#122b48").pack(side="left")
        tk.Label(header, text="TELEX  /  UNICODE", font=("Segoe UI", 10), fg="#adcaee", bg="#122b48").pack(side="left", padx=22)
        tk.Label(header, text="F8  ·  DỪNG", font=("Segoe UI Semibold", 10), fg="white", bg="#254361", padx=14, pady=7).pack(side="right")

        body = ttk.Frame(self.root, padding=(20, 18))
        # Pack the body last so its requested size cannot push Start/Stop offscreen.
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        main = ttk.Frame(body, style="Card.TFrame", padding=20)
        main.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)
        ttk.Label(main, text="01  Chuẩn bị nội dung", style="Card.TLabel", font=("Segoe UI Semibold", 13)).grid(row=0, column=0, sticky="w")
        toolbar = ttk.Frame(main, style="Card.TFrame")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(12, 5))
        self.file_button = ttk.Button(toolbar, text="Mở .txt / .docx", command=self.open_file)
        self.file_button.pack(side="left")
        self.link_button = ttk.Button(toolbar, text="Nhập link Google Docs", command=self.open_link)
        self.link_button.pack(side="left", padx=(8, 0))
        ttk.Label(main, textvariable=self.source_name, style="Muted.TLabel", wraplength=530).grid(row=2, column=0, sticky="w", pady=(5, 10))
        editor = ttk.Frame(main, style="Card.TFrame")
        editor.grid(row=3, column=0, sticky="nsew")
        self.text = tk.Text(editor, wrap="word", undo=True, width=35, height=5, font=("Segoe UI", 12), bg="#fbfcfe", fg="#1e334c", relief="solid", bd=1, padx=14, pady=12, insertbackground="#1963d3", highlightthickness=0)
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(editor, command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.tag_configure("problem", background="#ffe0d9", foreground="#971c17")
        self.text.bind("<<Modified>>", self.text_changed)
        ttk.Label(main, textvariable=self.meta, style="Muted.TLabel").grid(row=4, column=0, sticky="w", pady=(9, 0))
        ttk.Label(main, text="Dán hoặc sửa văn bản tại đây. Chỉ gõ chữ và xuống dòng; không giữ định dạng.", style="Muted.TLabel", wraplength=540).grid(row=5, column=0, sticky="w", pady=(6, 0))

        notebook = ttk.Notebook(body, width=278)
        notebook.grid(row=0, column=1, sticky="ns")
        side = ttk.Frame(notebook, style="Card.TFrame", padding=14)
        support = ttk.Frame(notebook, style="Card.TFrame", padding=14)
        notebook.add(side, text="Cách gõ")
        notebook.add(support, text="Thử / hỗ trợ")
        ttk.Label(side, text="Chế độ nhập", style="Card.TLabel").pack(anchor="w")
        self.mode_combo = ttk.Combobox(side, textvariable=self.mode, values=("Telex qua UniKey", "Unicode trực tiếp"), state="readonly", width=23)
        self.mode_combo.pack(fill="x", pady=(4, 10))
        self.mode_combo.bind("<<ComboboxSelected>>", self.invalidate_test)
        ttk.Label(side, text="02  Nhịp gõ", style="Card.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        self.speed_label = ttk.Label(side, text="Tốc độ: 1,00×", style="Card.TLabel")
        self.speed_label.pack(anchor="w", pady=(10, 4))
        self.speed_scale = ttk.Scale(side, from_=0.25, to=4, variable=self.speed, command=self.settings_changed, length=245)
        self.speed_scale.pack(fill="x")
        ttk.Label(side, text="Chậm                       Nhanh", style="Muted.TLabel").pack(fill="x", pady=(2, 8))
        self.correction_check = ttk.Checkbutton(side, text="Thỉnh thoảng gõ sai rồi sửa", variable=self.corrections, command=self.settings_changed)
        self.correction_check.pack(anchor="w")
        self.rate_label = ttk.Label(side, text="Tần suất: 2% số từ đủ điều kiện", style="Muted.TLabel")
        self.rate_label.pack(anchor="w", pady=(10, 4))
        self.rate_scale = ttk.Scale(side, from_=1, to=10, variable=self.rate, command=self.settings_changed)
        self.rate_scale.pack(fill="x")
        ttk.Label(side, text="Nghỉ thêm ở dấu câu và đoạn mới.", style="Muted.TLabel", wraplength=245).pack(anchor="w", pady=(8, 10))
        delay_row = ttk.Frame(side, style="Card.TFrame")
        delay_row.pack(fill="x")
        ttk.Label(delay_row, text="Đếm ngược (giây)", style="Card.TLabel").pack(side="left")
        self.countdown_combo = ttk.Combobox(delay_row, textvariable=self.countdown, values=("5", "10", "15"), state="readonly", width=4)
        self.countdown_combo.pack(side="right")
        ttk.Label(side, text="Bấm ô cần gõ trong lúc đếm ngược. Nếu Telex lỗi, thử Unicode trực tiếp.", style="Muted.TLabel", wraplength=240).pack(anchor="w", pady=(10, 0))
        ttk.Label(support, text="Thử trước khi gõ dài", style="Card.TLabel", font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(0, 12))
        self.modern_check = ttk.Checkbutton(support, text="Kiểu dấu mới: hoà, thuỷ", variable=self.modern, command=self.invalidate_test)
        self.modern_check.pack(anchor="w")
        self.check_button = ttk.Button(support, text="Hướng dẫn & gõ mẫu thử", command=self.setup_dialog)
        self.check_button.pack(fill="x", pady=(12, 8))
        ttk.Label(support, textvariable=self.profile, style="Muted.TLabel", wraplength=245).pack(anchor="w")
        ttk.Label(support, text="Gõ được vào Word, Notepad, ô văn bản trên web… Không giới hạn Google Docs.", style="Muted.TLabel", wraplength=245).pack(anchor="w", pady=(12, 0))
        self.verify_button = ttk.Button(support, text="Đối chiếu mẫu đã gõ", command=self.verify_dialog, state="disabled")
        self.verify_button.pack(fill="x", pady=(12, 0))

        bottom = ttk.Frame(self.root, padding=(24, 0, 24, 18))
        self.progress = ttk.Progressbar(bottom, maximum=100)
        self.progress.pack(fill="x", pady=(0, 12))
        line = ttk.Frame(bottom)
        line.pack(fill="x")
        labels = ttk.Frame(line)
        labels.pack(side="left", fill="x", expand=True)
        self.status_label = ttk.Label(labels, textvariable=self.status, wraplength=480, font=("Segoe UI Semibold", 10))
        self.status_label.pack(anchor="w")
        ttk.Label(labels, textvariable=self.eta, font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))
        self.stop_button = ttk.Button(line, text="Dừng · F8", style="Stop.TButton", command=self.stop, state="disabled")
        self.stop_button.pack(side="right", padx=(8, 0))
        self.start_button = ttk.Button(line, text="Bắt đầu", style="Accent.TButton", command=self.start, state="disabled")
        self.start_button.pack(side="right")
        tk.Label(self.root, text="Gõ từng phím/ký tự • F8 dừng • Không tự gửi tin nhắn hoặc lưu tài liệu", font=("Segoe UI", 9), fg="#586c83", bg="#e2eaf3", pady=6).pack(side="bottom", fill="x")
        bottom.pack(side="bottom", fill="x")
        body.pack(fill="both", expand=True)
        line.bind("<Configure>", lambda e: self.status_label.configure(wraplength=max(220, e.width-310)))
        self.settings_changed()

    def settings(self):
        return Settings(round(self.speed.get(), 2), round(self.rate.get()) / 100 if self.corrections.get() else 0, self.modern.get(), "unicode" if self.mode.get() == "Unicode trực tiếp" else "telex")

    def settings_changed(self, *_):
        self.speed_label.config(text=f"Tốc độ: {self.speed.get():.2f}×")
        self.rate_label.config(text=f"Tần suất: {round(self.rate.get())}% số từ đủ điều kiện")
        self.rate_scale.state(["!disabled"] if self.corrections.get() and not self.busy else ["disabled"])
        self.estimate()

    def estimate(self):
        if not self.busy:
            size = len(self.text.get("1.0", "end-1c"))
            self.meta.set(f"{size:,} / 100.000 ký tự")
            self.eta.set("Ước tính: " + duration(size * 0.23 / self.speed.get() + break_seconds(size)) + " · tính chính xác khi bắt đầu" if size else "Thời gian: —")
            self.start_button.state(["!disabled"] if self.text.get("1.0", "end-1c").strip() else ["disabled"])

    def text_changed(self, *_):
        if self.text.edit_modified():
            self.text.tag_remove("problem", "1.0", "end")
            self.text.edit_modified(False)
            self.estimate()

    def set_busy(self, value):
        self.busy = value
        for widget in (self.file_button, self.link_button, self.check_button, self.speed_scale, self.correction_check, self.modern_check, self.mode_combo, self.countdown_combo):
            widget.state(["disabled"] if value else ["!disabled"])
        self.text.config(state="disabled" if value else "normal")
        self.start_button.state(["!disabled"] if not value and self.text.get("1.0", "end-1c").strip() else ["disabled"])
        self.stop_button.state(["!disabled"] if value else ["disabled"])
        self.verify_button.state(["!disabled"] if not value and self.completed_test else ["disabled"])
        self.settings_changed()

    def invalidate_test(self, *_):
        self.verified_profile = self.completed_test = None
        self.profile.set("Có thể thử lại sau khi đổi cấu hình. Bắt đầu không bị khóa.")
        self.set_busy(False)

    def load(self, action, label):
        if self.busy:
            return
        self.set_busy(True)
        self.status.set("Đang đọc văn bản…")
        # Network imports cannot type. Stop simply discards their eventual result.
        self.preparing_cancel = threading.Event()
        cancel = self.preparing_cancel
        def worker():
            try:
                result = action()
                self.messages.put(("loaded", (result, label, cancel)))
            except Exception as error:
                self.messages.put(("load_error", (str(error), cancel)))
        threading.Thread(target=worker, daemon=True).start()

    def open_file(self):
        path = filedialog.askopenfilename(title="Chọn văn bản", filetypes=[("Văn bản và Word", "*.txt *.docx"), ("Văn bản UTF-8", "*.txt"), ("Word", "*.docx")])
        if path:
            from pathlib import Path
            self.load(lambda: read_file(path), Path(path).name)

    def open_link(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Nhập Google Docs công khai")
        dialog.geometry("650x205")
        dialog.transient(self.root)
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Liên kết phải đọc và tải được khi chưa đăng nhập.").pack(anchor="w")
        entry = ttk.Entry(frame)
        entry.pack(fill="x", pady=12)
        entry.focus_set()
        ttk.Label(frame, text="Tài liệu riêng tư: tải .docx hoặc .txt, sau đó dùng nút Mở tệp.", wraplength=590).pack(anchor="w")
        def submit():
            url = entry.get().strip()
            dialog.destroy()
            self.load(lambda: read_google_doc(url), "Google Docs · Bản nhập văn bản")
        ttk.Button(frame, text="Nhập văn bản", command=submit).pack(anchor="e", pady=12)

    def setup_dialog(self):
        if self.busy:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Kiểm tra tương thích UniKey")
        dialog.geometry(f"730x{min(650, self.root.winfo_screenheight()-100)}")
        dialog.transient(self.root)
        frame = ttk.Frame(dialog, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Chuẩn bị một ô nhập chữ trống để thử", font=("Segoe UI Semibold", 15)).pack(anchor="w", pady=(0, 12))
        def run():
            dialog.destroy()
            self.start(test=True)
        ttk.Button(frame, text=f"Gõ mẫu thử · đếm ngược {self.countdown.get()} giây", style="Accent.TButton", command=run).pack(side="bottom", anchor="e", pady=(10, 0))
        guidance_box = ttk.Frame(frame)
        guidance_box.pack(fill="both", expand=True)
        guidance = tk.Text(guidance_box, wrap="word", font=("Segoe UI", 11), height=8, relief="flat", padx=12, pady=12)
        guidance.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(guidance_box, command=guidance.yview)
        scroll.pack(side="right", fill="y")
        guidance.config(yscrollcommand=scroll.set)
        guidance.insert("1.0", SETUP)
        guidance.config(state="disabled")

    def start(self, test=False):
        if self.busy:
            return
        text = "Đoàng. Tiếng Việt: coffee, Windows.\n" + ("hoà thuỷ" if self.modern.get() else "hòa thủy") if test else normalize(self.text.get("1.0", "end-1c"))
        if not test:
            self.text.delete("1.0", "end")
            self.text.insert("1.0", text)
        self.select_input_mode(text)
        self.test_run = test
        self.has_started = True
        self.start_button.config(text="Bắt đầu từ đầu")
        self.progress["value"] = 0
        self.preparing_cancel = threading.Event()
        self.set_busy(True)
        self.status.set("Đang chuẩn bị nội dung trước khi gõ…")
        settings = self.settings()
        countdown = int(self.countdown.get())
        if test:
            self.verified_profile = self.completed_test = None
            self.profile.set("Đang kiểm tra…")
        def worker():
            try:
                plan = prepare(text, Settings(settings.speed, 0 if test else settings.correction_rate, settings.modern, settings.mode), cancel=self.preparing_cancel)
                if test:
                    # Force one independently verified correction in the trial.
                    encoder = Encoder(settings.modern) if settings.mode == "telex" else None
                    script = correction_keys(encoder, "Việt", encoder.word("Việt")) if encoder else "diệt " + "\b" * 5 + "Việt"
                    extra = tuple(Stroke(k, 0.18 / settings.speed, len(plan.text)) for k in " " + script)
                    plan = Plan(plan.text + " Việt", plan.strokes + extra, plan.estimated_seconds + sum(s.delay for s in extra), 1)
                    output = "".join(s.key for s in plan.strokes)
                    if (encoder.oracle.render(output) if encoder else render_unicode(output)) != plan.text:
                        raise ValueError("Mẫu đối chiếu nội bộ không khớp.")
                if self.preparing_cancel.is_set():
                    raise Cancelled()
                keyboard = WindowsKeyboard(mode=settings.mode)
                playback = Playback(keyboard, lambda event, data: self.messages.put((event, data)))
                self.playback = playback
                if self.preparing_cancel.is_set():
                    playback.stop()
                self.messages.put(("ready", plan))
                playback.run(plan, countdown=countdown)
                if test and not playback.cancelled.is_set() and keyboard.target:
                    # The main thread only exposes verification after a completed run.
                    self.messages.put(("test_profile", (plan.text, (keyboard.target.process, keyboard.target.layout, settings.modern))))
            except TextError as error:
                self.messages.put(("invalid", error))
                self.messages.put(("finished", "error"))
            except Cancelled:
                self.messages.put(("stopped", "Đã hủy trước khi gõ."))
                self.messages.put(("finished", "stopped"))
            except Exception as error:
                self.messages.put(("error", str(error)))
                self.messages.put(("finished", "error"))
        self.last_outcome = None
        threading.Thread(target=worker, daemon=True).start()

    def select_input_mode(self, text):
        # Switch the entire run, including the keyboard backend, before planning.
        # Never remove or transliterate characters that Telex cannot represent.
        if self.settings().mode == "telex" and any(ch not in SUPPORTED and ch.isprintable() for ch in text):
            self.mode.set("Unicode trực tiếp")
            self.invalidate_test()
            self.profile.set("Đã tự chuyển sang Unicode trực tiếp để giữ nguyên ký tự ngoài Telex.")

    def verify_dialog(self):
        if not self.completed_test or self.busy:
            return
        expected, profile = self.completed_test
        dialog = tk.Toplevel(self.root)
        dialog.title("Đối chiếu mẫu đã gõ (tùy chọn)")
        dialog.geometry("800x655")
        dialog.transient(self.root)
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Sao chép phần mẫu vừa gõ từ ứng dụng đích và dán vào ô dưới.", wraplength=750, font=("Segoe UI Semibold", 11)).pack(anchor="w", pady=(0, 10))
        pasted = tk.Text(frame, wrap="word", font=("Segoe UI", 11), height=11, padx=10, pady=10)
        pasted.pack(fill="both", expand=True)
        result = ttk.Label(frame, text="Kiểm tra này đối chiếu chữ thực tế, không chỉ kiểm tra cài đặt.", wraplength=730)
        result.pack(anchor="w", pady=10)
        ttk.Label(frame, text="Văn bản cần khớp:").pack(anchor="w")
        reference = tk.Text(frame, wrap="word", height=9, font=("Segoe UI", 10), bg="#e5edf7", padx=10, pady=8)
        reference.insert("1.0", expected)
        reference.config(state="disabled")
        reference.pack(fill="x", pady=(4, 10))
        def verify():
            actual = normalize(pasted.get("1.0", "end-1c")).rstrip("\n")
            if actual == expected:
                self.verified_profile = profile
                self.profile.set("Đã khớp mẫu · " + profile[0].replace(".exe", ""))
                self.status.set("Sẵn sàng. Chọn vị trí trống trong tài liệu khi đếm ngược.")
                self.set_busy(False)
                dialog.destroy()
            else:
                self.verified_profile = None
                diff = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b), min(len(actual), len(expected)))
                result.config(text=f"Chưa khớp tại ký tự {diff + 1}. Cần: {expected[diff:diff+18]!r}; nhận: {actual[diff:diff+18]!r}. Kiểm tra UniKey hoặc thử Unicode trực tiếp.", foreground="#b32b21")
        ttk.Button(frame, text="Đối chiếu kết quả", style="Accent.TButton", command=verify).pack(anchor="e")

    def stop(self):
        self.preparing_cancel.set()
        if self.playback:
            self.playback.stop()
        self.status.set("Đang dừng… Ứng dụng đích có thể vẫn đang xử lý ký tự vừa gửi.")

    def poll(self):
        try:
            while True:
                event, data = self.messages.get_nowait()
                if event == "loaded":
                    text, label, cancel = data
                    if not cancel.is_set():
                        self.text.config(state="normal")
                        self.text.delete("1.0", "end")
                        self.text.insert("1.0", text)
                        self.source_name.set(label)
                        self.status.set("Đã nhập văn bản. Bạn có thể chỉnh sửa trước khi gõ.")
                    else:
                        self.status.set("Đã hủy nhập văn bản.")
                    self.set_busy(False)
                elif event == "load_error":
                    error, cancel = data
                    self.status.set("Đã hủy nhập văn bản." if cancel.is_set() else error)
                    self.set_busy(False)
                elif event == "ready":
                    self.eta.set(f"Dự kiến: {duration(data.estimated_seconds)} · {data.corrections} lần sửa")
                elif event == "countdown":
                    self.status.set(f"{data}… {self.mode.get()} · Bấm vào ô cần gõ trong ứng dụng đích.")
                elif event == "progress":
                    count, total, remaining = data
                    self.progress["value"] = 100 * count / total
                    self.status.set(f"Đang gõ · {count:,} / {total:,} ký tự · F8 để dừng")
                    self.eta.set("Còn khoảng " + duration(remaining))
                elif event == "rest":
                    count, total, seconds, remaining = data
                    self.status.set(f"Đang nghỉ · {seconds} giây nữa gõ tiếp · {count:,} / {total:,} ký tự · F8 để dừng")
                    self.eta.set("Còn khoảng " + duration(remaining))
                elif event in ("complete", "stopped", "error"):
                    self.status.set(data)
                    if event == "complete":
                        self.progress["value"] = 100
                elif event == "invalid":
                    self.status.set(str(data))
                    if not self.test_run:
                        for issue in data.issues:
                            self.text.tag_add("problem", f"1.0+{issue.start}c", f"1.0+{issue.end}c")
                        self.text.see(f"1.0+{data.issues[0].start}c")
                elif event == "finished":
                    self.last_outcome = data
                    self.playback = None
                    self.set_busy(False)
                    if data == "complete":
                        self.eta.set("Hoàn tất · kiểm tra nội dung trong ứng dụng đích")
                elif event == "test_profile" and self.last_outcome == "complete":
                    self.completed_test = data
                    self.set_busy(False)
                    self.status.set("Mẫu đã gõ xong. Nhấn 'Đối chiếu mẫu đã gõ' để kiểm tra.")
        except queue.Empty:
            pass
        if self.closing and not self.busy:
            self.root.destroy()
            return
        self.root.after(40, self.poll)

    def close(self):
        if self.busy:
            self.closing = True
            self.stop()
            self.root.withdraw()
        else:
            self.root.destroy()

def main():
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    try:
        App(root)
        root.mainloop()
    except Exception as error:
        messagebox.showerror("Gõ Việt", "Không mở được ứng dụng: " + str(error))
        root.destroy()
