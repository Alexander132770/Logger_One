from abc import ABC, abstractmethod
from .models import NotificationMessage

class BaseNotificationChannel(ABC):
    """Базовый интерфейс канала уведомлений."""

    @abstractmethod
    def send(self, message: NotificationMessage) -> bool:
        """Отправляет уведомление. Возвращает True при успехе."""
        raise NotImplementedError
