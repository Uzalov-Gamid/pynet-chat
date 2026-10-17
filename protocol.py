"""JSON string frames, separated by newlines, over a TCP byte stream."""
import argparse
import json
import threading
import weakref

MAX_FRAME_BYTES = 1024 * 1024
_send_locks = weakref.WeakKeyDictionary()
_locks_guard = threading.Lock()


def send_frame(connection, message):
    if not isinstance(message, str):
        raise TypeError("Message must be a string")
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


def connection_options(argv=None):
    parser = argparse.ArgumentParser(description="PyNet TCP chat")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=12345)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    return args
