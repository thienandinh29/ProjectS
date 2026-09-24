"""Thread-serialized wrapper for the independent upstream UniKey engine."""
from pathlib import Path
import ctypes
import threading

_LOCK = threading.RLock()
_LIB = None

class Oracle:
    def __init__(self, modern=False):
        global _LIB
        with _LOCK:
            if _LIB is None:
                _LIB = ctypes.CDLL(str(Path(__file__).with_name("unikey_oracle.dll")))
                _LIB.oracle_init.argtypes = [ctypes.c_int]
                _LIB.oracle_init.restype = None
                _LIB.oracle_reset.argtypes = []
                _LIB.oracle_reset.restype = None
                _LIB.oracle_key.argtypes = [ctypes.c_uint, ctypes.POINTER(ctypes.c_int), ctypes.c_void_p, ctypes.c_int]
                _LIB.oracle_key.restype = ctypes.c_int
        self.modern = modern

    def render(self, keys: str, prefix="") -> str:
        with _LOCK:
            _LIB.oracle_init(int(self.modern))
            output = prefix
            for key in keys:
                if key == "\n":
                    _LIB.oracle_reset()
                    output += "\n"
                    continue
                backs = ctypes.c_int()
                buf = ctypes.create_string_buffer(4096)
                size = _LIB.oracle_key(ord(key), ctypes.byref(backs), buf, len(buf))
                if size < 0:
                    raise ValueError("UniKey output buffer exceeded")
                if key == "\b" and backs.value == 0 and size == 0:
                    backs.value = 1
                if backs.value:
                    if len(output) - backs.value < len(prefix):
                        raise ValueError("Sequence would delete text before its insertion point")
                    output = output[:-backs.value]
                if size:
                    output += buf.raw[:size].decode("utf-8")
                elif key != "\b" and backs.value == 0:
                    output += key
            return output
