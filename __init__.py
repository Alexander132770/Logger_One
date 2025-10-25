"""
Logging System for Fraud Detection Service

Надежная система структурированного логирования с поддержкой:
- Correlation ID для трассировки
- Специализированные логгеры для разных доменов
- Интеграция с системами мониторинга
- Автоматический аудит
"""

__version__ = "1.0.0"
__author__ = "Alexander132770"

from .config import setup_logging, LOGGING_CONFIG, LOGGING_CONFIG_DEV
from .context import (
    LoggingContext,
    set_correlation_id,
    get_correlation_id,
    clear_correlation_id,
    set_transaction_id,
    get_transaction_id,
    clear_transaction_id,
    set_user_id,
    get_user_id,
    clear_user_id,
    set_extra_field,
    get_extra_fields,
    clear_extra_fields,
    clear_all_context,
    with_logging_context,
    generate_correlation_id
)
from .helpers import (
    StructuredLogger,
    LogEvent,
    TransactionLogger,
    RuleLogger,
    NotificationLogger,
    AuditLogger,
    MetricsLogger,
    transaction_logger,
    rule_logger,
    notification_logger,
    audit_logger,
    metrics_logger,
    log_execution_time,
    log_method_call
)

# Экспортируем основные компоненты
__all__ = [
    # Конфигурация
    'setup_logging',
    'LOGGING_CONFIG',
    'LOGGING_CONFIG_DEV',
    
    # Контекст
    'LoggingContext',
    'set_correlation_id',
    'get_correlation_id',
    'clear_correlation_id',
    'set_transaction_id',
    'get_transaction_id',
    'clear_transaction_id',
    'set_user_id',
    'get_user_id',
    'clear_user_id',
    'set_extra_field',
    'get_extra_fields',
    'clear_extra_fields',
    'clear_all_context',
    'with_logging_context',
    'generate_correlation_id',
    
    # Логгеры и события
    'StructuredLogger',
    'LogEvent',
    'TransactionLogger',
    'RuleLogger',
    'NotificationLogger',
    'AuditLogger',
    'MetricsLogger',
    
    # Глобальные экземпляры логгеров
    'transaction_logger',
    'rule_logger',
    'notification_logger',
    'audit_logger',
    'metrics_logger',
    
    # Декораторы
    'log_execution_time',
    'log_method_call',
]


# Удобные функции для быстрого старта
def quick_setup(environment='production', log_dir='./logs'):
    """
    Быстрая настройка системы логирования
    
    Args:
        environment: 'production' или 'development'
        log_dir: Директория для хранения логов
        
    Example:
        >>> from logging_system import quick_setup
        >>> quick_setup('development')
    """
    import os
    os.environ['LOG_DIR'] = log_dir
    setup_logging(environment)
    
    # Возвращаем основные логгеры для удобства
    return {
        'transaction': transaction_logger,
        'rule': rule_logger,
        'notification': notification_logger,
        'audit': audit_logger,
        'metrics': metrics_logger
    }


def create_logger(name, component):
    """
    Создает новый структурированный логгер
    
    Args:
        name: Имя логгера
        component: Название компонента
        
    Returns:
        StructuredLogger: Настроенный логгер
        
    Example:
        >>> from logging_system import create_logger
        >>> logger = create_logger('my_service', 'api')
        >>> logger.info("Service started")
    """
    return StructuredLogger(name, component)


# Информация о версии и статусе
def get_version_info():
    """Возвращает информацию о версии системы"""
    return {
        'version': __version__,
        'author': __author__,
        'python_requires': '>=3.8',
        'status': 'production-ready'
    }


# Предупреждение при импорте в development режиме
import os
import warnings

if os.getenv('ENVIRONMENT') == 'development':
    warnings.filterwarnings('default', category=DeprecationWarning)
