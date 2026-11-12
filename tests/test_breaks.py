import random
import unittest
from unittest.mock import Mock

from telex_app.engine import BREAK_SECONDS, BREAK_SENTENCES, Playback, Settings, prepare
from telex_app.oracle import Oracle
from telex_app.engine import render_unicode
from test_playback import Keyboard

SENTENCE = "Hôm nay trời đẹp. "
LONG = SENTENCE * 80 + "Hết."


def rests(plan):
    return [(i, s) for i, s in enumerate(plan.strokes) if s.rest]


class BreakTests(unittest.TestCase):
    def test_breaks_follow_sentence_ends_with_random_gaps(self):
        for mode in ("unicode", "telex"):
            plan = prepare(LONG, Settings(mode=mode), random.Random(7))
            output = "".join(s.key for s in plan.strokes)
            found = rests(plan)
            self.assertGreater(len(found), 3)
            gaps, last = [], 0
            for index, stroke in found:
                self.assertEqual(plan.strokes[index].key, ".")
                self.assertTrue(BREAK_SECONDS[0] <= stroke.rest <= BREAK_SECONDS[1])
                self.assertEqual(stroke.rest, int(stroke.rest))
                done = output[:index + 1].count(".")
                gaps.append(done - last)
                last = done
            self.assertTrue(all(BREAK_SENTENCES[0] <= g <= BREAK_SENTENCES[1] for g in gaps))
            self.assertGreater(len(set(gaps)) + len({s.rest for _, s in found}), 2)
            self.assertEqual(Oracle().render(output) if mode == "telex" else render_unicode(output), LONG)

    def test_different_seeds_give_different_schedules(self):
        schedules = {tuple((i, s.rest) for i, s in rests(prepare(LONG, Settings(mode="unicode"), random.Random(n)))) for n in range(5)}
        self.assertGreater(len(schedules), 1)

    def test_no_break_without_sentence_end_or_after_last_sentence(self):
        self.assertEqual(rests(prepare("a" * 3000, Settings(mode="unicode"))), [])
        self.assertEqual(rests(prepare("3.14 " * 400, Settings(mode="unicode"))), [])
        plan = prepare(SENTENCE * 30, Settings(mode="unicode"), random.Random(2))
        self.assertTrue(all(i < len(plan.strokes) - 2 for i, _ in rests(plan)))

    def test_newline_counts_once_and_corrections_keep_text(self):
        text = ("Việt Nam\n" * 60).strip()
        for mode in ("unicode", "telex"):
            plan = prepare(text, Settings(mode=mode, correction_rate=0.1), random.Random(1))
            self.assertTrue(rests(plan))
            output = "".join(s.key for s in plan.strokes)
            self.assertEqual(render_unicode(output) if mode == "unicode" else Oracle().render(output), text)

    def test_speed_does_not_scale_breaks(self):
        slow = prepare(LONG, Settings(mode="unicode"), random.Random(3))
        fast = prepare(LONG, Settings(speed=4, mode="unicode"), random.Random(3))
        self.assertEqual(sum(s.rest for s in slow.strokes), sum(s.rest for s in fast.strokes))
        total = sum(s.rest for s in slow.strokes)
        self.assertAlmostEqual(slow.estimated_seconds - total, (fast.estimated_seconds - total) * 4)

    def test_playback_waits_then_resumes(self):
        kb, seen = Keyboard(), []
        def notify(event, data):
            if event == "rest":
                seen.append((len(kb.sent), data))
        player = Playback(kb, notify)
        player.wait = Mock()
        plan = prepare(LONG, Settings(mode="unicode"), random.Random(4))
        player.run(plan, countdown=0)
        self.assertEqual(sum(1 for _, d in seen), sum(int(s.rest) for s in plan.strokes))
        self.assertEqual(len(kb.sent), len(plan.strokes))
        self.assertTrue(kb.closed)

    def test_stop_and_focus_loss_interrupt_break(self):
        plan = prepare(LONG, Settings(mode="unicode"), random.Random(5))
        first = rests(plan)[0][0] + 1
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
                self.assertEqual(len(kb.sent), first)
                self.assertEqual(messages[-1], ("finished", "stopped"))
                self.assertTrue(kb.closed)


if __name__ == "__main__":
    unittest.main()
