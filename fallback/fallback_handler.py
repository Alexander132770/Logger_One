import sys
import os
import time
import threading
from queue import Queue, Empty


class FallbackHandler:
    """
    Надёжный резервный обработчик логов.
    Перехватывает ошибки основной системы логирования и сохраняет записи
    в безопасное место — stdout или резервный файл.
    """

    def __init__(self, mode="stdout", backup_file="fallback.log", flush_interval=5):
        self.mode = mode
        self.backup_file = backup_file
        self.queue = Queue()
        self._stop_event = threading.Event()
        self.flush_interval = flush_interval
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def emit(self, record: str):
        """Добавить сообщение в очередь."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.queue.put(f"[{timestamp}] {record}")

    def _worker(self):
        """Фоновый поток для безопасной записи."""
        while not self._stop_event.is_set():
            try:
                message = self.queue.get(timeout=self.flush_interval)
                self._write(message)
            except Empty:
                continue
            except Exception as e:
                sys.stderr.write(f"[FALLBACK ERROR] {e}\n")

    def _write(self, msg):
        if self.mode == "stdout":
            print(msg, flush=True)
        else:
            os.makedirs(os.path.dirname(self.backup_file), exist_ok=True)
            with open(self.backup_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")

    def stop(self):
        """Безопасное завершение."""
        self._stop_event.set()
        self._thread.join(timeout=2)
        while not self.queue.empty():
            self._write(self.queue.get())
