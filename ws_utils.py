"""
Утилиты для работы с WebSocket серверами
"""
import re
import asyncio
import websockets
from typing import Tuple, Optional


def parse_ws_url(url: str) -> Optional[Tuple[str, int]]:
    """
    Парсит WebSocket URL и возвращает (host, port)
    
    Args:
        url: URL в формате ws://host:port
        
    Returns:
        Tuple (host, port) или None если формат неверный
    """
    url_pattern = re.compile(r'ws://([^:]+):(\d+)')
    match = url_pattern.match(url)
    if not match:
        return None
    
    host = match.group(1)
    port = int(match.group(2))
    return (host, port)


async def run_websocket_server(handler, host: str, port: int, startup_message: str = None):
    """
    Запускает WebSocket сервер и ожидает бесконечно
    
    Args:
        handler: Обработчик подключений (async функция)
        host: Хост для привязки
        port: Порт для привязки
        startup_message: Сообщение для вывода при запуске
    """
    if startup_message:
        print(startup_message)
    
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # Запускаем бесконечный цикл


def get_client_id(websocket: websockets.WebSocketServerProtocol) -> int:
    """
    Возвращает ID клиента на основе объекта websocket
    
    Args:
        websocket: WebSocket соединение
        
    Returns:
        ID клиента
    """
    return id(websocket)

