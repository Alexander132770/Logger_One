from .fallback_handler import FallbackHandler
from .buffer_manager import BufferManager


class SafeLogger:
    """
    Обёртка над любым логгером — гарантирует, что ни одно сообщение не потеряется.
    """

    def __init__(self, main_logger, fallback_mode="stdout"):
        self.main_logger = main_logger
        self.fallback = FallbackHandler(mode=fallback_mode)
        self.buffer = BufferManager()

    def log(self, level: str, msg: str):
        try:
            self.main_logger.log(level, msg)
        except Exception as e:
            self.buffer.add(msg)
            self.fallback.emit(f"[MAIN LOGGER ERROR: {e}] {msg}")

    def recover(self):
        """Попытка восстановить соединение и переслать накопленные логи."""
        try:
            self.buffer.flush(lambda m: self.main_logger.log("INFO", m))
            self.fallback.emit("✅ Recovery complete — all buffered logs flushed.")
        except Exception as e:
            self.fallback.emit(f"❌ Recovery failed: {e}")
