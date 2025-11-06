import socket
import threading
import json

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
    username = conn.recv(1024).decode()
    clients[username] = conn

    while True:
        try:
            msg = conn.recv(1024).decode()
            if not msg:
                break

            if msg.startswith("/msg "):
                parts = msg.split(" ", 2)
                if len(parts) < 3:
                    continue
                target, text = parts[1], parts[2]
                if target in clients:
                    clients[target].send(f"[PM {username}]: {text}".encode())

            else:
                friends = users.get(username, {}).get('friends', [])
                for friend in friends:
                    if friend in clients:
                        clients[friend].send(f"[{username}]: {msg}".encode())

        except:
            break

    conn.close()
    del clients[username]

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
