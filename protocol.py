"""JSON string frames, separated by newlines, over a TCP byte stream."""
import json

MAX_FRAME_BYTES = 1024 * 1024


def send_frame(connection, message):
    frame = json.dumps(message, ensure_ascii=False).encode("utf-8") + b"\n"
    if len(frame) > MAX_FRAME_BYTES:
        raise ValueError("Message exceeds frame size limit")
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
