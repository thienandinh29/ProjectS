"""Preflight, independently verified correction scripts, and cancellable playback."""
from dataclasses import dataclass
import random
import time
import threading
from .telex import Encoder, TextError, Issue, normalize
from .telex import WORD, VIETNAMESE
from .importers import MAX_CHARS

BREAK_INTERVAL = 500
BREAK_SECONDS = 10

def break_seconds(size):
    return max(0, (size - 1) // BREAK_INTERVAL) * BREAK_SECONDS

@dataclass(frozen=True)
class Settings:
    speed: float = 1.0
    correction_rate: float = 0.0
    modern: bool = False
    mode: str = "telex"

def unicode_tokens(text):
    issues = [Issue(i, i+1, f"Ký tự điều khiển chưa hỗ trợ: U+{ord(c):04X}.")
              for i, c in enumerate(text) if c != "\n" and (not c.isprintable() or 0xD800 <= ord(c) <= 0xDFFF)]
    if issues:
        raise TextError(issues)
    tokens, cursor = [], 0
    for match in WORD.finditer(text):
        if cursor < match.start():
            tokens.append((text[cursor:match.start()], text[cursor:match.start()], False))
        tokens.append((match.group(), match.group(), True))
        cursor = match.end()
    if cursor < len(text):
        tokens.append((text[cursor:], text[cursor:], False))
    return tokens

def render_unicode(keys):
    chars = []
    for char in keys:
        if char == "\b":
            if not chars:
                raise ValueError("Correction would delete pre-existing text")
            chars.pop()
        else:
            chars.append(char)
    return "".join(chars)

@dataclass(frozen=True)
class Stroke:
    key: str
    delay: float
    progress: int
    rest: float = 0.0

@dataclass(frozen=True)
class Plan:
    text: str
    strokes: tuple
    estimated_seconds: float
    corrections: int

def correction_keys(encoder, word, correct):
    # A plain consonant misspelling has a known visible length. Commit with a
    # space before erasing, and prove the whole transaction with UniKey.
    wrong = "d" + word[1:] if word[0].lower() != "d" else "b" + word[1:]
    try:
        typed = encoder.word(wrong)
    except ValueError:
        return None
    script = typed + " " + "\b" * (len(wrong) + 1) + correct
    sentinel = "KEEP. "
    if encoder.oracle.render(script + " ", prefix=sentinel) != sentinel + word + " ":
        return None
    return script

def prepare(text, settings=Settings(), rng=None, cancel=None):
    if settings.mode not in ("telex", "unicode"):
        raise ValueError("Chế độ gõ không hợp lệ.")
    if not 0.25 <= settings.speed <= 4 or not 0 <= settings.correction_rate <= 0.10:
        raise ValueError("Thiết lập tốc độ hoặc tần suất không hợp lệ.")
    text = normalize(text)
    if not text.strip():
        raise TextError([Issue(0, 0, "Hãy nhập nội dung trước khi bắt đầu.")])
    if len(text) > MAX_CHARS:
        raise TextError([Issue(0, len(text), "Tối đa 100.000 ký tự mỗi lần.")])
    encoder, rng = Encoder(settings.modern) if settings.mode == "telex" else None, rng or random.Random()
    tokens = encoder.tokenize(text) if encoder else unicode_tokens(text)
    strokes, progress, corrections = [], 0, 0
    next_break = BREAK_INTERVAL
    for token, keys, is_word in tokens:
        if cancel and cancel.is_set():
            raise Cancelled()
        script = keys
        if is_word and len(token) >= 3 and progress > 0 and text[progress - 1].isspace() and rng.random() < settings.correction_rate:
            if encoder:
                candidate = correction_keys(encoder, token, keys)
            elif all(c in VIETNAMESE or c.isascii() for c in token):
                wrong = ("d" if token[0].lower() != "d" else "b") + token[1:]
                candidate = wrong + " " + "\b" * (len(wrong) + 1) + keys
            else:
                candidate = None
            if candidate:
                script = candidate
                corrections += 1
        # Count source characters only in the final, correct spelling. Telex
        # modifiers and the temporary typo/backspaces do not advance the count.
        correct_start = len(script) - len(keys)
        crosses_break = progress < next_break <= progress + len(token) and next_break < len(text)
        for index, key in enumerate(script):
            delay = rng.uniform(0.100, 0.220)
            if key in ".!?":
                delay += rng.uniform(0.45, 1.0)
            elif key in ",;:":
                delay += rng.uniform(0.18, 0.45)
            elif key == "\n":
                delay += rng.uniform(0.8, 1.6)
            if index + 1 < len(script) and script[index + 1] == "\b" and key != "\b":
                delay += rng.uniform(0.4, 0.8)
            completed = progress + len(token) if index == len(script) - 1 else progress
            if index >= correct_start:
                correct_index = index - correct_start
                if not encoder or not is_word:
                    completed = progress + correct_index + 1
                elif crosses_break:
                    completed = progress + min(len(token), len(encoder.oracle.render(keys[:correct_index + 1])))
            rest = 0.0
            if next_break <= completed and next_break < len(text):
                rest = BREAK_SECONDS
                next_break += BREAK_INTERVAL
            strokes.append(Stroke(key, delay / settings.speed, completed, rest))
        progress += len(token)
    output = "".join(s.key for s in strokes)
    if (encoder.oracle.render(output) if encoder else render_unicode(output)) != text:
        raise TextError([Issue(0, len(text), "Kế hoạch sửa lỗi không cho kết quả chính xác; hãy tắt sửa lỗi rồi thử lại.")])
    return Plan(text, tuple(strokes), sum(s.delay + s.rest for s in strokes), corrections)

class Cancelled(Exception):
    pass

class Playback:
    """No event queue in the OS: send one complete key stroke at a time."""
    def __init__(self, keyboard, notify=lambda *_: None):
        self.keyboard = keyboard
        self.notify = notify
        self.cancelled = threading.Event()
        self.reason = "Đã dừng. Nội dung đã gõ được giữ nguyên."
        self._send_lock = threading.RLock()

    def stop(self, reason=None):
        # Set first: cancellation also wakes all punctuation/countdown waits.
        self.cancelled.set()
        if reason:
            self.reason = reason
        with self._send_lock:
            pass  # Wait only for a stroke already being dispatched.

    def wait(self, seconds):
        deadline = time.monotonic() + seconds
        while True:
            if self.cancelled.is_set():
                raise Cancelled()
            if self.keyboard.armed and not self.keyboard.target_is_safe():
                self.stop("Đã dừng vì cửa sổ/tài liệu đích hoặc tiêu điểm đã thay đổi.")
                raise Cancelled()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            self.cancelled.wait(min(0.025, remaining))

    def run(self, plan, countdown=5):
        outcome = "stopped"
        try:
            self.keyboard.start_monitor(self.stop)
            for seconds in range(countdown, 0, -1):
                self.notify("countdown", seconds)
                self.wait(1)
            if self.cancelled.is_set():
                raise Cancelled()
            self.keyboard.arm()
            self.wait(0)
            remaining = plan.estimated_seconds
            for stroke in plan.strokes:
                with self._send_lock:
                    self.wait(0)
                    self.keyboard.send(stroke.key)
                self.notify("progress", (stroke.progress, len(plan.text), remaining))
                self.wait(stroke.delay)
                remaining = max(0, remaining - stroke.delay)
                if stroke.rest:
                    for seconds in range(int(stroke.rest), 0, -1):
                        self.notify("rest", (stroke.progress, len(plan.text), seconds, remaining))
                        self.wait(1)
                        remaining = max(0, remaining - 1)
            outcome = "complete"
            self.notify("complete", "Đã gõ xong. Hãy kiểm tra nội dung trong ứng dụng đích.")
        except Cancelled:
            self.notify("stopped", self.reason)
        except Exception as error:
            outcome = "error"
            self.notify("error", str(error))
        finally:
            self.keyboard.close()
            self.notify("finished", outcome)
