"""Turn LaTeX and a_j^(1) style markup into Unicode text (symbols, sub/superscripts)."""
import re
import string
import unicodedata

_SUB = dict(zip("0123456789+-=()aehijklmnoprstuvx", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"))
_SUP = dict(zip("0123456789+-=()abcdefghijklmnoprstuvwxyz",
                "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ"))
_SUP.update(zip("ABDEGHIJKLMNOPRTUVW", "ᴬᴮᴰᴱᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿᵀᵁⱽᵂ"))
_SUB["−"], _SUP["−"] = "₋", "⁻"  # U+2212 minus sign, as produced by Word/Docs
# _ or ^ followed by {group}, (group) or one letter/digit/sign.
_PATTERN = re.compile(r"([_^])(\{[^{}\n]*\}|\([^()\n]*\)|[A-Za-z0-9+\-=])")

def convert_scripts(text):
    """Return (new_text, skipped). Markup that cannot be fully converted is left unchanged."""
    skipped = []
    def replace(match):
        mark, body = match.groups()
        table = _SUB if mark == "_" else _SUP
        keep = body.startswith("(")
        inner = body[1:-1] if body[0] in "{(" else body
        source = ("(" + inner + ")") if keep else inner
        try:
            return "".join(table[c] for c in source)
        except KeyError:
            skipped.append(match.group())
            return match.group()
    return _PATTERN.sub(replace, text), skipped


_GREEK = dict(
    alpha="α", beta="β", gamma="γ", delta="δ", epsilon="ε", varepsilon="ε", zeta="ζ", eta="η", theta="θ",
    vartheta="ϑ", iota="ι", kappa="κ", lambda_="λ", mu="μ", nu="ν", xi="ξ", pi="π", varpi="ϖ", rho="ρ",
    varrho="ϱ", sigma="σ", varsigma="ς", tau="τ", upsilon="υ", phi="φ", varphi="ϕ", chi="χ", psi="ψ", omega="ω",
    Gamma="Γ", Delta="Δ", Theta="Θ", Lambda="Λ", Xi="Ξ", Pi="Π", Sigma="Σ", Upsilon="Υ", Phi="Φ", Psi="Ψ", Omega="Ω",
)
_GREEK["lambda"] = _GREEK.pop("lambda_")
_SYMBOLS = dict(
    leq="≤", le="≤", geq="≥", ge="≥", neq="≠", ne="≠", approx="≈", equiv="≡", sim="∼", simeq="≃", cong="≅",
    propto="∝", ll="≪", gg="≫", pm="±", mp="∓", times="×", div="÷", cdot="·", ast="∗", star="⋆", circ="∘",
    bullet="•", oplus="⊕", otimes="⊗", sum="∑", prod="∏", coprod="∐", int="∫", iint="∬", iiint="∭", oint="∮",
    sqrt_="√", partial="∂", nabla="∇", infty="∞", forall="∀", exists="∃", nexists="∄", neg="¬", lnot="¬",
    land="∧", wedge="∧", lor="∨", vee="∨", in_="∈", notin="∉", ni="∋", subset="⊂", supset="⊃", subseteq="⊆",
    supseteq="⊇", cup="∪", cap="∩", setminus="∖", emptyset="∅", varnothing="∅", to="→", rightarrow="→",
    leftarrow="←", leftrightarrow="↔", Rightarrow="⇒", Leftarrow="⇐", Leftrightarrow="⇔", implies="⟹",
    iff="⟺", mapsto="↦", uparrow="↑", downarrow="↓", longrightarrow="⟶", ldots="…", cdots="⋯", dots="…",
    vdots="⋮", ddots="⋱", degree="°", prime="′", angle="∠", perp="⊥", parallel="∥", mid="∣", therefore="∴",
    because="∵", langle="⟨", rangle="⟩", lfloor="⌊", rfloor="⌋", lceil="⌈", rceil="⌉", hbar="ℏ", ell="ℓ",
    Re="ℜ", Im="ℑ", aleph="ℵ", top="⊤", triangle="△", square="□", checkmark="✓",
)
_SYMBOLS["in"] = _SYMBOLS.pop("in_")
_SYMBOLS["sqrt"] = None  # handled as a command with an argument
_SYMBOLS.pop("sqrt_")
_NAMED = {"sin", "cos", "tan", "cot", "sec", "csc", "log", "ln", "exp", "lim", "max", "min", "sup", "inf",
          "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "det", "dim", "gcd", "mod", "arg", "deg", "ker"}
_SPACES = {",": " ", ";": " ", ":": " ", " ": " ", "!": "", "quad": "  ", "qquad": "    "}
_ESCAPED = set("{}%&_$#")
_ACCENTS = dict(hat="\u0302", widehat="\u0302", bar="\u0304", overline="\u0304", vec="\u20d7", dot="\u0307",
                ddot="\u0308", tilde="\u0303", widetilde="\u0303", underline="\u0332")
_STYLE_PLAIN = {"text", "mathrm", "mathit", "mathbb", "mathcal", "mathsf", "mathtt", "operatorname", "textrm",
                "textit", "displaystyle", "mbox"}
_STYLE_BOLD = {"mathbf", "boldsymbol", "bm", "textbf"}
_BLACKBOARD = dict(zip("CHNPQRZ", "ℂℍℕℙℚℝℤ"))


def _bold(text):
    out = []
    for c in text:
        if "A" <= c <= "Z":
            out.append(chr(0x1D400 + ord(c) - 65))
        elif "a" <= c <= "z":
            out.append(chr(0x1D41A + ord(c) - 97))
        else:
            out.append(c)
    return "".join(out)


def _group(s, i):
    """s[i] == '{': return (content, index after the matching brace) or None."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    return None


def _arg(s, i):
    """Read one LaTeX argument at s[i:] (skipping spaces): braces group or a single character."""
    while i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s):
        return None
    if s[i] == "{":
        return _group(s, i)
    if s[i] == "\\":
        m = re.match(r"\\[A-Za-z]+", s[i:])
        if m:
            return m.group(), i + m.end()
    return s[i], i + 1


def _wrap(text):
    return text if len(text) == 1 or text.isdigit() else "(" + text + ")"


def _latex(s, skipped, eat=False):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            m = re.match(r"\\([A-Za-z]+)", s[i:])
            if not m:
                nxt = s[i + 1]
                if nxt == "\\":
                    out.append("\n")
                elif nxt in _SPACES:
                    out.append(_SPACES[nxt])
                elif nxt in _ESCAPED or nxt in string.punctuation:
                    out.append(nxt)  # LaTeX escapes (\%) and Markdown escapes (\<, \*, \#)
                else:
                    out.append(s[i:i + 2])
                    skipped.append(s[i:i + 2])
                i += 2
                continue
            name, i = m.group(1), i + m.end()
            if name in _GREEK:
                out.append(_GREEK[name])
                # TeX ignores the space after a command: "\\pi r^2" is "πr²".
                if eat and re.match(r" +[A-Za-z0-9]", s[i:]):
                    i += len(s[i:]) - len(s[i:].lstrip(" "))
            elif name in _SYMBOLS and _SYMBOLS[name]:
                out.append(_SYMBOLS[name])
            elif name in _NAMED:
                out.append(name)
            elif name in _SPACES:
                out.append(_SPACES[name])
            elif name in ("left", "right", "big", "Big", "bigg", "Bigg", "limits", "nolimits"):
                if i < len(s) and s[i] == ".":
                    i += 1
            elif name in ("begin", "end"):
                got = _arg(s, i)
                if got:
                    i = got[1]
            elif name == "frac" or name == "dfrac" or name == "tfrac":
                a, b = _arg(s, i), None
                if a:
                    b = _arg(s, a[1])
                if a and b:
                    out.append(_wrap(_latex(a[0], skipped, eat)) + "/" + _wrap(_latex(b[0], skipped, eat)))
                    i = b[1]
                else:
                    out.append("\\" + name)
                    skipped.append("\\" + name)
            elif name == "sqrt":
                index = None
                if i < len(s) and s[i] == "[" and "]" in s[i:]:
                    end = s.index("]", i)
                    index, i = s[i + 1:end], end + 1
                a = _arg(s, i)
                if a:
                    body = _latex(a[0], skipped, eat)
                    prefix = ("".join(_SUP.get(ch, ch) for ch in index)) if index else ""
                    out.append(prefix + "√" + _wrap(body))
                    i = a[1]
                else:
                    out.append("√")
            elif name in _ACCENTS:
                a = _arg(s, i)
                if a:
                    body = _latex(a[0], skipped, eat)
                    out.append((body[:-1] + body[-1] + _ACCENTS[name]) if len(body) == 1 else body + _ACCENTS[name])
                    i = a[1]
            elif name in _STYLE_PLAIN or name in _STYLE_BOLD:
                a = _arg(s, i)
                if a:
                    body = _latex(a[0], skipped, eat)
                    if name == "mathbb":
                        body = "".join(_BLACKBOARD.get(ch, ch) for ch in body)
                    elif name in _STYLE_BOLD:
                        body = _bold(body)
                    out.append(body)
                    i = a[1]
            else:
                out.append("\\" + name)
                skipped.append("\\" + name)
            continue
        if c in "^_" and i + 1 < len(s) and s[i + 1] == "{":
            grp = _group(s, i + 1)
            if grp:
                out.append(c + "{" + _latex(grp[0], skipped, eat) + "}")
                i = grp[1]
                continue
        if c == "{":
            grp = _group(s, i)
            if grp:
                out.append(_latex(grp[0], skipped, eat))
                i = grp[1]
                continue
        out.append(c)
        i += 1
    return "".join(out)


_MATH_SPANS = [
    re.compile(r"\$\$(.+?)\$\$", re.S),
    re.compile(r"\\\[(.+?)\\\]", re.S),
    re.compile(r"\\\((.+?)\\\)", re.S),
    re.compile(r"(?<![\\$])\$([^$\n]+)\$(?!\$)"),
]


_PLAIN_NOTE = "\0plain"
_FALLBACK_NOTE = "\0fallback"
_KEEP_SUB, _KEEP_SUP = "\ue001", "\ue002"
_HTML_SCRIPT = re.compile(r"<(sub|sup)>(.*?)</\1>", re.I | re.S)
_BOLD_MD = re.compile(r"\*\*(?=\S)([^\n]+?)(?<=\S)\*\*")


def _markdown_bold(content, skipped):
    """**text** -> Unicode bold. Letters with accents (Vietnamese, Greek) have no bold form:
    the markers are dropped and the text stays plain, which is reported."""
    content, left = convert_scripts(content)  # sub/superscripts first: they cannot be bold
    skipped.extend(left)
    marks = set(_SUB.values()) | set(_SUP.values())
    if any(ch.isalpha() and not ch.isascii() and ch not in marks for ch in content):
        skipped.append(_PLAIN_NOTE)
        return content
    return _bold(content)


def _html_script(match, skipped):
    """<sub>2</sub> / <sup>(1)</sup> (HTML inside Markdown) -> subscript / superscript."""
    is_sub = match.group(1).lower() == "sub"
    table = _SUB if is_sub else _SUP
    try:
        return "".join(table[c] for c in match.group(2))
    except KeyError:
        # No Unicode form (decimal point, ×, subscript y...): readable plain notation instead.
        skipped.append(_FALLBACK_NOTE)
        body = match.group(2)
        # Placeholder marks keep the later _/^ pass from reprocessing this plain notation.
        return (_KEEP_SUB if is_sub else _KEEP_SUP) + (body if len(body) == 1 else "(" + body + ")")


def convert_math(text):
    """Translate LaTeX, then a_j^(1) markup. Returns (new_text, skipped)."""
    skipped = []
    for pattern in _MATH_SPANS:
        # Delimiters count only if the inside looks like math: "$5 and $6" and Markdown's
        # escaped brackets "\\[1, 2\\]" stay as text. "$$" is always math.
        text = pattern.sub(lambda m: _latex(m.group(1), skipped, True) if pattern is _MATH_SPANS[0] or re.search(r"[\\^_{]", m.group(1)) else m.group(0), text)
    text = _latex(text, skipped)
    text = _HTML_SCRIPT.sub(lambda m: _html_script(m, skipped), text)
    text = _BOLD_MD.sub(lambda m: _markdown_bold(m.group(1), skipped), text)
    text, left = convert_scripts(text)
    skipped = skipped + left
    plain, fallback = skipped.count(_PLAIN_NOTE), skipped.count(_FALLBACK_NOTE)
    skipped = [x for x in skipped if x not in (_PLAIN_NOTE, _FALLBACK_NOTE)]
    if fallback:
        skipped.append(f"(đổi sang dạng ^(…) hoặc _(…) ở {fallback} chỗ không có chỉ số Unicode)")
    if plain:
        skipped.append(f"(bỏ in đậm ở {plain} đoạn chữ có dấu, giữ chữ thường)")
    text = text.replace(_KEEP_SUB, "_").replace(_KEEP_SUP, "^")
    return unicodedata.normalize("NFC", text), skipped


def markdown_to_text(text):
    """Drop Markdown structure that would be typed literally (and that Google Docs would
    auto-format): headings, quotes, rules, HTML wrappers, list markers, table pipes, italics."""
    out = []
    for line in text.split("\n"):
        stripped = line.strip()
        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped):
            continue
        if re.fullmatch(r"\|?[\s:|-]+\|?", stripped) and "-" in stripped and "|" in stripped:
            continue  # table separator row
        line = re.sub(r"^\s*>+ ?", "", line)
        line = re.sub(r"^\s*#{1,6}\s+", "", line)
        line = re.sub(r"^(\s*)[-*+] +", r"\1• ", line)  # "- " would start a Docs list
        if line.strip().startswith("|") and line.strip().endswith("|"):
            cells = [c.strip() for c in line.strip()[1:-1].split("|")]
            line = " | ".join(c for c in cells if c)
            if not line:
                continue
        line = re.sub(r"</?(?:p|b|i|em|strong|br|div|span)\b[^>]*>", "", line, flags=re.I)
        line = re.sub(r"(?<![*\w])\*(?=\S)([^*\n]+?)(?<=\S)\*(?![*\w])", r"\1", line)
        out.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip("\n")


def prepare_markdown(text):
    """Markdown/LaTeX source -> plain text ready to type. Returns (text, notes)."""
    text, notes = convert_math(text)
    return markdown_to_text(text), notes
