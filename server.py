"""
Простой WebSocket сервер
"""
from websocket_server import WebsocketServer
import threading
from keyboard_input import KeyboardInputHandler


def new_client(client, server):
    """Вызывается когда новый клиент подключается"""
    print(f"Новый клиент подключен: {client['id']}")
    server.send_message_to_all("Новый клиент подключился!")


def client_left(client, server):
    """Вызывается когда клиент отключается"""
    print(f"Клиент отключен: {client['id']}")


def message_received(client, server, message):
    """Вызывается когда получено сообщение от клиента"""
    # Исправляем декодирование: если сообщение пришло как неправильно декодированная строка
    if isinstance(message, bytes):
        # Если сообщение пришло как bytes, декодируем как UTF-8
        message = message.decode('utf-8')
    elif isinstance(message, str):
        # Если это неправильно декодированная строка (UTF-8 байты, прочитанные как Latin-1)
        # Преобразуем обратно в байты (Latin-1 сохраняет все байты 1:1) и декодируем как UTF-8
        try:
            message = message.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass  # Если не получилось, оставляем как есть
    
    print(f"Клиент {client['id']} отправил: {message}")
    # Отправляем ответ обратно клиенту
    server.send_message(client, f"Сервер получил: {message}")
    # Или отправляем всем
    # server.send_message_to_all(f"Клиент {client['id']} сказал: {message}")


if __name__ == "__main__":
    PORT = 8765
    server = WebsocketServer(host="127.0.0.1", port=PORT)
    
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    
    # Создаем обработчик ввода с клавиатуры
    keyboard_handler = KeyboardInputHandler()
    
    print(f"WebSocket сервер запущен на ws://127.0.0.1:{PORT}")
    print("Введите сообщение и нажмите Enter для отправки всем клиентам. Ctrl+C для остановки.")
    
    # Запускаем поток для ввода с клавиатуры
    keyboard_handler.start()
    
    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=server.run_forever, daemon=True)
    server_thread.start()
    
    # Основной цикл: проверяем очередь и отправляем сообщения всем клиентам
    try:
        while server_thread.is_alive() and not keyboard_handler.is_stopped():
            # Получаем сообщение из очереди
            message = keyboard_handler.get_message(timeout=0.1)
            if message:
                server.send_message_to_all(f"[Сервер]: {message}")
    except KeyboardInterrupt:
        keyboard_handler.stop()
    
    print("\nОстановка сервера...")
    keyboard_handler.stop()
