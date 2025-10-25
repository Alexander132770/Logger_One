import abc
import time
from typing import Any, Dict


class Metric(abc.ABC):
    """Абстрактная метрика — базовый интерфейс для всех метрик."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.timestamp = time.time()

    @abc.abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Собрать текущее значение метрики."""
        pass

    @abc.abstractmethod
    def reset(self):
        """Сбросить состояние метрики."""
        pass
