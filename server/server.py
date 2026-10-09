import socket
import threading
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from protocol import connection_options, receive_frame, send_frame

HOST = '127.0.0.1'
PORT = 12345
HANDSHAKE_TIMEOUT = 10.0


try:
    with open('data.json', 'r') as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

clients = {}
clients_lock = threading.Lock()

def deliver(target, message):
    with clients_lock:
        connection = clients.get(target)
    if connection is None:
        return False
    try:
        send_frame(connection, message)
        return True
    except OSError:
        with clients_lock:
            if clients.get(target) is connection:
                clients.pop(target, None)
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        connection.close()
        return False


def handle_client(conn, addr):
    print(f"Новое подключение: {addr}")
    username = None
    try:
        previous_timeout = conn.gettimeout()
        conn.settimeout(HANDSHAKE_TIMEOUT)
        with conn.makefile("rb") as reader:
            username = receive_frame(reader)
            conn.settimeout(previous_timeout)
            if not username:
                return
            if len(username) > 64 or any(char.isspace() for char in username):
                send_frame(conn, "Error: invalid username")
                return
            with clients_lock:
                duplicate = username in clients
                if not duplicate:
                    clients[username] = conn
            if duplicate:
                send_frame(conn, "Error: username is already connected")
                return
            while True:
                msg = receive_frame(reader)
                if msg is None:
                    break
                if msg.startswith("/friends "):
                    friends = json.loads(msg[len("/friends "):])
                    if (not isinstance(friends, list) or len(friends) > 1000 or
                            any(not isinstance(name, str) or not name or len(name) > 64 or
                                any(char.isspace() for char in name) for name in friends)):
                        raise ValueError("Invalid friend list")
                    users.setdefault(username, {})["friends"] = list(dict.fromkeys(friends))
                    continue
                if msg.startswith("/msg "):
                    parts = msg.split(" ", 2)
                    if len(parts) < 3:
                        continue
                    target, text = parts[1], parts[2]
                    if not deliver(target, f"[PM {username}]: {text}"):
                        send_frame(conn, f"Error: recipient {target} is not connected")
                else:
                    friends = users.get(username, {}).get('friends', [])
                    for friend in friends:
                        deliver(friend, f"[{username}]: {msg}")
    except (OSError, ValueError, UnicodeError) as error:
        print(f"Соединение {addr} закрыто: {error}")
    finally:
        with clients_lock:
            if clients.get(username) is conn:
                clients.pop(username, None)
        conn.close()


def listening_socket(host, port):
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    server = socket.socket(family, socket.SOCK_STREAM)
    try:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
    except BaseException:
        server.close()
        raise
    return server


def start_server(host=HOST, port=PORT):
    server = listening_socket(host, port)
    print(f"Сервер запущен на {host}:{port}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    args = connection_options()
    start_server(args.host, args.port)
