"""Turn a_j^(1) style markup into Unicode subscript / superscript characters."""
import re

_SUB = dict(zip("0123456789+-=()aehijklmnoprstuvx", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"))
_SUP = dict(zip("0123456789+-=()abcdefghijklmnoprstuvwxyz",
                "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ"))
_SUP.update(zip("ABDEGHIJKLMNOPRTUVW", "ᴬᴮᴰᴱᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿᵀᵁⱽᵂ"))
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
