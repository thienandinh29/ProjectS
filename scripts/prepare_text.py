"""Convert a Markdown/LaTeX file to plain UTF-8 text before opening it in Gõ Việt.

    python scripts/prepare_text.py input.md output.txt
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from telex_app.importers import read_file
from telex_app.symbols import prepare_markdown


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    text, notes = prepare_markdown(read_file(sys.argv[1]))
    Path(sys.argv[2]).write_text(text + "\n", encoding="utf-8")
    print(f"Đã ghi {len(text):,} ký tự vào {sys.argv[2]}")
    for note in dict.fromkeys(notes):
        print(" -", note)


if __name__ == "__main__":
    main()
