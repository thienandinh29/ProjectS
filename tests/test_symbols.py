import unittest

from telex_app.symbols import convert_scripts


class SymbolTests(unittest.TestCase):
    def test_example_from_user(self):
        out, skipped = convert_scripts("a_j^(1) = max(0, z_j^(1))")
        self.assertEqual(out, "aⱼ⁽¹⁾ = max(0, zⱼ⁽¹⁾)")
        self.assertEqual(skipped, [])

    def test_braces_and_plain_text(self):
        self.assertEqual(convert_scripts("x^{2n+1} + y_{12} = z²")[0], "x²ⁿ⁺¹ + y₁₂ = z²")
        self.assertEqual(convert_scripts("Tiếng Việt")[0], "Tiếng Việt")

    def test_unsupported_is_kept_and_reported(self):
        out, skipped = convert_scripts("a_q và b^q")
        self.assertEqual(out, "a_q và b^q")
        self.assertEqual(skipped, ["_q", "^q"])


if __name__ == "__main__":
    unittest.main()
