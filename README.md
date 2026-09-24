# Gõ Việt

Windows desktop app that sends Telex keystrokes to Google Docs. UniKey performs
the actual Vietnamese composition. Text stays in memory; anonymous Google Docs
imports are the only network operation. No account access, clipboard writes,
telemetry, content logs, or fabricated history.

## Run

Open `dist/GoViet.exe`, then follow [the Vietnamese guide](HUONG_DAN.md).
No Python installation is needed for the executable. Windows 10/11 x64,
UniKey Unicode + Telex, and Chrome or Edge are required.

Use a blank scratch Google Doc for the first compatibility test. Copy its output
back to the app to unlock typing. This is required every app session and after
changing the tone-placement setting; browser/keyboard-profile changes also
require a new test. Do not change UniKey settings after the check.

The test is a real-output comparison, not a guarantee about Google version
history. Live Google Docs testing was unavailable in the implementation session;
see [test results](TEST_RESULTS.md) for what has actually been verified.

## Develop and build

Use Python 3.11 x64 and Visual Studio 2022 with the C++ desktop build tools.
The complete vendored UniKey source is included, so cloning is not needed.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/build_native.py
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/smoke_ui.py
.\.venv\Scripts\python.exe scripts/build_release.py
```

The build script uses PyInstaller to produce a portable one-file executable plus
its matching source archive and notices. It does not install UniKey or alter
system settings. Run the build under a normal Windows user account; a restricted
sandbox may prevent Tcl/Tk from loading its scripts.

## Architecture and boundaries

- `importers`: bounded UTF-8/UTF-16 and Word imports; anonymous HTTPS Docs export.
- `telex` / `oracle`: normalize NFC, generate key sequences, verify them with the
  separately compiled upstream UniKey engine, then reject unsupported input.
- `engine`: verified word corrections, randomized timing, cancellable playback.
- `keyboard`: complete key-down/up batches via SendInput; temporary low-level
  hooks stop on physical input. Browser title, focused child window, process,
  and keyboard layout are checked before every stroke and during waits.
- `ui`: Tkinter interface; workers only report state through a queue.

Supported input: Vietnamese letters, ASCII letters/numbers/punctuation,
paragraphs. Tabs become four spaces. Curly quotes, emoji and other unsupported
characters are highlighted rather than silently changed. Files are limited to
10 MB and source text to 100,000 characters; `.doc` is not supported. DOCX tables
become rows of plain text; images, headers/footers and formatting are omitted.

Compatibility is tied to UniKey behavior and Google Docs settings. The offline
oracle is based on the shared open-source core; it is not the installed Windows
UniKey binary. Target-window checks cannot inspect Docs' internal selection or
guarantee that its server has saved. Place the cursor in a blank position, turn
off Docs automatic substitutions, and inspect the completed document.

Stopping cancels future strokes and preserves text already sent, including a
partially typed word/correction. It does not roll back or resume. The next Start
begins at the start of the source. A stroke already dispatched may still finish
inside the browser after Stop.

## License

GPL-3.0-or-later. See `LICENSE.txt` and `THIRD_PARTY.md`. If distributing the
executable, also distribute the matching source and license notices provided
in `GoViet-Windows.zip`.
