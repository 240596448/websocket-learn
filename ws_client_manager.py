"""
Менеджер для управления подключениями WebSocket клиентов
"""
import websockets
from typing import Set, Callable, Optional


class ClientManager:
    """Менеджер для управления подключениями клиентов"""
    
    def __init__(self):
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.on_connect_callback: Optional[Callable[[websockets.WebSocketServerProtocol], None]] = None
        self.on_disconnect_callback: Optional[Callable[[websockets.WebSocketServerProtocol], None]] = None
    
    def add_client(self, websocket: websockets.WebSocketServerProtocol):
        """Добавляет клиента в список подключенных"""
        self.connected_clients.add(websocket)
        if self.on_connect_callback:
            self.on_connect_callback(websocket)
    
    def remove_client(self, websocket: websockets.WebSocketServerProtocol):
        """Удаляет клиента из списка подключенных"""
        self.connected_clients.discard(websocket)
        if self.on_disconnect_callback:
            self.on_disconnect_callback(websocket)
    
    def get_client_count(self) -> int:
        """Возвращает количество подключенных клиентов"""
        return len(self.connected_clients)
    
    def is_connected(self, websocket: websockets.WebSocketServerProtocol) -> bool:
        """Проверяет, подключен ли клиент"""
        return websocket in self.connected_clients
    
    def set_on_connect(self, callback: Callable[[websockets.WebSocketServerProtocol], None]):
        """Устанавливает callback при подключении клиента"""
        self.on_connect_callback = callback
    
    def set_on_disconnect(self, callback: Callable[[websockets.WebSocketServerProtocol], None]):
        """Устанавливает callback при отключении клиента"""
        self.on_disconnect_callback = callback

