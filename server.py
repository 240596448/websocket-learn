#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой WebSocket сервер
"""
from websocket_server import WebsocketServer
import threading
import queue


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


def input_thread_func(message_queue, stop_event):
    """Поток для ввода сообщений с клавиатуры"""
    while not stop_event.is_set():
        try:
            message = input()
            if message.strip():
                message_queue.put(message)
        except EOFError:
            break
        except KeyboardInterrupt:
            stop_event.set()
            break


if __name__ == "__main__":
    PORT = 8765
    server = WebsocketServer(host="127.0.0.1", port=PORT)
    
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    
    # Очередь для сообщений из потока ввода
    message_queue = queue.Queue()
    stop_event = threading.Event()
    
    print(f"WebSocket сервер запущен на ws://127.0.0.1:{PORT}")
    print("Введите сообщение и нажмите Enter для отправки всем клиентам. Ctrl+C для остановки.")
    
    # Запускаем поток для ввода с клавиатуры
    input_thread = threading.Thread(target=input_thread_func, args=(message_queue, stop_event), daemon=True)
    input_thread.start()
    
    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=server.run_forever, daemon=True)
    server_thread.start()
    
    # Основной цикл: проверяем очередь и отправляем сообщения всем клиентам
    try:
        while server_thread.is_alive() and not stop_event.is_set():
            try:
                # Проверяем очередь с таймаутом, чтобы можно было обработать Ctrl+C
                message = message_queue.get(timeout=0.1)
                server.send_message_to_all(f"[Сервер]: {message}")
            except queue.Empty:
                continue
            except KeyboardInterrupt:
                stop_event.set()
                break
    except KeyboardInterrupt:
        stop_event.set()
    
    print("\nОстановка сервера...")

