"""
Простой WebSocket клиент
"""
import websocket
import threading
import time
import argparse
from keyboard_input import KeyboardInputHandler


def on_message(ws, message):
    """Вызывается при получении сообщения от сервера"""
    # Не выводим сообщения бенчмарка, чтобы не засорять консоль
    if "__BENCHMARK_DATA__" in message:
        return
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
    

def run_benchmark(ws, duration, interval):
    """
    Запускает замер производительности: отправка сообщений в цикле
    
    Args:
        ws: WebSocket соединение
        duration: Длительность теста в секундах
        interval: Интервал для вывода статистики в секундах
    """
    print(f"\n{'='*60}")
    print("Запуск замера производительности")
    print(f"Длительность: {duration} секунд")
    print(f"Интервал статистики: {interval} секунд")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    end_time = start_time + duration
    message_count = 0
    interval_start = start_time
    interval_count = 0
    
    test_message = "__BENCHMARK_DATA__Тестовое сообщение для замера производительности"
    
    # Отправляем метку начала замера
    if ws.sock and ws.sock.connected:
        ws.send("__BENCHMARK_START__")
    
    print("Начало отправки сообщений...\n")
    
    while time.time() < end_time:
        if ws.sock and ws.sock.connected:
            try:
                ws.send(test_message)
                message_count += 1
                interval_count += 1
            except Exception as e:
                print(f"Ошибка при отправке: {e}")
                break
        else:
            print("Соединение потеряно!")
            break
        
        # Проверяем, нужно ли вывести статистику за интервал
        current_time = time.time()
        if current_time - interval_start >= interval:
            elapsed = current_time - interval_start
            rate = interval_count / elapsed if elapsed > 0 else 0
            print(f"[{current_time - start_time:.1f}с] "
                  f"Отправлено: {interval_count} сообщений за {elapsed:.1f}с "
                  f"({rate:.2f} сообщений/сек)")
            interval_start = current_time
            interval_count = 0
        
        # Небольшая задержка, чтобы не перегружать систему
        time.sleep(0.001)
    
    # Отправляем метку окончания замера
    if ws.sock and ws.sock.connected:
        ws.send("__BENCHMARK_END__")
    
    # Финальная статистика
    total_time = time.time() - start_time
    total_rate = message_count / total_time if total_time > 0 else 0
    
    print(f"\n{'='*60}")
    print("Замер завершен!")
    print(f"Всего отправлено: {message_count} сообщений")
    print(f"Общее время: {total_time:.2f} секунд")
    print(f"Средняя скорость: {total_rate:.2f} сообщений/секунду")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="WebSocket клиент с опциональным замером производительности")
    parser.add_argument("--benchmark", action="store_true", 
                       help="Запустить режим замера производительности")
    parser.add_argument("--duration", type=float, default=10.0,
                       help="Длительность замера в секундах (по умолчанию: 10)")
    parser.add_argument("--interval", type=float, default=1.0,
                       help="Интервал для вывода статистики в секундах (по умолчанию: 1)")
    parser.add_argument("--url", type=str, default="ws://127.0.0.1:8765",
                       help="URL WebSocket сервера (по умолчанию: ws://127.0.0.1:8765)")
    
    args = parser.parse_args()
    
    # URL WebSocket сервера
    ws_url = args.url
    
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
    
    # Ждем установления соединения
    connection_timeout = 5
    start_wait = time.time()
    while not (ws.sock and ws.sock.connected):
        if time.time() - start_wait > connection_timeout:
            print("Ошибка: не удалось установить соединение")
            ws.close()
            exit(1)
        time.sleep(0.1)
    
    # Если включен режим замера
    if args.benchmark:
        run_benchmark(ws, args.duration, args.interval)
        print("Закрытие соединения...")
        ws.close()
    else:
        # Обычный режим: ввод с клавиатуры
        keyboard_handler = KeyboardInputHandler()
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

