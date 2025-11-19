"""
WebSocket сервер для замера производительности исходящих сообщений
"""
from websocket_server import WebsocketServer
import time
import threading

def new_client(client, _server):
    """Вызывается когда новый клиент подключается"""
    print(f"Новый клиент подключен: {client['id']}")


def client_left(client, _server):
    """Вызывается когда клиент отключается"""
    client_id = client['id']
    print(f"Клиент отключен: {client_id}")


def message_received(client, server, message):
    """Вызывается когда получено сообщение от клиента"""
    client_id = client['id']
    
    # Обработка команды запуска замера
    if message.startswith("__BENCHMARK_START__"):
        # Парсим количество сообщений из команды
        # Формат: "__BENCHMARK_START__:N" где N - количество сообщений
        try:
            parts = message.split(":")
            if len(parts) == 2:
                num_messages = int(parts[1])
            else:
                print("Ошибка: неверный формат команды. Ожидается: __BENCHMARK_START__:N")
                return
        except (ValueError, IndexError):
            print(f"Ошибка: не удалось распарсить количество сообщений из команды: {message}")
            return
        
        print(f"\n{'='*60}")
        print(f"Клиент {client_id}: Начинается отправка {num_messages} сообщений...")
        print(f"{'='*60}\n")
        
        # Запускаем отправку сообщений в отдельном потоке, чтобы не блокировать обработку
        def send_messages():
            start_time = time.time()
            server.send_message(client, f"__BENCHMARK_START__:{num_messages}")
            
            # Отправляем N сообщений
            for i in range(num_messages):
                server.send_message(client, f"__BENCHMARK_DATA__:{i}")
            
            server.send_message(client, f"__BENCHMARK_END__")

            end_time = time.time()
            elapsed_time = end_time - start_time
            rate = num_messages / elapsed_time if elapsed_time > 0 else 0
            
            # Выводим статистику
            print(f"\n{'='*60}")
            print(f"Клиент {client_id}: Замер завершен!")
            print(f"Отправлено: {num_messages} сообщений")
            print(f"Время отправки: {elapsed_time:.4f} секунд")
            print(f"Скорость отправки: {rate:.2f} сообщений/секунду")
            print(f"{'='*60}\n")
        
        # Запускаем отправку в отдельном потоке
        thread = threading.Thread(target=send_messages)
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    # Создаем сервер на стандартном адресе
    host = "127.0.0.1"
    port = 8765
    
    server = WebsocketServer(host=host, port=port)
    
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    
    print(f"WebSocket сервер запущен на ws://{host}:{port}")
    print("Ожидание подключений для замера производительности исходящих сообщений...")
    print("Формат команды: __BENCHMARK_START__:N (где N - количество сообщений)")
    
    # Запускаем сервер в текущем потоке (блокирующий вызов)
    try:
        server.run_forever()
    except KeyboardInterrupt:
        print("\nОстановка сервера...")
