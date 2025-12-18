import socket
import threading
from common.config import HOST, PORT, BUFFER_SIZE, ENCODING
from server.storage import add_user_if_not_exists
from server.handlers import process_command

# Хранилище активных подключений: {username: socket_conn}
active_clients = {}


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    username = None

    try:
        # Первое сообщение - это всегда имя пользователя
        username = conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
        if not username:
            return

        # Регистрируем пользователя
        active_clients[username] = conn
        add_user_if_not_exists(username)
        print(f"[LOGIN] Пользователь {username} вошел в сеть.")
        conn.send(f"Добро пожаловать, {username}!".encode(ENCODING))

        while True:
            msg = conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
            if not msg:
                break

            # Обрабатываем команду через handlers.py
            response = process_command(username, msg, active_clients)

            # Если хендлер вернул ответ (системное сообщение), шлем его обратно
            if response:
                conn.send(response.encode(ENCODING))

    except ConnectionResetError:
        pass
    finally:
        if username and username in active_clients:
            del active_clients[username]
            print(f"[LOGOUT] {username} отключился.")
        conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Сервер запущен на {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    start_server()
