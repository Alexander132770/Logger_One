from typing import Dict, List
from .models import NotificationMessage
from .retry_policy import with_retry
from logger import StructuredLogger

logger = StructuredLogger(component="notifications.dispatcher")

class NotificationDispatcher:
    """Центральный диспетчер, управляющий каналами уведомлений."""

    def __init__(self):
        self.channels: Dict[str, List] = {
            "INFO": [],
            "WARN": [],
            "ALERT": [],
            "ERROR": [],
        }

    def register_channel(self, level: str, channel):
        if level not in self.channels:
            self.channels[level] = []
        self.channels[level].append(channel)
        logger.info(f"Channel registered for level={level}", channel=str(channel))

    @with_retry(retries=3, delay=3)
    def dispatch(self, message: NotificationMessage):
        """Рассылает уведомление всем каналам нужного уровня."""
        targets = self.channels.get(message.level, [])
        if not targets:
            logger.warn("No channels registered for level", level=message.level)
            return False
        success = True
        for ch in targets:
            ok = ch.send(message)
            success = success and ok
        return success
