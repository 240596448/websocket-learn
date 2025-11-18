"""
Простой WebSocket клиент
"""
import websocket
import threading
from keyboard_input import KeyboardInputHandler


def on_message(ws, message):
    """Вызывается при получении сообщения от сервера"""
    print(f"Получено от сервера: {message}")


def on_error(ws, error):
    """Вызывается при ошибке"""
    print(f"Ошибка: {error}")


def on_close(ws, close_status_code, close_msg):
    """Вызывается при закрытии соединения"""
    print("Соединение закрыто")


def on_open(ws):
    """Вызывается при открытии соединения"""
    print("Подключено к серверу!")
    
    # Отправляем тестовое сообщение
    ws.send("Привет от клиента!")
    

if __name__ == "__main__":
    # URL WebSocket сервера
    ws_url = "ws://127.0.0.1:8765"
    
    # Создаем обработчик ввода с клавиатуры
    keyboard_handler = KeyboardInputHandler()
    
    # Создаем WebSocket соединение
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Запускаем WebSocket в отдельном потоке
    ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
    ws_thread.start()
    
    print(f"Подключение к {ws_url}...")
    print("Введите сообщение и нажмите Enter для отправки. Ctrl+C для выхода.")
    
    # Запускаем поток для ввода с клавиатуры
    keyboard_handler.start()
    
    # Основной цикл: проверяем очередь и отправляем сообщения
    try:
        while ws_thread.is_alive() and not keyboard_handler.is_stopped():
            # Получаем сообщение из очереди
            message = keyboard_handler.get_message(timeout=0.1)
            if message:
                if ws.sock and ws.sock.connected:
                    ws.send(message)
                else:
                    print("Соединение не установлено, сообщение не отправлено")
    except KeyboardInterrupt:
        keyboard_handler.stop()
    
    print("\nЗакрытие соединения...")
    keyboard_handler.stop()
    ws.close()

