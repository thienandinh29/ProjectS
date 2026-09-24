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
app.text.delete("1.0", "end")
root.update()
assert app.start_button.instate(["disabled"])
root.destroy()
print("UI smoke: passed; no keyboard input sent")
