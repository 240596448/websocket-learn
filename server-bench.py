"""
WebSocket сервер для замера производительности входящих сообщений
"""
from websocket_server import WebsocketServer
import time
import argparse
import re

# Словарь для хранения статистики бенчмарка по клиентам
benchmark_stats = {}

def new_client(client, server):
    """Вызывается когда новый клиент подключается"""
    print(f"Новый клиент подключен: {client['id']}")


def client_left(client, server):
    """Вызывается когда клиент отключается"""
    client_id = client['id']
    print(f"Клиент отключен: {client_id}")
    # Очищаем статистику бенчмарка для отключившегося клиента
    global benchmark_stats
    if client_id in benchmark_stats:
        del benchmark_stats[client_id]


def create_message_received(interval):
    """Создает функцию обработки сообщений с параметром interval"""
    def message_received(client, server, message):
        """Вызывается когда получено сообщение от клиента"""
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
                'interval': interval
            }
            print(f"\n{'='*60}")
            print(f"Клиент {client_id}: Выполняется замер производительности...")
            print(f"{'='*60}\n")
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
            return
    return message_received


if __name__ == "__main__":
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="WebSocket сервер для замера производительности входящих сообщений")
    parser.add_argument("--benchmark", action="store_true", 
                       help="Запустить режим замера производительности")
    parser.add_argument("--duration", type=float, default=10.0,
                       help="Длительность замера в секундах (по умолчанию: 10)")
    parser.add_argument("--interval", type=float, default=1.0,
                       help="Интервал для вывода статистики в секундах (по умолчанию: 1)")
    parser.add_argument("--url", type=str, default="ws://127.0.0.1:8765",
                       help="URL WebSocket сервера (по умолчанию: ws://127.0.0.1:8765)")
    
    args = parser.parse_args()
    
    # Парсим URL для извлечения host и port
    url_pattern = re.compile(r'ws://([^:]+):(\d+)')
    match = url_pattern.match(args.url)
    if not match:
        print(f"Ошибка: неверный формат URL: {args.url}")
        print("Ожидается формат: ws://host:port")
        exit(1)
    
    host = match.group(1)
    port = int(match.group(2))
    
    # Создаем сервер
    server = WebsocketServer(host=host, port=port)
    
    # Создаем функцию обработки сообщений с параметром interval
    message_handler = create_message_received(args.interval)
    
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_handler)
    
    print(f"WebSocket сервер запущен на ws://{host}:{port}")
    print("Ожидание подключений для замера производительности...")
    
    # Запускаем сервер в текущем потоке (блокирующий вызов)
    try:
        server.run_forever()
    except KeyboardInterrupt:
        print("\nОстановка сервера...")
