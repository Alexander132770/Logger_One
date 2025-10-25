import requests
from ..base import BaseNotificationChannel
from ..models import NotificationMessage
from logger import StructuredLogger

logger = StructuredLogger(component="notifications.telegram")

class TelegramChannel(BaseNotificationChannel):
    def __init__(self, bot_token: str, chat_id: str):
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.chat_id = chat_id

    def send(self, message: NotificationMessage) -> bool:
        payload = {
            "chat_id": self.chat_id,
            "text": f"[{message.level}] {message.title}\n{message.text}",
            "disable_notification": message.level == "INFO"
        }
        try:
            r = requests.post(self.url, json=payload, timeout=5)
            r.raise_for_status()
            logger.info("Telegram notification sent", correlation_id=message.correlation_id, level=message.level)
            return True
        except Exception as e:
            logger.error("Telegram send failed", error=str(e), correlation_id=message.correlation_id)
            return False
