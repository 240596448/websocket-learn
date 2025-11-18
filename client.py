#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой WebSocket клиент
"""
import websocket
import threading
import queue


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
    
    # Можно отправлять сообщения в цикле
    # for i in range(5):
    #     time.sleep(1)
    #     ws.send(f"Сообщение {i+1}")
    # ws.close()


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
    # URL WebSocket сервера
    ws_url = "ws://127.0.0.1:8765"
    
    # Очередь для сообщений из потока ввода
    message_queue = queue.Queue()
    stop_event = threading.Event()
    
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
    input_thread = threading.Thread(target=input_thread_func, args=(message_queue, stop_event), daemon=True)
    input_thread.start()
    
    # Основной цикл: проверяем очередь и отправляем сообщения
    try:
        while ws_thread.is_alive() and not stop_event.is_set():
            try:
                # Проверяем очередь с таймаутом, чтобы можно было обработать Ctrl+C
                message = message_queue.get(timeout=0.1)
                if ws.sock and ws.sock.connected:
                    ws.send(message)
                else:
                    print("Соединение не установлено, сообщение не отправлено")
            except queue.Empty:
                continue
            except KeyboardInterrupt:
                stop_event.set()
                break
    except KeyboardInterrupt:
        stop_event.set()
    
    print("\nЗакрытие соединения...")
    ws.close()

