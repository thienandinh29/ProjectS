import unittest
from telex_app.math_text import convert_math


class MathTextTests(unittest.TestCase):
    def test_common_formulas(self):
        self.assertEqual(convert_math(r"MSE $L=\frac12(\hat y-y)^2$."),
                         "MSE L=(1)⁄(2)(ŷ-y)².")
        self.assertEqual(convert_math(r"$\hat y\in(0,1)$ và $\sum_{k=1}^3 y_k\ln\hat y_k$"),
                         "ŷ∈(0,1) và ∑ₖ₌₁³ yₖlnŷₖ")

    def test_nested_fractions_and_unknown_commands(self):
        self.assertEqual(convert_math(r"$\frac{a+b}{\frac{1}{2}}+\unknown{x}$"),
                         r"(a+b)⁄((1)⁄(2))+\unknown{x}")

    def test_unmatched_dollars_are_unchanged(self):
        self.assertEqual(convert_math("Chưa đóng $x+1"), "Chưa đóng $x+1")

if __name__ == "__main__":
    unittest.main()
