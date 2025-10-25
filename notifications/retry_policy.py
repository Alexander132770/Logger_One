import time
import functools
from logger import StructuredLogger

logger = StructuredLogger(component="notifications.retry")

def with_retry(retries=3, delay=2):
    """Декоратор для повторных попыток отправки уведомлений."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, retries + 1):
                success = func(*args, **kwargs)
                if success:
                    return True
                logger.warn("Retrying notification", attempt=attempt)
                time.sleep(delay)
            logger.error("Notification failed after retries")
            return False
        return wrapper
    return decorator
