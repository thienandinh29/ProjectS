import unittest

from telex_app.symbols import convert_math, convert_scripts


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

    def test_latex_cases(self):
        cases = {
            r"$a_j^{(1)} = \max(0, z_j^{(1)})$": "aⱼ⁽¹⁾ = max(0, zⱼ⁽¹⁾)",
            r"$$\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$$": "∑ᵢ₌₁ⁿ i = (n(n+1))/2",
            r"\int_0^1 x\,dx = \frac12": "∫₀¹ x dx = 1/2",
            r"\frac{-b \pm \sqrt{\Delta}}{2a}": "(-b ± √Δ)/(2a)",
            r"\alpha \to \infty, x \in \mathbb{R}^n": "α → ∞, x ∈ ℝⁿ",
            r"\mathbf{W}^{(1)} \hat{y} \sqrt[3]{8}": "𝐖⁽¹⁾ ŷ ³√8",
            r"\left( x \right) \leq \text{max}": "( x ) ≤ max",
            r"\(\theta_1\) và \[\pi r^2\]": "θ₁ và πr²",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                out, skipped = convert_math(source)
                self.assertEqual(out, expected)
                self.assertEqual(skipped, [])

    def test_unknown_and_non_math_left_alone(self):
        out, skipped = convert_math(r"Giá $5 và $6. \foo x_{1,2}")
        self.assertEqual(out, r"Giá $5 và $6. \foo x_{1,2}")
        self.assertEqual(skipped, [r"\foo", "_{1,2}"])
        self.assertEqual(convert_math("Tiếng Việt có dấu.")[0], "Tiếng Việt có dấu.")

    def test_markdown_escapes_and_bold(self):
        self.assertEqual(convert_math(r"a \< b \> c \* d"), ("a < b > c * d", []))
        self.assertEqual(convert_math("**W** và **a_j**"), ("𝐖 và 𝐚ⱼ", []))
        out, skipped = convert_math("**Chương 1**: a ** b")
        self.assertEqual(out, "Chương 1: a ** b")
        self.assertEqual(skipped, ["(bỏ in đậm ở 1 đoạn chữ có dấu, giữ chữ thường)"])
        self.assertEqual(convert_math(r"**\alpha**")[0], "α")

    def test_html_sub_sup_and_aggregated_note(self):
        out, skipped = convert_math("z<sup>(1)</sup> = W<SUP>(1)</SUP>x + b<sub>2</sub>, ŷ = σ(z<sup>(2)</sup>)")
        self.assertEqual(out, "z⁽¹⁾ = W⁽¹⁾x + b₂, ŷ = σ(z⁽²⁾)")
        self.assertEqual(skipped, [])
        out, skipped = convert_math("**Bước 1** **Bước 2** x<sub>q</sub>")
        self.assertEqual(out, "Bước 1 Bước 2 x_q")
        self.assertEqual(skipped, ["(đổi sang dạng ^(…) hoặc _(…) ở 1 chỗ không có chỉ số Unicode)", "(bỏ in đậm ở 2 đoạn chữ có dấu, giữ chữ thường)"])

    def test_html_script_fallbacks_from_real_text(self):
        src = "a<sup>−0.732</sup> b<sub>t−1</sub> c<sub>y</sub> d<sup>2×1</sup> e<sup>−z</sup> f<sup>0.20303</sup>"
        out, skipped = convert_math(src)
        self.assertEqual(out, "a^(−0.732) bₜ₋₁ c_y d^(2×1) e⁻ᶻ f^(0.20303)")
        self.assertEqual(skipped, ["(đổi sang dạng ^(…) hoặc _(…) ở 4 chỗ không có chỉ số Unicode)"])


if __name__ == "__main__":
    unittest.main()
