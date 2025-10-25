"""
Управление контекстными данными для логирования
Использует thread-local и context variables для correlation ID
Обеспечивает thread-safe и async-safe работу
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
    """
    Генерирует новый correlation ID в формате UUID
    
    Returns:
        str: UUID в формате строки
        
    Example:
        >>> cid = generate_correlation_id()
        >>> print(cid)
        'abc123-def456-...'
    """
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Устанавливает correlation ID для текущего контекста
    Если ID не указан, генерируется автоматически
    
    Args:
        correlation_id: ID или None для автогенерации
        
    Returns:
        str: Установленный correlation ID
        
    Example:
        >>> set_correlation_id("my-request-123")
        'my-request-123'
        >>> set_correlation_id()  # Автогенерация
        'a1b2c3d4-...'
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    
    # Устанавливаем в оба хранилища для совместимости
    _correlation_id_ctx.set(correlation_id)
    _thread_local.correlation_id = correlation_id
    
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Получает correlation ID из текущего контекста
    
    Returns:
        Optional[str]: Correlation ID или None если не установлен
        
    Example:
        >>> set_correlation_id("test-123")
        >>> get_correlation_id()
        'test-123'
    """
    # Пробуем context var (приоритет для async)
    cid = _correlation_id_ctx.get()
    if cid:
        return cid
    
    # Fallback на thread-local
    return getattr(_thread_local, 'correlation_id', None)


def clear_correlation_id():
    """
    Очищает correlation ID из контекста
    
    Example:
        >>> set_correlation_id("test")
        >>> clear_correlation_id()
        >>> get_correlation_id()
        None
    """
    _correlation_id_ctx.set(None)
    if hasattr(_thread_local, 'correlation_id'):
        delattr(_thread_local, 'correlation_id')


def set_transaction_id(transaction_id: str):
    """
    Устанавливает ID транзакции в контекст
    
    Args:
        transaction_id: Идентификатор транзакции
        
    Example:
        >>> set_transaction_id("tx-12345")
    """
    _transaction_id_ctx.set(transaction_id)
    _thread_local.transaction_id = transaction_id


def get_transaction_id() -> Optional[str]:
    """
    Получает ID транзакции из контекста
    
    Returns:
        Optional[str]: Transaction ID или None
        
    Example:
        >>> set_transaction_id("tx-123")
        >>> get_transaction_id()
        'tx-123'
    """
    tid = _transaction_id_ctx.get()
    if tid:
        return tid
    return getattr(_thread_local, 'transaction_id', None)


def clear_transaction_id():
    """Очищает ID транзакции из контекста"""
    _transaction_id_ctx.set(None)
    if hasattr(_thread_local, 'transaction_id'):
        delattr(_thread_local, 'transaction_id')


def set_user_id(user_id: str):
    """
    Устанавливает ID пользователя в контекст
    
    Args:
        user_id: Идентификатор пользователя
        
    Example:
        >>> set_user_id("user-789")
    """
    _user_id_ctx.set(user_id)
    _thread_local.user_id = user_id


def get_user_id() -> Optional[str]:
    """
    Получает ID пользователя из контекста
    
    Returns:
        Optional[str]: User ID или None
    """
    uid = _user_id_ctx.get()
    if uid:
        return uid
    return getattr(_thread_local, 'user_id', None)


def clear_user_id():
    """Очищает ID пользователя из контекста"""
    _user_id_ctx.set(None)
    if hasattr(_thread_local, 'user_id'):
        delattr(_thread_local, 'user_id')


def set_extra_field(key: str, value: Any):
    """
    Добавляет дополнительное поле в контекст логирования
    
    Args:
        key: Ключ поля
        value: Значение поля
        
    Example:
        >>> set_extra_field("request_method", "POST")
        >>> set_extra_field("user_agent", "Mozilla/5.0...")
    """
    extra = _extra_fields_ctx.get().copy()
    extra[key] = value
    _extra_fields_ctx.set(extra)
    
    if not hasattr(_thread_local, 'extra_fields'):
        _thread_local.extra_fields = {}
    _thread_local.extra_fields[key] = value


def get_extra_fields() -> Dict[str, Any]:
    """
    Получает все дополнительные поля из контекста
    
    Returns:
        Dict[str, Any]: Словарь дополнительных полей
        
    Example:
        >>> set_extra_field("key1", "value1")
        >>> get_extra_fields()
        {'key1': 'value1'}
    """
    ctx_extra = _extra_fields_ctx.get()
    if ctx_extra:
        return ctx_extra.copy()
    return getattr(_thread_local, 'extra_fields', {}).copy()


