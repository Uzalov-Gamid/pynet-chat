"""JSON string frames, separated by newlines, over a TCP byte stream."""
import json
import threading
import weakref

MAX_FRAME_BYTES = 1024 * 1024
_send_locks = weakref.WeakKeyDictionary()
_locks_guard = threading.Lock()


def send_frame(connection, message):
    frame = json.dumps(message, ensure_ascii=False).encode("utf-8") + b"\n"
    if len(frame) > MAX_FRAME_BYTES:
        raise ValueError("Message exceeds frame size limit")
    with _locks_guard:
        lock = _send_locks.setdefault(connection, threading.Lock())
    with lock:
        connection.sendall(frame)


def receive_frame(reader):
    frame = reader.readline(MAX_FRAME_BYTES + 1)
    if not frame:
        return None
    if len(frame) > MAX_FRAME_BYTES or not frame.endswith(b"\n"):
        raise ValueError("Oversized or incomplete message frame")
    message = json.loads(frame.decode("utf-8"))
    if not isinstance(message, str):
        raise ValueError("Message must be a string")
    return message
