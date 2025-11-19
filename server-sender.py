"""
WebSocket сервер для замера производительности исходящих сообщений
"""
import websockets
import asyncio
import time

from ws_utils import run_websocket_server, get_client_id
from ws_client_manager import ClientManager

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


async def send_messages(websocket: websockets.WebSocketServerProtocol, num_messages: int):
    """Отправка сообщений для бенчмарка"""
    client_id = get_client_id(websocket)
    start_time = time.time()
    
    try:
        await websocket.send(f"__BENCHMARK_START__:{num_messages}")
        
        # Отправляем N сообщений
        for i in range(num_messages):
            await websocket.send(f"__BENCHMARK_DATA__:{i}")
        
        await websocket.send(f"__BENCHMARK_END__:{num_messages}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Клиент {client_id}: соединение закрыто во время отправки")
        return
    
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


async def handle_client(websocket: websockets.WebSocketServerProtocol, path: str):
    """Обработка подключения клиента"""
    client_id = get_client_id(websocket)
    client_manager.add_client(websocket)
    
    try:
        async for message in websocket:
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
                        continue
                except (ValueError, IndexError):
                    print(f"Ошибка: не удалось распарсить количество сообщений из команды: {message}")
                    continue
                
                print(f"\n{'='*60}")
                print(f"Клиент {client_id}: Начинается отправка {num_messages} сообщений...")
                print(f"{'='*60}\n")
                
                # Запускаем отправку сообщений в отдельной задаче
                asyncio.create_task(send_messages(websocket, num_messages))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Очищаем при отключении клиента
        client_manager.remove_client(websocket)


async def main():
    # Создаем сервер на стандартном адресе
    host = "127.0.0.1"
    port = 8765
    
    # Настраиваем callbacks для менеджера клиентов
    client_manager.set_on_connect(on_client_connect)
    client_manager.set_on_disconnect(on_client_disconnect)
    
    startup_message = (
        f"WebSocket сервер запущен на ws://{host}:{port}\n"
        "Ожидание подключений для замера производительности исходящих сообщений...\n"
        "Формат команды: __BENCHMARK_START__:N (где N - количество сообщений)"
    )
    
    # Запускаем сервер
    await run_websocket_server(handle_client, host, port, startup_message)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановка сервера...")
