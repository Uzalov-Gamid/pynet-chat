from server.storage import add_friend, get_friends


def process_command(username, message, active_clients):
    """
    Разбирает сообщение от клиента и возвращает ответ.
    message: текст сообщения (например "/add bob" или "Привет")
    active_clients: словарь {username: socket}
    """

    # Команда: Добавить друга
    if message.startswith("/add "):
        parts = message.split(" ", 1)
        if len(parts) < 2:
            return "Server: Укажите имя друга."
        friend_name = parts[1].strip()
        success, response = add_friend(username, friend_name)
        return f"Server: {response}"

    # Команда: Список друзей
    elif message == "/friends":
        friends = get_friends(username)
        if not friends:
            return "Server: Список друзей пуст."
        return f"Server: Ваши друзья: {', '.join(friends)}"

    # Команда: Личное сообщение (/msg friend text)
    elif message.startswith("/msg "):
        parts = message.split(" ", 2)
        if len(parts) < 3:
            return "Server: Формат /msg <имя> <текст>"

        target_user = parts[1]
        text = parts[2]

        # Проверка, в друзьях ли этот человек (безопасность)
        my_friends = get_friends(username)
        if target_user not in my_friends:
            return f"Server: Пользователь {target_user} не в ваших друзьях."

        # Отправка
        if target_user in active_clients:
            try:
                target_socket = active_clients[target_user]
                # Отправляем получателю
                target_socket.send(f"[PM {username}]: {text}".encode('utf-8'))
                return None  # Не отправляем ответ отправителю, он сам отобразит у себя
            except:
                return f"Server: Ошибка отправки пользователю {target_user}."
        else:
            return f"Server: Пользователь {target_user} сейчас офлайн."

    # Обычное сообщение (рассылка всем друзьям, кто онлайн)
    else:
        friends = get_friends(username)
        count = 0
        for friend in friends:
            if friend in active_clients:
                try:
                    active_clients[friend].send(
                        f"[{username}]: {message}".encode('utf-8'))
                    count += 1
                except:
                    pass
        return None  # Нет системного ответа
