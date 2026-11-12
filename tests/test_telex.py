import random
import unittest
import unicodedata
from telex_app.telex import Encoder, VIETNAMESE, TextError, normalize
from telex_app.engine import prepare, Settings, correction_keys, render_unicode
from telex_app.oracle import Oracle
from telex_app.ui import SAMPLE

class TelexTests(unittest.TestCase):
    def test_all_vietnamese_characters(self):
        encoder = Encoder()
        for char in sorted(VIETNAMESE):
            with self.subTest(char=ascii(char)):
                self.assertEqual(encoder.oracle.render(encoder.word(char) + " "), char + " ")

    def test_real_sentences_and_literal_telex_letters(self):
        text = "Đoàng. Tiếng Việt —".replace(" —", "")
        text += "\nTôi yêu quê hương, trường học và những người bạn.\n"
        text += "TIẾNG VIỆT: QUỐC GIA, NGƯỜI, ĐƯỜNG.\n"
        text += "coffee address success software Windows office roof offer issue assess W w aa ee oo dd as sf rr xx zz"
        plan = prepare(text)
        self.assertEqual(Oracle().render("".join(s.key for s in plan.strokes)), text)

    def test_sample_and_paragraphs(self):
        plan = prepare(SAMPLE)
        self.assertEqual(Oracle().render("".join(s.key for s in plan.strokes)), SAMPLE)
        self.assertIn("\n\n", plan.text)

    def test_modern_and_traditional_tone_placement(self):
        self.assertEqual(Encoder(False).oracle.render("hoaf"), "hòa")
        self.assertEqual(Encoder(True).oracle.render("hoaf"), "hoà")
        prepare("hòa thủy", Settings(modern=False))
        prepare("hoà thuỷ", Settings(modern=True))
        with self.assertRaises(TextError):
            prepare("hoà", Settings(modern=False))

    def test_decomposed_unicode_and_tabs(self):
        text = unicodedata.normalize("NFD", "Tiếng\tViệt\r\nĐoàng")
        self.assertEqual(prepare(text).text, "Tiếng    Việt\nĐoàng")

    def test_unsupported_characters_with_offsets(self):
        with self.assertRaises(TextError) as caught:
            prepare("a🙂b“c")
        self.assertEqual([(i.start, i.end) for i in caught.exception.issues], [(1, 2), (3, 4)])

    def test_blank_and_size_limits(self):
        for text in (" ", "a" * 100001):
            with self.assertRaises(TextError):
                prepare(text)

    def test_correction_does_not_touch_prefix(self):
        encoder = Encoder()
        for word in ("Việt", "Đoàng", "tiếng", "coffee", "đường", "NGƯỜI"):
            with self.subTest(word=word):
                script = correction_keys(encoder, word, encoder.word(word))
                self.assertIsNotNone(script)
                self.assertIn("\b", script)
                self.assertEqual(encoder.oracle.render(script + "!", prefix="PRE-EXISTING. "), "PRE-EXISTING. " + word + "!")

    def test_random_corrections_preserve_final_text(self):
        text = ("Đoàng và những người bạn yêu tiếng Việt. coffee address success!\n" * 8).rstrip()
        for seed in range(8):
            with self.subTest(seed=seed):
                plan = prepare(text, Settings(correction_rate=0.1), random.Random(seed))
                self.assertGreater(plan.corrections, 0)
                self.assertEqual(Oracle().render("".join(s.key for s in plan.strokes)), text)

    def test_speed_scaling_and_delays(self):
        slow = prepare("Việt.\n", Settings(speed=1), random.Random(3))
        fast = prepare("Việt.\n", Settings(speed=2), random.Random(3))
        self.assertAlmostEqual(slow.estimated_seconds, fast.estimated_seconds * 2)
        self.assertGreater(next(s.delay for s in slow.strokes if s.key == "."), 0.45)
        self.assertGreater(slow.strokes[-1].delay, 0.8)
        self.assertEqual(slow.strokes[-1].progress, len(slow.text))

    def test_oracle_rejects_deletion_before_insertion(self):
        with self.assertRaises(ValueError):
            Oracle().render("a " + "\b" * 3)

    def test_direct_unicode_keeps_vietnamese_and_punctuation(self):
        text = "Đoàng, ‘Tiếng Việt’ — hello 🙂!\nhoà và hòa"
        plan = prepare(text, Settings(mode="unicode"))
        self.assertEqual("".join(s.key for s in plan.strokes), text)

    def test_unicode_corrections_preserve_text(self):
        text = "Tiếng Việt rất đẹp. " * 20
        plan = prepare(text, Settings(mode="unicode", correction_rate=0.1), random.Random(1))
        self.assertGreater(plan.corrections, 0)
        self.assertEqual(render_unicode("".join(s.key for s in plan.strokes)), text)

    def test_unicode_preserves_greek_eta_in_vietnamese(self):
        text = "Hiệu suất η = 0.85. Tiếng Việt, ‘ký hiệu’ — 🙂."
        plan = prepare(text, Settings(mode="unicode"))
        self.assertEqual(plan.text, text)
        self.assertEqual(render_unicode("".join(s.key for s in plan.strokes)), text)

    def test_unicode_rejects_control_characters(self):
        with self.assertRaises(TextError):
            prepare("abc\x08d", Settings(mode="unicode"))

if __name__ == "__main__":
    unittest.main()
