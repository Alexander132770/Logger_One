import threading


class BufferManager:
    """
    Хранит последние N логов в памяти.
    При восстановлении соединения с основным логгером — пересылает их.
    """

    def __init__(self, capacity=500):
        self.capacity = capacity
        self.buffer = []
        self.lock = threading.Lock()

    def add(self, message):
        with self.lock:
            self.buffer.append(message)
            if len(self.buffer) > self.capacity:
                self.buffer.pop(0)

    def flush(self, target_callback):
        """Отправить накопленные логи в основной логгер."""
        with self.lock:
            for msg in list(self.buffer):
                try:
                    target_callback(msg)
                except Exception:
                    break
            self.buffer.clear()
