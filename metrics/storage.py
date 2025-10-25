import json
import os
import threading
from typing import Dict, Any


class ReliableStorage:
    """Надёжное хранилище с резервированием на диск."""

    def __init__(self, file_path: str = "metrics/backup.json"):
        self.file_path = file_path
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def save_to_disk(self):
        with self._lock:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)

    def set(self, key: str, value: Any):
        with self._lock:
            self._data[key] = value
        self.save_to_disk()

    def get(self, key: str) -> Any:
        return self._data.get(key)
