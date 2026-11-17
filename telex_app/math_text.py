"""Convert common inline LaTeX math to readable Unicode plain text."""
import re

SYMBOLS = {
    "in": "∈", "notin": "∉", "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥",
    "neq": "≠", "ne": "≠", "times": "×", "cdot": "·", "pm": "±", "infty": "∞",
    "sum": "∑", "prod": "∏", "alpha": "α", "beta": "β", "gamma": "γ",
    "delta": "δ", "theta": "θ", "lambda": "λ", "mu": "μ", "sigma": "σ",
    "pi": "π", "Delta": "Δ", "Sigma": "Σ", "rightarrow": "→", "to": "→",
    "ln": "ln", "log": "log", "sin": "sin", "cos": "cos", "left": "", "right": "",
}
SUPER = str.maketrans("0123456789+-=()in", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁱⁿ")
SUB = str.maketrans("0123456789+-=()aeoxihklmnprstuv", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓᵢₕₖₗₘₙₚᵣₛₜᵤᵥ")

def _argument(text, index):
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text):
        return None, index
    if text[index] == "{":
        depth = 1
        end = index + 1
        while end < len(text) and depth:
            depth += (text[end] == "{") - (text[end] == "}")
            end += 1
        if depth:
            return None, index
        return text[index + 1:end - 1], end
    if text[index] == "\\":
        match = re.match(r"\\[A-Za-z]+|\\.", text[index:])
        if match:
            return match.group(), index + len(match.group())
    return text[index], index + 1

def _math(text):
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        if char == "\\":
            match = re.match(r"\\([A-Za-z]+|.)", text[i:])
            if not match:
                result.append(char)
                i += 1
                continue
            command = match.group(1)
            end = i + len(match.group())
            if command == "frac":
                numerator, after_num = _argument(text, end)
                denominator, after_den = _argument(text, after_num)
                if numerator is not None and denominator is not None:
                    result.append("(" + _math(numerator) + ")⁄(" + _math(denominator) + ")")
                    i = after_den
                    continue
            if command in ("hat", "bar", "vec"):
                arg, after = _argument(text, end)
                if arg is not None:
                    value = _math(arg)
                    result.append(value + {"hat": "̂", "bar": "̄", "vec": "⃗"}[command])
                    i = after
                    continue
            if command not in SYMBOLS and end < len(text) and text[end] == "{":
                arg, after = _argument(text, end)
                if arg is not None:
                    result.append(text[i:after])
                    i = after
                    continue
            result.append(SYMBOLS.get(command, match.group()))
            i = end
        elif char in "_^":
            arg, end = _argument(text, i + 1)
            if arg is None:
                result.append(char)
                i += 1
                continue
            value = _math(arg)
            table = SUB if char == "_" else SUPER
            converted = value.translate(table)
            result.append(converted if all(ord(c) in table for c in value) else char + ("{" + value + "}" if len(value) > 1 else value))
            i = end
        elif char in "{}":
            i += 1
        else:
            result.append(char)
            i += 1
    return "".join(result)

def convert_math(text):
    """Convert balanced single-dollar expressions; leave other text untouched."""
    return re.sub(r"(?<!\\)\$(?!\$)([^$\n]+)(?<!\\)\$(?!\$)", lambda m: _math(m.group(1)), text)
