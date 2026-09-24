import ctypes
import unittest
import os
from unittest.mock import Mock
from telex_app.keyboard import INPUT, KEYBDINPUT, WindowsKeyboard, Target

class NativeBindingTests(unittest.TestCase):
    def test_win64_structure_sizes_and_marker(self):
        self.assertEqual(ctypes.sizeof(INPUT), 40)
        self.assertEqual(ctypes.sizeof(KEYBDINPUT), 24)
        backend = WindowsKeyboard()
        event = backend._input(65, True)
        self.assertEqual(event.ki.dwFlags, 2)
        self.assertEqual(event.ki.dwExtraInfo, 0x47565431)

    def test_send_rejects_unarmed_backend(self):
        backend = WindowsKeyboard()
        with self.assertRaises(ValueError):
            backend.send("a")

    def test_no_input_without_live_monitor(self):
        backend = WindowsKeyboard()
        backend.target = Target(1, 2, "Test - Google Docs", "chrome.exe", 1033)
        self.assertFalse(backend.target_is_safe())

    def test_title_change_does_not_change_destination(self):
        original = Target(1, 2, "Untitled - Notepad", "notepad.exe", 1033, 20)
        edited = Target(1, 2, "*New text - Notepad", "notepad.exe", 1033, 20)
        self.assertTrue(original.same_destination(edited))
        for changed in (Target(3, 2, "Untitled", "notepad.exe", 1033, 20),
                        Target(1, 4, "Untitled", "notepad.exe", 1033, 20),
                        Target(1, 2, "Untitled", "notepad.exe", 1066, 20),
                        Target(1, 2, "Untitled", "notepad.exe", 1033, 21)):
            self.assertFalse(original.same_destination(changed))

    def test_arm_accepts_non_browser_applications(self):
        for process in ("notepad.exe", "winword.exe", "chrome.exe", "firefox.exe", "Code.exe"):
            backend = WindowsKeyboard()
            backend._snapshot = lambda p=process: Target(1, 2, "Any title", p, 1033, os.getpid()+1)
            backend.user = Mock()
            backend.user.GetKeyState.return_value = 0
            backend.user.GetAsyncKeyState.return_value = 0
            backend.user.VkKeyScanExW.return_value = 65
            backend.arm()
            self.assertTrue(backend.armed)

    def test_arm_rejects_own_app_and_missing_focus(self):
        for target in (Target(1, 2, "GoViet", "GoViet.exe", 1033, os.getpid()),
                       Target(1, 0, "Other app", "notepad.exe", 1033, os.getpid()+1)):
            backend = WindowsKeyboard()
            backend._snapshot = lambda t=target: t
            with self.assertRaises(ValueError):
                backend.arm()

    def test_unicode_events_and_surrogate_pairs(self):
        backend = WindowsKeyboard(mode="unicode")
        events = backend._unicode_events("Đ")
        self.assertEqual([(i.ki.wVk, i.ki.wScan, i.ki.dwFlags) for i in events], [(0, 0x110, 4), (0, 0x110, 6)])
        events = backend._unicode_events("🙂")
        self.assertEqual([i.ki.wScan for i in events], [0xD83D, 0xD83D, 0xDE42, 0xDE42])

    def test_telex_events_include_scan_codes(self):
        backend = WindowsKeyboard()
        backend.target = Target(1, 2, "Test", "notepad.exe", 1033)
        backend.user = Mock()
        backend.user.MapVirtualKeyExW.return_value = 0x1E
        self.assertEqual(backend._input(65).ki.wScan, 0x1E)

if __name__ == "__main__":
    unittest.main()
