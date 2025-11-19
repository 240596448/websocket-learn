"""
Простой WebSocket сервер
"""
from websocket_server import WebsocketServer
import threading
import time
from keyboard_input import KeyboardInputHandler

# Словарь для хранения статистики бенчмарка по клиентам
benchmark_stats = {}

def new_client(client, server):
    """Вызывается когда новый клиент подключается"""
    print(f"Новый клиент подключен: {client['id']}")
    server.send_message_to_all("Новый клиент подключился!")


def client_left(client, server):
    """Вызывается когда клиент отключается"""
    client_id = client['id']
    print(f"Клиент отключен: {client_id}")
    # Очищаем статистику бенчмарка для отключившегося клиента
    global benchmark_stats
    if client_id in benchmark_stats:
        del benchmark_stats[client_id]


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
    
    global benchmark_stats
    client_id = client['id']
    
    # Обработка меток бенчмарка
    if message == "__BENCHMARK_START__":
        # Инициализируем статистику для клиента
        benchmark_stats[client_id] = {
            'start_time': time.time(),
            'interval_start': time.time(),
            'message_count': 0,
            'interval_count': 0,
            'interval': 1.0  # Интервал статистики по умолчанию 1 секунда
        }
        print(f"\n{'='*60}")
        print(f"Клиент {client_id}: Выполняется замер производительности...")
        print(f"{'='*60}\n")
        server.send_message(client, f"Сервер получил: {message}")
        return
    elif message == "__BENCHMARK_END__":
        # Выводим финальную статистику
        if client_id in benchmark_stats:
            stats = benchmark_stats[client_id]
            total_time = time.time() - stats['start_time']
            total_rate = stats['message_count'] / total_time if total_time > 0 else 0
            
            print(f"\n{'='*60}")
            print(f"Клиент {client_id}: Замер завершен!")
            print(f"Всего получено: {stats['message_count']} сообщений")
            print(f"Общее время: {total_time:.2f} секунд")
            print(f"Средняя скорость: {total_rate:.2f} сообщений/секунду")
            print(f"{'='*60}\n")
            
            # Удаляем статистику клиента
            del benchmark_stats[client_id]
        
        server.send_message(client, f"Сервер получил: {message}")
        return
    elif message.startswith("__BENCHMARK_DATA__"):
        # Обновляем статистику и проверяем интервалы
        if client_id in benchmark_stats:
            stats = benchmark_stats[client_id]
            stats['message_count'] += 1
            stats['interval_count'] += 1
            
            # Проверяем, нужно ли вывести статистику за интервал
            current_time = time.time()
            if current_time - stats['interval_start'] >= stats['interval']:
                elapsed = current_time - stats['interval_start']
                rate = stats['interval_count'] / elapsed if elapsed > 0 else 0
                total_elapsed = current_time - stats['start_time']
                print(f"[Сервер] Клиент {client_id} [{total_elapsed:.1f}с] "
                      f"Получено: {stats['interval_count']} сообщений за {elapsed:.1f}с "
                      f"({rate:.2f} сообщений/сек)")
                stats['interval_start'] = current_time
                stats['interval_count'] = 0
        
        # Сообщения бенчмарка не выводим в консоль, только обрабатываем
        server.send_message(client, f"Сервер получил: {message}")
        return
    
    # Обычные сообщения выводим в консоль
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
