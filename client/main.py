import socket
import threading
import sys
from datetime import datetime
from common.config import HOST, PORT, BUFFER_SIZE, ENCODING, Colors


def receive_messages(sock):
    """Поток для приема сообщений от сервера"""
    while True:
        try:
            msg = sock.recv(BUFFER_SIZE).decode(ENCODING)
            if not msg:
                print(f"\n{Colors.ERROR}Отключено от сервера.{Colors.RESET}")
                sock.close()
                sys.exit()

            # Выводим сообщение с новой строки, чтобы не ломать ввод
            timestamp = datetime.now().strftime("%H:%M")
            print(f"\n{Colors.FRIEND}[{timestamp}] {msg}{Colors.RESET}")
            print(f"{Colors.YOU}You> {Colors.RESET}", end="", flush=True)

        except Exception:
            break


def start_client():
    username = input("Введите имя пользователя: ").strip()
    if not username:
        return

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        # Сразу отправляем имя пользователя
        client.send(username.encode(ENCODING))
    except ConnectionRefusedError:
        print(f"{Colors.ERROR}Не удалось подключиться к серверу.{Colors.RESET}")
        return

    # Запускаем поток прослушки
    thread = threading.Thread(target=receive_messages,
                              args=(client,), daemon=True)
    thread.start()

    print(f"{Colors.INFO}=== GoNet Chat v2.0 ==={Colors.RESET}")
    print("Команды: /add <name>, /friends, /msg <name> <text>, /exit")

    while True:
        try:
            msg = input(f"{Colors.YOU}You> {Colors.RESET}")
            if msg == "/exit":
                break

            client.send(msg.encode(ENCODING))
        except KeyboardInterrupt:
            break

    client.close()


if __name__ == "__main__":
    start_client()
