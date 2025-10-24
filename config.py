"""
Управление контекстными данными для логирования
Использует thread-local и context variables для correlation ID
"""

import threading
import uuid
from contextvars import ContextVar
from typing import Optional, Dict, Any
from functools import wraps

# Context variables для async/await
_correlation_id_ctx: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
_transaction_id_ctx: ContextVar[Optional[str]] = ContextVar('transaction_id', default=None)
_user_id_ctx: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_extra_fields_ctx: ContextVar[Dict[str, Any]] = ContextVar('extra_fields', default={})

# Thread-local для синхронного кода
_thread_local = threading.local()


def generate_correlation_id() -> str:
    """Генерирует новый correlation ID"""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Устанавливает correlation ID для текущего контекста
    
    Args:
        correlation_id: ID или None для автогенерации
        
    Returns:
        Установленный correlation ID
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    
    # Устанавливаем в оба хранилища
    _correlation_id_ctx.set(correlation_id)
    _thread_local.correlation_id = correlation_id
    
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Получает correlation ID из текущего контекста"""
    # Пробуем context var (приоритет для async)
    cid = _correlation_id_ctx.get()
    if cid:
        return cid
    
    # Fallback на thread-local
    return getattr(_thread_local, 'correlation_id', None)


def clear_correlation_id():
    """Очищает correlation ID"""
    _correlation_id_ctx.set(None)
    if hasattr(_thread_local, 'correlation_id'):
        delattr(_thread_local, 'correlation_id')


def set_transaction_id(transaction_id: str):
    """Устанавливает ID транзакции"""
    _transaction_id_ctx.set(transaction_id)
    _thread_local.transaction_id = transaction_id


def get_transaction_id() -> Optional[str]:
    """Получает ID транзакции"""
    tid = _transaction_id_ctx.get()
    if tid:
        return tid
    return getattr(_thread_local, 'transaction_id', None)


def clear_transaction_id():
    """Очищает ID транзакции"""
    _transaction_id_ctx.set(None)
    if hasattr(_thread_local, 'transaction_id'):
        delattr(_thread_local, 'transaction_id')


def set_user_id(user_id: str):
    """Устанавливает ID пользователя"""
    _user_id_ctx.set(user_id)
    _thread_local.user_id = user_id


def get_user_id() -> Optional[str]:
    """Получает ID пользователя"""
    uid = _user_id_ctx.get()
    if uid:
        return uid
    return getattr(_thread_local, 'user_id', None)


def clear_user_id():
    """Очищает ID пользователя"""
    _user_id_ctx.set(None)
    if hasattr(_thread_local, 'user_id'):
        delattr(_thread_local, 'user_id')


def set_extra_field(key: str, value: Any):
    """Добавляет дополнительное поле в контекст логирования"""
    extra = _extra_fields_ctx.get().copy()
    extra[key] = value
    _extra_fields_ctx.set(extra)
    
    if not hasattr(_thread_local, 'extra_fields'):
        _thread_local.extra_fields = {}
    _thread_local.extra_fields[key] = value


def get_extra_fields() -> Dict[str, Any]:
    """Получает все дополнительные поля"""
    ctx_extra = _extra_fields_ctx.get()
    if ctx_extra:
        return ctx_extra.copy()
    return getattr(_thread_local, 'extra_fields', {}).copy()


def clear_extra_fields():
    """Очищает дополнительные поля"""
    _extra_fields_ctx.set({})
    if hasattr(_thread_local, 'extra_fields'):
        _thread_local.extra_fields = {}


def clear_all_context():
    """Очищает весь контекст логирования"""
    clear_correlation_id()
    clear_transaction_id()
    clear_user_id()
    clear_extra_fields()


class LoggingContext:
    """
    Контекстный менеджер для логирования с автоматической установкой контекста
    
    Usage:
        with LoggingContext(correlation_id='abc-123', component='ingest'):
            # Все логи внутри будут иметь correlation_id и component
            logger.info('Processing transaction')
    """
    
    def __init__(
        self,
        correlation_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        user_id: Optional[str] = None,
        auto_generate_correlation: bool = True,
        **extra_fields
    ):
        self.correlation_id = correlation_id
        self.transaction_id = transaction_id
        self.user_id = user_id
        self.auto_generate_correlation = auto_generate_correlation
        self.extra_fields = extra_fields
        
        # Сохраняем предыдущие значения
        self.prev_correlation_id = None
        self.prev_transaction_id = None
        self.prev_user_id = None
        self.prev_extra_fields = None
    
    def __enter__(self):
        # Сохраняем текущие значения
        self.prev_correlation_id = get_correlation_id()
        self.prev_transaction_id = get_transaction_id()
        self.prev_user_id = get_user_id()
        self.prev_extra_fields = get_extra_fields()
        
        # Устанавливаем новые значения
        if self.correlation_id or self.auto_generate_correlation:
            set_correlation_id(self.correlation_id)
        
        if self.transaction_id:
            set_transaction_id(self.transaction_id)
        
        if self.user_id:
            set_user_id(self.user_id)
        
        for key, value in self.extra_fields.items():
            set_extra_field(key, value)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Восстанавливаем предыдущие значения
        if self.prev_correlation_id:
            set_correlation_id(self.prev_correlation_id)
        else:
            clear_correlation_id()
        
        if self.prev_transaction_id:
            set_transaction_id(self.prev_transaction_id)
        else:
            clear_transaction_id()
        
        if self.prev_user_id:
            set_user_id(self.prev_user_id)
        else:
            clear_user_id()
        
        clear_extra_fields()
        for key, value in self.prev_extra_fields.items():
            set_extra_field(key, value)


def with_logging_context(**context_kwargs):
    """
    Декоратор для автоматической установки контекста логирования
    
    Usage:
        @with_logging_context(component='rules', auto_generate_correlation=True)
        def process_rules(transaction):
            logger.info('Processing rules')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with LoggingContext(**context_kwargs):
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with LoggingContext(**context_kwargs):
                return await func(*args, **kwargs)
        
        # Возвращаем нужный wrapper
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x100:  # CO_COROUTINE
            return async_wrapper
        return wrapper
    
    return decorator
