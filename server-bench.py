"""
WebSocket сервер для замера производительности входящих сообщений
"""
import websockets
import asyncio
import time
import argparse
from typing import Dict

from ws_utils import parse_ws_url, run_websocket_server, get_client_id
from ws_client_manager import ClientManager

# Словарь для хранения статистики бенчмарка по клиентам
benchmark_stats: Dict[websockets.WebSocketServerProtocol, dict] = {}
# Менеджер подключений
client_manager = ClientManager()


def on_client_connect(websocket: websockets.WebSocketServerProtocol):
    """Callback при подключении клиента"""
    client_id = get_client_id(websocket)
    print(f"Новый клиент подключен: {client_id}")


def on_client_disconnect(websocket: websockets.WebSocketServerProtocol):
    """Callback при отключении клиента"""
    client_id = get_client_id(websocket)
    print(f"Клиент отключен: {client_id}")
    if websocket in benchmark_stats:
        del benchmark_stats[websocket]


async def handle_client(websocket: websockets.WebSocketServerProtocol, interval: float):
    """Обработка подключения клиента"""
    client_id = get_client_id(websocket)
    client_manager.add_client(websocket)
    
    try:
        async for message in websocket:
            # Обработка меток бенчмарка
            if message == "__BENCHMARK_START__":
                # Инициализируем статистику для клиента
                benchmark_stats[websocket] = {
                    'start_time': time.time(),
                    'interval_start': time.time(),
                    'message_count': 0,
                    'interval_count': 0,
                    'interval': interval
                }
                print(f"\n{'='*60}")
                print(f"Клиент {client_id}: Выполняется замер производительности...")
                print(f"{'='*60}\n")
                continue
            elif message == "__BENCHMARK_END__":
                # Выводим финальную статистику
                if websocket in benchmark_stats:
                    stats = benchmark_stats[websocket]
                    total_time = time.time() - stats['start_time']
                    total_rate = stats['message_count'] / total_time if total_time > 0 else 0
                    
                    print(f"\n{'='*60}")
                    print(f"Клиент {client_id}: Замер завершен!")
                    print(f"Всего получено: {stats['message_count']} сообщений")
                    print(f"Общее время: {total_time:.2f} секунд")
                    print(f"Средняя скорость: {total_rate:.2f} сообщений/секунду")
                    print(f"{'='*60}\n")
                    
                    # Удаляем статистику клиента
                    del benchmark_stats[websocket]
                continue
            elif message.startswith("__BENCHMARK_DATA__"):
                # Обновляем статистику и проверяем интервалы
                if websocket in benchmark_stats:
                    stats = benchmark_stats[websocket]
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
                continue
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Очищаем статистику при отключении клиента
        client_manager.remove_client(websocket)


def create_handler(interval: float):
    """Создает обработчик с параметром interval"""
    async def handler(websocket: websockets.WebSocketServerProtocol):
        await handle_client(websocket, interval)
    return handler


async def main():
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
    url_result = parse_ws_url(args.url)
    if not url_result:
        print(f"Ошибка: неверный формат URL: {args.url}")
        print("Ожидается формат: ws://host:port")
        return
    
    host, port = url_result
    
    # Настраиваем callbacks для менеджера клиентов
    client_manager.set_on_connect(on_client_connect)
    client_manager.set_on_disconnect(on_client_disconnect)
    
    # Создаем обработчик с параметром interval
    handler = create_handler(args.interval)
    
    startup_message = (
        f"WebSocket сервер запущен на ws://{host}:{port}\n"
        "Ожидание подключений для замера производительности..."
    )
    
    # Запускаем сервер
    await run_websocket_server(handler, host, port, startup_message)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановка сервера...")
