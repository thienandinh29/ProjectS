"""Build the vendored UniKey core with the MSVC static runtime."""
from pathlib import Path
import os
import subprocess
import shutil

ROOT = Path(__file__).resolve().parents[1]

def main():
    vswhere = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    install = subprocess.check_output([str(vswhere), "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"], text=True).strip()
    if not install:
        raise RuntimeError("Install Visual Studio C++ build tools first.")
    vcvars = Path(install) / "VC/Auxiliary/Build/vcvars64.bat"
    result = subprocess.check_output(f'call "{vcvars}" >nul && set', shell=True, text=True)
    env = {k.upper(): v for k, v in os.environ.items()}
    captured = {}
    for line in result.splitlines():
        if "=" in line and not line.startswith("="):
            k, v = line.split("=", 1)
            captured.setdefault(k.upper(), v)
    env.update(captured)
    build = ROOT / "build/native"
    build.mkdir(parents=True, exist_ok=True)
    # Select the portable engine, not the historical Windows hook frontend.
    # Original upstream files remain unchanged and ship with the source.
    for src in (ROOT / "vendor/fcitx-unikey/unikey").iterdir():
        if src.suffix in (".cpp", ".h"):
            content = src.read_bytes()
            if src.name != "convert.cpp":
                content = content.replace(b"defined(_WIN32)", b"defined(UNIKEY_WINDOWS_FRONTEND)")
                content = content.replace(b"defined(WIN32)", b"defined(UNIKEY_WINDOWS_FRONTEND)")
            else:
                # The oracle uses memory conversion only. Disable the unused
                # POSIX file-export path instead of adding a temp-file shim.
                content = content.replace(b"mkstemp(tmpName)", b"(-1) /* file export disabled */")
            (build / src.name).write_bytes(content)
    output = ROOT / "telex_app/unikey_oracle.dll"
    output.parent.mkdir(exist_ok=True)
    sources = [str(p) for p in build.glob("*.cpp")] + [str(ROOT / "native/oracle.cpp")]
    compiler = shutil.which("cl", path=env["PATH"])
    if not compiler:
        raise RuntimeError("MSVC compiler was not found after vcvars64.")
    subprocess.run([compiler, "/nologo", "/LD", "/O2", "/MT", "/EHsc", "/std:c++17", "/D_CRT_SECURE_NO_WARNINGS", "/Dstrcasecmp=_stricmp", "/I"+str(build), *sources, "/link", "/OUT:"+str(output)], cwd=build, env=env, check=True)

if __name__ == "__main__":
    main()
