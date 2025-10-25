import requests
from ..base import BaseNotificationChannel
from ..models import NotificationMessage
from logger import StructuredLogger

logger = StructuredLogger(component="notifications.webhook")

class WebhookChannel(BaseNotificationChannel):
    def __init__(self, url: str):
        self.url = url

    def send(self, message: NotificationMessage) -> bool:
        payload = {
            "id": message.id,
            "level": message.level,
            "title": message.title,
            "text": message.text,
            "timestamp": message.timestamp.isoformat(),
            "correlation_id": message.correlation_id,
        }
        try:
            r = requests.post(self.url, json=payload, timeout=5)
            r.raise_for_status()
            logger.info("Webhook notification sent", correlation_id=message.correlation_id)
            return True
        except Exception as e:
            logger.error("Webhook send failed", error=str(e), correlation_id=message.correlation_id)
            return False
