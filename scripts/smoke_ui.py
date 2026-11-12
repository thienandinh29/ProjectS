"""Construct and exercise the UI without sending keyboard input."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tkinter as tk
from telex_app.ui import App

root = tk.Tk()
root.withdraw()
app = App(root)
root.update_idletasks()
assert app.start_button.instate(["disabled"])
app.text.insert("1.0", "Tiếng Việt")
root.update()
assert "10" in app.meta.get()
assert app.verified_profile is None
app.set_busy(False)
assert app.start_button.instate(["!disabled"])
app.set_busy(True)
assert app.stop_button.instate(["!disabled"])
assert str(app.text.cget("state")) == "disabled"
app.set_busy(False)
app.invalidate_test()
assert app.start_button.instate(["!disabled"])
app.mode.set("Unicode trực tiếp")
assert app.settings().mode == "unicode"
assert app.countdown.get() == "5"
app.mode.set("Telex qua UniKey")
app.select_input_mode("Tiếng Việt")
assert app.settings().mode == "telex"
app.completed_test = ("old sample", ("notepad.exe", 0, False))
app.verified_profile = app.completed_test[1]
app.select_input_mode("Hiệu suất η = 0.85")
assert app.settings().mode == "unicode"
assert app.completed_test is None and app.verified_profile is None
assert "Unicode" in app.profile.get()
app.mode.set("Telex qua UniKey")
app.select_input_mode("abc\x08d")
assert app.settings().mode == "telex"
app.text.delete("1.0", "end")
root.update()
assert app.start_button.instate(["disabled"])
root.destroy()
print("UI smoke: passed; no keyboard input sent")
