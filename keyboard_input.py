"""
Модуль для работы с вводом с клавиатуры через отдельный поток и очередь
"""
import threading
import queue


class KeyboardInputHandler:
    """Класс для обработки ввода с клавиатуры в отдельном потоке"""
    
    def __init__(self):
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.input_thread = None
    
    def _input_thread_func(self):
        """Поток для ввода сообщений с клавиатуры"""
        while not self.stop_event.is_set():
            try:
                message = input()
                if message.strip():
                    self.message_queue.put(message)
            except EOFError:
                break
            except KeyboardInterrupt:
                self.stop_event.set()
                break
    
    def start(self):
        """Запускает поток для ввода с клавиатуры"""
        if self.input_thread is None or not self.input_thread.is_alive():
            self.input_thread = threading.Thread(target=self._input_thread_func, daemon=True)
            self.input_thread.start()
    
    def stop(self):
        """Останавливает поток ввода"""
        self.stop_event.set()
    
    def get_message(self, timeout=0.1):
        """
        Получает сообщение из очереди
        
        Args:
            timeout: Таймаут в секундах для ожидания сообщения
            
        Returns:
            str или None: Сообщение из очереди или None, если очередь пуста
        """
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def is_stopped(self):
        """Проверяет, остановлен ли обработчик"""
        return self.stop_event.is_set()
