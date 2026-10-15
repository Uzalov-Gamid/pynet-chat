import json
import socket
import threading
import unittest

from protocol import MAX_FRAME_BYTES, receive_frame, send_frame


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.sender, self.receiver = socket.socketpair()
        self.sender.settimeout(2)
        self.receiver.settimeout(2)
        self.reader = self.receiver.makefile("rb")
        self.addCleanup(self.sender.close)
        self.addCleanup(self.receiver.close)
        self.addCleanup(self.reader.close)

    def test_multiple_messages_in_one_write(self):
        self.sender.sendall(b'"alice"\n"first"\n"second"\n')
        self.assertEqual([receive_frame(self.reader) for _ in range(3)],
                         ["alice", "first", "second"])

    def test_fragmented_unicode_and_embedded_newline(self):
        message = "Привет\nмир"
        frame = json.dumps(message, ensure_ascii=False).encode() + b"\n"
        def write_bytes():
            for byte in frame:
                self.sender.sendall(bytes([byte]))
        worker = threading.Thread(target=write_bytes)
        worker.start()
        self.assertEqual(receive_frame(self.reader), message)
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())

    def test_large_message(self):
        message = "я" * 5000
        worker = threading.Thread(target=send_frame, args=(self.sender, message))
        worker.start()
        self.assertEqual(receive_frame(self.reader), message)
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())

    def test_clean_disconnect(self):
        self.sender.shutdown(socket.SHUT_WR)
        self.assertIsNone(receive_frame(self.reader))

    def test_partial_disconnect(self):
        self.sender.sendall(b'"unfinished')
        self.sender.shutdown(socket.SHUT_WR)
        with self.assertRaises(ValueError):
            receive_frame(self.reader)

    def test_non_string_frame_rejected(self):
        self.sender.sendall(b'{}\n')
        with self.assertRaises(ValueError):
            receive_frame(self.reader)

    def test_server_routes_coalesced_handshake_and_private_message(self):
        from server import server
        target, target_peer = socket.socketpair()
        target_peer.settimeout(2)
        server.clients["bob"] = target
        reader = target_peer.makefile("rb")
        worker = threading.Thread(target=server.handle_client,
                                  args=(self.receiver, ("local", 0)), daemon=True)
        try:
            worker.start()
            self.sender.sendall(b'"alice"\n"/msg bob hello"\n')
            self.assertEqual(receive_frame(reader), "[PM alice]: hello")
        finally:
            self.sender.shutdown(socket.SHUT_WR)
            worker.join(timeout=2)
            server.clients.pop("bob", None)
            reader.close()
            target.close()
            target_peer.close()
        self.assertFalse(worker.is_alive())
        self.assertNotIn("alice", server.clients)

    def test_duplicate_username_does_not_replace_connected_user(self):
        from server import server
        original, peer = socket.socketpair()
        server.clients["alice"] = original
        worker = threading.Thread(target=server.handle_client,
                                  args=(self.receiver, ("local", 0)), daemon=True)
        reader = self.sender.makefile("rb")
        try:
            worker.start()
            send_frame(self.sender, "alice")
            self.assertIn("already connected", receive_frame(reader))
            worker.join(timeout=2)
            self.assertIs(server.clients["alice"], original)
        finally:
            server.clients.pop("alice", None)
            reader.close()
            original.close()
            peer.close()
        self.assertFalse(worker.is_alive())

    def test_friend_update_takes_effect_without_server_restart(self):
        from server import server
        target, target_peer = socket.socketpair()
        target_peer.settimeout(2)
        server.clients["bob"] = target
        reader = target_peer.makefile("rb")
        worker = threading.Thread(target=server.handle_client,
                                  args=(self.receiver, ("local", 0)), daemon=True)
        try:
            worker.start()
            send_frame(self.sender, "alice")
            send_frame(self.sender, '/friends ["bob"]')
            send_frame(self.sender, "hello friends")
            self.assertEqual(receive_frame(reader), "[alice]: hello friends")
        finally:
            self.sender.shutdown(socket.SHUT_WR)
            worker.join(timeout=2)
            server.clients.pop("bob", None)
            server.users.pop("alice", None)
            reader.close()
            target.close()
            target_peer.close()
        self.assertFalse(worker.is_alive())

    def test_concurrent_senders_preserve_large_frames(self):
        messages = ["a" * 10000, "б" * 10000]
        errors = []
        def write(message):
            try:
                for _ in range(5):
                    send_frame(self.sender, message)
            except Exception as error:
                errors.append(error)
        workers = [threading.Thread(target=write, args=(message,)) for message in messages]
        for worker in workers:
            worker.start()
        received = [receive_frame(self.reader) for _ in range(10)]
        for worker in workers:
            worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertCountEqual(received, messages * 5)

    def test_oversized_send_rejected(self):
        with self.assertRaises(ValueError):
            send_frame(self.sender, "x" * MAX_FRAME_BYTES)


if __name__ == "__main__":
    unittest.main()
