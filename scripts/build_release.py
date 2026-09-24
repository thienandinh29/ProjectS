"""Reproducible local release: executable, matching source and license notices."""
from pathlib import Path
import importlib.metadata
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from telex_app import __version__
APP_NAME = "GoViet-" + __version__

def main():
    subprocess.run([sys.executable, str(ROOT / "scripts/build_native.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/smoke_ui.py")], cwd=ROOT, check=True)
    licenses = ROOT / "licenses"
    licenses.mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "vendor/fcitx-unikey/COPYING", ROOT / "LICENSE.txt")
    python_home = Path(sys.base_prefix)
    shutil.copyfile(python_home / "LICENSE.txt", licenses / "Python.txt")
    for name in ("tcl8.6", "tk8.6"):
        notice = python_home / "tcl" / name / "license.terms"
        # The standard Python Windows LICENSE also contains the Tcl/Tk terms.
        if notice.exists():
            shutil.copyfile(notice, licenses / (name + ".txt"))
    for package in ("python-docx", "lxml", "typing_extensions", "pyinstaller"):
        dist = importlib.metadata.distribution(package)
        for file in dist.files or []:
            if file.name.lower().startswith(("license", "copying", "notice")):
                source = Path(dist.locate_file(file))
                if source.is_file():
                    shutil.copyfile(source, licenses / (package + "-" + file.name))
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", APP_NAME, "--add-binary", str(ROOT / "telex_app/unikey_oracle.dll") + ";telex_app",
        "--add-data", str(ROOT / "LICENSE.txt") + ";.",
        "--add-data", str(licenses) + ";licenses", str(ROOT / "main.py"),
    ], cwd=ROOT, check=True)
    archive_release()

def archive_release():
    release = ROOT / "dist"
    for name in ("HUONG_DAN.md", "README.md", "LICENSE.txt", "THIRD_PARTY.md", "TEST_RESULTS.md"):
        shutil.copyfile(ROOT / name, release / name)
    source_zip = release / (APP_NAME + "-source.zip")
    with zipfile.ZipFile(source_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("main.py", "requirements.txt", ".gitignore", "README.md", "HUONG_DAN.md", "LICENSE.txt", "THIRD_PARTY.md", "TEST_RESULTS.md"):
            archive.write(ROOT / name, "GoViet/" + name)
        for folder in ("telex_app", "scripts", "tests", "native", "licenses"):
            for path in (ROOT / folder).rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix not in (".pyc", ".dll"):
                    archive.write(path, "GoViet/" + path.relative_to(ROOT).as_posix())
        for path in (ROOT / "vendor/fcitx-unikey").rglob("*"):
            if path.is_file() and ".git" not in path.parts:
                archive.write(path, "GoViet/" + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(release / (APP_NAME + "-Windows.zip"), "w", zipfile.ZIP_DEFLATED) as archive:
        for name in (APP_NAME + ".exe", source_zip.name, "HUONG_DAN.md", "LICENSE.txt", "THIRD_PARTY.md", "TEST_RESULTS.md"):
            archive.write(release / name, name)
    print("Release ready:", release / (APP_NAME + "-Windows.zip"))

if __name__ == "__main__":
    if "--archives-only" in sys.argv:
        archive_release()
    else:
        main()
