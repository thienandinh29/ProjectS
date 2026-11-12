import random
import unittest
from unittest.mock import Mock

from telex_app.engine import BREAK_SECONDS, Playback, Settings, break_seconds, prepare
from telex_app.oracle import Oracle
from telex_app.engine import render_unicode
from test_playback import Keyboard


class BreakTests(unittest.TestCase):
    def test_exact_boundaries_and_no_final_break(self):
        for size, expected in ((499, []), (500, []), (501, [500]),
                               (1000, [500]), (1001, [500, 1000])):
            with self.subTest(size=size):
                plan = prepare("1" * size, Settings(mode="unicode"))
                self.assertEqual([s.progress for s in plan.strokes if s.rest], expected)
                self.assertEqual(sum(s.rest for s in plan.strokes), break_seconds(size))
                self.assertAlmostEqual(plan.estimated_seconds,
                                       sum(s.delay for s in plan.strokes) + 10 * len(expected))

    def test_break_inside_long_unicode_word(self):
        plan = prepare("η" * 1001, Settings(mode="unicode"))
        self.assertEqual([i + 1 for i, s in enumerate(plan.strokes) if s.rest], [500, 1000])

    def test_telex_counts_source_not_modifier_keys(self):
        for text in ("đ " * 251, "a " * 249 + "Việt xyz"):
            plan = prepare(text)
            self.assertEqual([s.progress for s in plan.strokes if s.rest], [500])
            self.assertEqual(Oracle().render("".join(s.key for s in plan.strokes)), text)
            index = next(i for i, s in enumerate(plan.strokes) if s.rest)
            self.assertEqual(len(Oracle().render("".join(s.key for s in plan.strokes[:index + 1]))), 500)

    def test_corrections_do_not_count_temporary_typing(self):
        for mode in ("unicode", "telex"):
            text = "Việt " * 201
            plan = prepare(text, Settings(mode=mode, correction_rate=0.1), random.Random(1))
            self.assertGreater(plan.corrections, 0)
            self.assertEqual([s.progress for s in plan.strokes if s.rest], [500, 1000])
            output = "".join(s.key for s in plan.strokes)
            self.assertEqual(render_unicode(output) if mode == "unicode" else Oracle().render(output), text)

    def test_speed_does_not_scale_breaks(self):
        text = "1" * 501
        slow = prepare(text, Settings(mode="unicode"), random.Random(3))
        fast = prepare(text, Settings(speed=4, mode="unicode"), random.Random(3))
        self.assertEqual(sum(s.rest for s in fast.strokes), BREAK_SECONDS)
        self.assertAlmostEqual(slow.estimated_seconds - 10, (fast.estimated_seconds - 10) * 4)

    def test_playback_waits_then_resumes(self):
        kb, rests = Keyboard(), []
        def notify(event, data):
            if event == "rest":
                rests.append((len(kb.sent), data))
        player = Playback(kb, notify)
        player.wait = Mock()
        player.run(prepare("1" * 501, Settings(mode="unicode")), countdown=0)
        self.assertEqual([data[2] for _, data in rests], list(range(10, 0, -1)))
        self.assertTrue(all(count == 500 for count, _ in rests))
        self.assertEqual(sum(call.args == (1,) for call in player.wait.call_args_list), 10)
        self.assertEqual(len(kb.sent), 501)
        self.assertTrue(kb.closed)

    def test_stop_and_focus_loss_interrupt_break(self):
        plan = prepare("1" * 501, Settings(mode="unicode"))
        # Skip ordinary typing delays; retain the real cancellable break wait.
        for lose_focus in (False, True):
            with self.subTest(lose_focus=lose_focus):
                kb, messages = Keyboard(), []
                def notify(event, data):
                    messages.append((event, data))
                    if event == "rest":
                        if lose_focus:
                            kb.safe = False
                        else:
                            player.stop()
                player = Playback(kb, notify)
                original_wait = player.wait
                player.wait = lambda seconds: original_wait(seconds if seconds in (0, 1) else 0)
                player.run(plan, countdown=0)
                self.assertEqual(len(kb.sent), 500)
                self.assertEqual(messages[-1], ("finished", "stopped"))
                self.assertTrue(kb.closed)


if __name__ == "__main__":
    unittest.main()
