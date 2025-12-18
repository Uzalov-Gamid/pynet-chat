import json
import os
from common.config import DB_DIR, DB_FILE

# Путь к файлу: data/users.json
DB_PATH = os.path.join(DB_DIR, DB_FILE)

def _ensure_db_exists():
    """Создает папку и файл, если их нет"""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({}, f)

def load_data():
    _ensure_db_exists()
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_user_if_not_exists(username):
    data = load_data()
    if username not in data:
        data[username] = {"friends": []}
        save_data(data)

def add_friend(username, friend_name):
    data = load_data()
    
    if friend_name == username:
        return False, "Нельзя добавить самого себя."

    user_friends = data.get(username, {}).get("friends", [])
    
    if friend_name in user_friends:
        return False, "Этот пользователь уже в списке друзей."
    
    # Добавляем друга
    data[username]["friends"].append(friend_name)
    save_data(data)
    return True, f"Пользователь {friend_name} добавлен в друзья."

def get_friends(username):
    data = load_data()
    return data.get(username, {}).get("friends", [])
