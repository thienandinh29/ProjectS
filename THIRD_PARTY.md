# Third-party software

Gõ Việt is distributed under GPL-3.0-or-later with complete corresponding source.

The offline oracle incorporates the UniKey engine by Pham Kim Long, from
https://github.com/fcitx/fcitx-unikey at commit
`2ea5bee3a3209a76b0de330cb63f574d9e82e5cb`.
Upstream files are kept unchanged in `vendor/fcitx-unikey`. Their individual
GPL/LGPL notices remain intact. The root distribution uses GPL v3 (per the
engine's GPL-2.0-or-later terms); the GPL v3 license is in `LICENSE.txt`.

`scripts/build_native.py` makes build-directory copies with Windows frontend
conditionals disabled so the portable core can be compiled independently of the
legacy Windows hook frontend. The unused POSIX file-output temp-file operation
is disabled. `native/oracle.cpp` adds three small entry points for in-memory
verification only. It neither installs nor replaces the user's UniKey software.

Bundled runtime dependencies include Python 3.11, Tcl/Tk 8.6, python-docx 1.2.0,
lxml 6.1.3 and typing_extensions 4.16.0. PyInstaller 6.22.3 packages the program
using its bootloader exception. Their notices are collected under `licenses/`
in the source archive and embedded in the executable. The native oracle uses
MSVC's statically linked runtime. No Google API credentials are included.

UniKey project information: https://www.unikey.org/en/source.html
