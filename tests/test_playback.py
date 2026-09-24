import threading
import time
import unittest
from telex_app.engine import Playback, Plan, Stroke

class Keyboard:
    def __init__(self):
        self.armed = False
        self.safe = True
        self.sent = []
        self.closed = False
        self.on_send = None
        self.monitor_error = False

    def start_monitor(self, stop):
        self.stop = stop
        if self.monitor_error:
            raise OSError("hooks unavailable")

    def arm(self):
        self.armed = True

    def target_is_safe(self):
        return self.safe

    def send(self, key):
        self.sent.append(key)
        if self.on_send:
            self.on_send()

    def close(self):
        self.closed = True
        self.armed = False

class PlaybackTests(unittest.TestCase):
    def plan(self, keys="abc", delay=0.0):
        return Plan(keys, tuple(Stroke(k, delay, i + 1) for i, k in enumerate(keys)), delay * len(keys), 0)

    def test_completes_and_unhooks(self):
        kb, messages = Keyboard(), []
        player = Playback(kb, lambda *event: messages.append(event))
        player.run(self.plan(), countdown=0)
        self.assertEqual(kb.sent, list("abc"))
        self.assertTrue(kb.closed)
        self.assertEqual(messages[-1], ("finished", "complete"))

    def test_stop_before_start(self):
        kb = Keyboard()
        player = Playback(kb)
        player.stop()
        player.run(self.plan(), countdown=0)
        self.assertFalse(kb.sent)
        self.assertTrue(kb.closed)

    def test_stop_countdown_and_long_delay(self):
        for countdown in (5, 0):
            kb = Keyboard()
            player = Playback(kb)
            worker = threading.Thread(target=player.run, args=(self.plan(delay=5),), kwargs={"countdown": countdown})
            worker.start()
            time.sleep(0.05)
            start = time.monotonic()
            player.stop()
            worker.join(0.3)
            self.assertFalse(worker.is_alive())
            self.assertLess(time.monotonic() - start, 0.3)
            self.assertEqual(kb.sent, [] if countdown else ["a"])

    def test_stop_during_backspaces(self):
        kb = Keyboard()
        player = Playback(kb)
        def stop_at_backspace():
            if kb.sent[-1] == "\b":
                player.stop()
        kb.on_send = stop_at_backspace
        player.run(self.plan("word \b\b\b\b\bright"), countdown=0)
        self.assertEqual(kb.sent, list("word \b"))

    def test_focus_loss_before_next_stroke(self):
        kb = Keyboard()
        player = Playback(kb)
        kb.on_send = lambda: setattr(kb, "safe", False)
        player.run(self.plan(), countdown=0)
        self.assertEqual(kb.sent, ["a"])

    def test_no_typing_when_hooks_fail(self):
        kb = Keyboard()
        kb.monitor_error = True
        messages = []
        Playback(kb, lambda *event: messages.append(event)).run(self.plan(), countdown=0)
        self.assertEqual(kb.sent, [])
        self.assertTrue(kb.closed)
        self.assertEqual(messages[-1], ("finished", "error"))

if __name__ == "__main__":
    unittest.main()
