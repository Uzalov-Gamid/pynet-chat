import socket
import threading
import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from protocol import receive_frame, send_frame

HOST = '127.0.0.1'
PORT = 12345
DATA_FILE = 'data.json'

class Colors:
    YOU = '\033[92m'
    FRIEND = '\033[94m'
    INFO = '\033[93m'
    RESET = '\033[0m'

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        users = json.load(f)
else:
    users = {}

os.system("clear")
username = input("Введите имя пользователя: ")

if username not in users:
    users[username] = {"friends": []}
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
send_frame(client, username)
send_frame(client, "/friends " + json.dumps(users[username]["friends"], ensure_ascii=False))

chat_history = []

def print_chat():
    os.system("clear")
    print("=== GoNet Chat ===")
    print("-"*40)
    for line in chat_history[-20:]:
        print(line)
    print("-"*40)

def receive_messages():
    try:
        with client.makefile("rb") as reader:
            while True:
                msg = receive_frame(reader)
                if msg is None:
                    break
                timestamp = datetime.now().strftime("%H:%M")
                chat_history.append(f"{Colors.FRIEND}[{timestamp}] {msg}{Colors.RESET}")
                print_chat()
    except (OSError, ValueError, UnicodeError) as error:
        print(f"Соединение закрыто: {error}")


threading.Thread(target=receive_messages, daemon=True).start()

current_chat = None

def add_friend(name):
    if name not in users[username]["friends"]:
        users[username]["friends"].append(name)
        with open(DATA_FILE, 'w') as f:
            json.dump(users, f)
        send_frame(client, "/friends " + json.dumps(users[username]["friends"], ensure_ascii=False))
        chat_history.append(f"{Colors.INFO}Добавлен друг: {name}{Colors.RESET}")
        print_chat()
    else:
        chat_history.append(f"{Colors.INFO}{name} уже в друзьях{Colors.RESET}")
        print_chat()

def enter_chat(friend):
    global current_chat
    if friend in users[username]["friends"]:
        current_chat = friend
        chat_history.append(f"{Colors.INFO}=== Вошли в чат с {friend} ==={Colors.RESET}")
        print_chat()
    else:
        chat_history.append(f"{Colors.INFO}{friend} не в друзьях{Colors.RESET}")
        print_chat()

def back_chat():
    global current_chat
    if current_chat:
        chat_history.append(f"{Colors.INFO}<<< Вышли из чата с {current_chat} >>>{Colors.RESET}")
        current_chat = None
        print_chat()

def send_message(text):
    timestamp = datetime.now().strftime("%H:%M")
    if current_chat:
        send_frame(client, f"/msg {current_chat} {text}")
        chat_history.append(f"{Colors.YOU}[{timestamp}] [PM You]: {text}{Colors.RESET}")
        print_chat()
    else:
        send_frame(client, text)
        chat_history.append(f"{Colors.YOU}[{timestamp}] [PM You to all friends]: {text}{Colors.RESET}")
        print_chat()

def print_help():
    chat_history.append("Команды:")
    chat_history.append("/add <имя>      - добавить друга")
    chat_history.append("/friends        - показать друзей")
    chat_history.append("/chat <имя>     - войти в чат с другом")
    chat_history.append("/back           - выйти из чата")
    chat_history.append("/exit           - выйти из программы")
    chat_history.append("/help           - показать это сообщение")
    print_chat()

print_help()

while True:
    try:
        msg = input("You> ").strip()
        if not msg:
            continue
        if msg.startswith("/add "):
            add_friend(msg.split(" ",1)[1])
        elif msg == "/friends":
            friends = users[username]["friends"]
            chat_history.append(f"Друзья: {', '.join(friends) if friends else 'Список друзей пуст'}")
            print_chat()
        elif msg.startswith("/chat "):
            enter_chat(msg.split(" ",1)[1])
        elif msg == "/back":
            back_chat()
        elif msg == "/help":
            print_help()
        elif msg == "/exit":
            break
        else:
            send_message(msg)
    except KeyboardInterrupt:
        break

client.close()
