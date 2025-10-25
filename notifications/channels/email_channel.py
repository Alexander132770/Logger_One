import smtplib
from email.mime.text import MIMEText
from ..base import BaseNotificationChannel
from ..models import NotificationMessage
from logger import StructuredLogger

logger = StructuredLogger(component="notifications.email")

class EmailChannel(BaseNotificationChannel):
    def __init__(self, smtp_server: str, smtp_port: int, sender: str, password: str, recipients: list[str]):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender = sender
        self.password = password
        self.recipients = recipients

    def send(self, message: NotificationMessage) -> bool:
        msg = MIMEText(message.text)
        msg["Subject"] = f"[{message.level}] {message.title}"
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.recipients, msg.as_string())
            logger.info("Email sent", correlation_id=message.correlation_id, level=message.level)
            return True
        except Exception as e:
            logger.error("Email send failed", error=str(e), correlation_id=message.correlation_id)
            return False
