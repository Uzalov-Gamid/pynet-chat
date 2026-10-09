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

def handle_client(conn, addr):
    print(f"Новое подключение: {addr}")
    username = None
    try:
        with conn.makefile("rb") as reader:
            username = receive_frame(reader)
            if not username:
                return
            clients[username] = conn
            while True:
                msg = receive_frame(reader)
                if msg is None:
                    break
                if msg.startswith("/msg "):
                    parts = msg.split(" ", 2)
                    if len(parts) < 3:
                        continue
                    target, text = parts[1], parts[2]
                    if target in clients:
                        send_frame(clients[target], f"[PM {username}]: {text}")
                else:
                    friends = users.get(username, {}).get('friends', [])
                    for friend in friends:
                        if friend in clients:
                            send_frame(clients[friend], f"[{username}]: {msg}")
    except (OSError, ValueError, UnicodeError) as error:
        print(f"Соединение {addr} закрыто: {error}")
    finally:
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
