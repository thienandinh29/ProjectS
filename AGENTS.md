# Repository Guidelines

## Project Structure & Module Organization

`main.py` starts the Windows Tkinter application. Application code lives in `telex_app/`: `ui.py` handles the interface, `engine.py` playback, `keyboard.py` Windows input, `telex.py` and `oracle.py` conversion and verification, and `importers.py` file and Google Docs imports. `native/oracle.cpp` bridges the vendored UniKey core in `vendor/fcitx-unikey/`. Tests are in `tests/`; build and UI smoke scripts are in `scripts/`. License notices live in `licenses/`.

## Build, Test, and Development Commands

Use Windows 10/11 x64, Python 3.11 x64, and Visual Studio 2022 C++ desktop build tools. From the repository root:

- `python -m venv .venv` creates a virtual environment; install dependencies with `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- `.\.venv\Scripts\python.exe scripts/build_native.py` builds the UniKey oracle DLL; run this before exercising conversion.
- `.\.venv\Scripts\python.exe main.py` starts the app.
- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` runs the automated suite.
- `.\.venv\Scripts\python.exe scripts/smoke_ui.py` checks the interface without sending keyboard input.
- `.\.venv\Scripts\python.exe scripts/build_release.py` builds the native component, runs checks, and packages the executable, source, and notices.

## Coding Style & Testing

Follow the existing Python style: four-space indentation, `snake_case` functions and modules, and `PascalCase` classes. Keep Tkinter work on the UI thread and use the existing queue for worker updates. Preserve upstream files in `vendor/`; adapt the build or bridge when necessary. Add `unittest` cases in `tests/test_*.py` with `test_*` methods, covering behavior and failure paths. No coverage threshold or repository formatter is specified. See `TEST_RESULTS.md` for limitations of offline verification; use a blank scratch document for live compatibility checks.

## Commits, Pull Requests & Distribution

History contains only `first commit`, so no established commit convention can be inferred. Write concise, descriptive commit subjects. In pull requests, describe the behavior changed, list checks run, link relevant issues, and include screenshots for interface changes. The project is GPL-3.0-or-later: retain third-party notices and distribute matching source with executable releases.
After completing each task, automatically commit the task changes and push them to the current branch.
