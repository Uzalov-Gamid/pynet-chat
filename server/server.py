import socket
import threading
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from protocol import receive_frame, send_frame

HOST = '127.0.0.1'
PORT = 12345


try:
    with open('data.json', 'r') as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

clients = {}
clients_lock = threading.Lock()

def handle_client(conn, addr):
    print(f"Новое подключение: {addr}")
    username = None
    try:
        with conn.makefile("rb") as reader:
            username = receive_frame(reader)
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
                if msg.startswith("/msg "):
                    parts = msg.split(" ", 2)
                    if len(parts) < 3:
                        continue
                    target, text = parts[1], parts[2]
                    with clients_lock:
                        target_conn = clients.get(target)
                    if target_conn is not None:
                        send_frame(target_conn, f"[PM {username}]: {text}")
                else:
                    friends = users.get(username, {}).get('friends', [])
                    for friend in friends:
                        with clients_lock:
                            target_conn = clients.get(friend)
                        if target_conn is not None:
                            send_frame(target_conn, f"[{username}]: {msg}")
    except (OSError, ValueError, UnicodeError) as error:
        print(f"Соединение {addr} закрыто: {error}")
    finally:
        with clients_lock:
            if clients.get(username) is conn:
                clients.pop(username, None)
        conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Сервер запущен на {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()