def clear_extra_fields():
    """Очищает все дополнительные поля из контекста"""
    _extra_fields_ctx.set({})
    if hasattr(_thread_local, 'extra_fields'):
        _thread_local.extra_fields = {}


def clear_all_context():
    """
    Очищает весь контекст логирования
    Удаляет все ID и дополнительные поля
    
    Example:
        >>> clear_all_context()
    """
    clear_correlation_id()
    clear_transaction_id()
    clear_user_id()
    clear_extra_fields()


class LoggingContext:
    """
    Контекстный менеджер для логирования с автоматической установкой контекста
    
    Attributes:
        correlation_id: ID для трассировки
        transaction_id: ID транзакции
        user_id: ID пользователя
        auto_generate_correlation: Автогенерация correlation_id если не указан
        **extra_fields: Дополнительные поля
    
    Example:
        >>> with LoggingContext(correlation_id='abc-123', component='ingest'):
        ...     logger.info('Processing transaction')
        
        >>> with LoggingContext(transaction_id='tx-456'):
        ...     # correlation_id будет сгенерирован автоматически
        ...     logger.info('Processing')
    """
    
    def __init__(
        self,
        correlation_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        user_id: Optional[str] = None,
        auto_generate_correlation: bool = True,
        **extra_fields
    ):
        """
        Инициализация контекста логирования
        
        Args:
            correlation_id: ID для трассировки
            transaction_id: ID транзакции
            user_id: ID пользователя
            auto_generate_correlation: Генерировать correlation_id если не указан
            **extra_fields: Дополнительные поля для логов
        """
        self.correlation_id = correlation_id
        self.transaction_id = transaction_id
        self.user_id = user_id
        self.auto_generate_correlation = auto_generate_correlation
        self.extra_fields = extra_fields
        
        # Сохраняем предыдущие значения для восстановления
        self.prev_correlation_id = None
        self.prev_transaction_id = None
        self.prev_user_id = None
        self.prev_extra_fields = None
    
    def __enter__(self):
        """Вход в контекст - сохраняем старые и устанавливаем новые значения"""
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
        
        # Устанавливаем дополнительные поля
        for key, value in self.extra_fields.items():
            set_extra_field(key, value)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекста - восстанавливаем предыдущие значения"""
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
        
        # Восстанавливаем дополнительные поля
        clear_extra_fields()
        for key, value in self.prev_extra_fields.items():
            set_extra_field(key, value)


def with_logging_context(**context_kwargs):
    """
    Декоратор для автоматической установки контекста логирования
    
    Args:
        **context_kwargs: Параметры для LoggingContext
        
    Returns:
        Декорированная функция с контекстом
    
    Example:
        >>> @with_logging_context(component='rules', auto_generate_correlation=True)
        ... def process_rules(transaction):
        ...     logger.info('Processing rules')
        
        >>> @with_logging_context(user_id='admin')
        ... async def admin_action():
        ...     logger.info('Admin action')
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
        
        # Возвращаем нужный wrapper в зависимости от типа функции
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


# Вспомогательные функции для работы с контекстом

def get_current_context() -> Dict[str, Any]:
    """
    Получает весь текущий контекст логирования
    
    Returns:
        Dict[str, Any]: Словарь со всеми полями контекста
        
    Example:
        >>> context = get_current_context()
        >>> print(context)
        {
            'correlation_id': 'abc-123',
            'transaction_id': 'tx-456',
            'user_id': 'user-789',
            'extra_fields': {...}
        }
    """
    return {
        'correlation_id': get_correlation_id(),
        'transaction_id': get_transaction_id(),
        'user_id': get_user_id(),
        'extra_fields': get_extra_fields()
    }


def set_context_from_dict(context: Dict[str, Any]):
    """
    Устанавливает контекст из словаря
    
    Args:
        context: Словарь с полями контекста
        
    Example:
        >>> context = {'correlation_id': 'abc', 'transaction_id': 'tx1'}
        >>> set_context_from_dict(context)
    """
    if 'correlation_id' in context and context['correlation_id']:
        set_correlation_id(context['correlation_id'])
    
    if 'transaction_id' in context and context['transaction_id']:
        set_transaction_id(context['transaction_id'])
    
    if 'user_id' in context and context['user_id']:
        set_user_id(context['user_id'])
    
    if 'extra_fields' in context and isinstance(context['extra_fields'], dict):
        for key, value in context['extra_fields'].items():
            set_extra_field(key, value)


def copy_context() -> Dict[str, Any]:
    """
    Создает копию текущего контекста для передачи в другой поток/задачу
    
    Returns:
        Dict[str, Any]: Копия контекста
        
    Example:
        >>> context = copy_context()
        >>> # В другом потоке/задаче:
        >>> set_context_from_dict(context)
    """
    return get_current_context().copy()
