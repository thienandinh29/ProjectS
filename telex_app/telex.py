"""Encode source text as Telex, then verify it against the upstream engine."""
from dataclasses import dataclass
from functools import lru_cache
import re
import unicodedata
from .oracle import Oracle

TONES = {"\u0301": "s", "\u0300": "f", "\u0309": "r", "\u0303": "x", "\u0323": "j"}
SHAPES = {"\u0302", "\u0306", "\u031b"}
BASES = "aăâeêioôơuưyđ"
VIETNAMESE = set(BASES + BASES.upper())
for _base in BASES[:-1]:
    for _tone in TONES:
        VIETNAMESE.update(unicodedata.normalize("NFC", c + _tone) for c in (_base, _base.upper()))
SUPPORTED = set(chr(i) for i in range(32, 127)) | VIETNAMESE | {"\n"}
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

@dataclass(frozen=True)
class Issue:
    start: int
    end: int
    message: str

class TextError(ValueError):
    def __init__(self, issues):
        self.issues = issues
        super().__init__(issues[0].message)

def normalize(text):
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    "))

def char_keys(char):
    if char in "đĐ":
        return ("Dd" if char == "Đ" else "dd"), ""
    pieces = unicodedata.normalize("NFD", char)
    base = pieces[0]
    keys, tone = base, ""
    for mark in pieces[1:]:
        if mark in TONES:
            tone = TONES[mark]
        elif mark == "\u0302":
            keys += base.lower()
        elif mark in {"\u0306", "\u031b"}:
            keys += "w"
    return keys, tone

class Encoder:
    def __init__(self, modern=False):
        self.oracle = Oracle(modern)

    @lru_cache(maxsize=8192)
    def word(self, word):
        if len(word) > 180:
            raise ValueError("Một từ quá dài (tối đa 180 ký tự). Hãy thêm khoảng trắng.")
        pieces = [char_keys(ch) for ch in word]
        body = "".join(k for k, _ in pieces)
        tones = "".join(t for _, t in pieces)
        candidates = [body + tones, "".join(k + t for k, t in pieces)]
        if word.isascii():
            keys, prefix = "", ""
            for char in word:
                prefix += char
                for n in range(1, 5):
                    attempt = keys + char * n
                    if self.oracle.render(attempt) == prefix:
                        keys = attempt
                        break
                else:
                    break
            else:
                candidates.insert(0, keys)
        for keys in candidates:
            if self.oracle.render(keys + " ") == word + " ":
                return keys
        raise ValueError(f"Không thể gõ chính xác “{word}” với cấu hình dấu hiện tại. Kiểm tra kiểu dấu oà/òa trong phần thiết lập.")

    def tokenize(self, text):
        issues = [Issue(i, i + 1, f"Ký tự chưa hỗ trợ: {ch!r} (U+{ord(ch):04X}).") for i, ch in enumerate(text) if ch not in SUPPORTED]
        if issues:
            raise TextError(issues)
        tokens = []
        cursor = 0
        for match in WORD.finditer(text):
            if cursor < match.start():
                tokens.append((text[cursor:match.start()], text[cursor:match.start()], False))
            try:
                tokens.append((match.group(), self.word(match.group()), True))
            except ValueError as error:
                issues.append(Issue(match.start(), match.end(), str(error)))
            cursor = match.end()
        if cursor < len(text):
            tokens.append((text[cursor:], text[cursor:], False))
        if issues:
            raise TextError(issues)
        # Catch context effects from digits/punctuation as well as word spelling.
        if self.oracle.render("".join(keys for _, keys, _ in tokens)) != text:
            raise TextError([Issue(0, len(text), "Chuỗi ký tự này bị UniKey đổi theo ngữ cảnh. Hãy tách chữ và số bằng khoảng trắng rồi kiểm tra lại.")])
        return tokens
