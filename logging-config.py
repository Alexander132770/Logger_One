"""
Централизованная конфигурация системы логирования
Поддерживает структурированное JSON-логирование с корреляционными ID
"""

import logging
import logging.config
import json
from typing import Any, Dict
from datetime import datetime
import sys
import os
from pathlib import Path

# Директории для логов
LOG_DIR = Path(os.getenv('LOG_DIR', './logs'))
LOG_DIR.mkdir(exist_ok=True)

class StructuredFormatter(logging.Formatter):
    """
    Форматтер для структурированного JSON-логирования
    Добавляет метаданные и контекстную информацию
    """
    
    def __init__(self, service_name: str = "fraud-detection"):
        super().__init__()
        self.service_name = service_name
        self.hostname = os.getenv('HOSTNAME', 'localhost')
        
    def format(self, record: logging.LogRecord) -> str:
        """Преобразует запись лога в JSON"""
        
        # Базовая структура
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'component': getattr(record, 'component', 'unknown'),
            'message': record.getMessage(),
            'service': self.service_name,
            'hostname': self.hostname,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # Добавляем correlation_id если есть
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
            
        # Добавляем transaction_id если есть
        if hasattr(record, 'transaction_id'):
            log_data['transaction_id'] = record.transaction_id
            
        # Добавляем user_id если есть
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
            
        # Добавляем дополнительные поля
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
            
        # Информация о местоположении в коде
        log_data['location'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName,
            'module': record.module
        }
        
        # Добавляем исключение если есть
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        # Добавляем stack_info если есть
        if record.stack_info:
            log_data['stack_info'] = record.stack_info
            
        return json.dumps(log_data, ensure_ascii=False, default=str)


class CorrelationFilter(logging.Filter):
    """
    Фильтр для добавления correlation_id в каждую запись лога
    Использует thread-local storage
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        from .context import get_correlation_id, get_transaction_id
        
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = get_correlation_id()
            
        if not hasattr(record, 'transaction_id'):
            record.transaction_id = get_transaction_id()
            
        return True


class ComponentFilter(logging.Filter):
    """
    Фильтр для добавления имени компонента
    """
    
    def __init__(self, component: str):
        super().__init__()
        self.component = component
        
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'component'):
            record.component = self.component
        return True


# Конфигурация логирования
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'json': {
            '()': StructuredFormatter,
            'service_name': 'fraud-detection-service'
        },
        'simple': {
            'format': '%(asctime)s [%(levelname)s] %(component)s - %(message)s [%(correlation_id)s]',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] [%(correlation_id)s] %(component)s.%(name)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    
    'filters': {
        'correlation': {
            '()': CorrelationFilter
        }
    },
    
    'handlers': {
        # Консоль - JSON для production
        'console_json': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filters': ['correlation'],
            'stream': sys.stdout
        },
        
        # Консоль - читаемый формат для development
        'console_simple': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filters': ['correlation'],
            'stream': sys.stdout
        },
        
        # Основной файл логов - JSON
        'file_json': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filters': ['correlation'],
            'filename': str(LOG_DIR / 'application.json.log'),
            'maxBytes': 100 * 1024 * 1024,  # 100MB
            'backupCount': 10,
            'encoding': 'utf-8'
        },
        
        # Файл ошибок
        'file_errors': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json',
            'filters': ['correlation'],
            'filename': str(LOG_DIR / 'errors.json.log'),
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 20,
            'encoding': 'utf-8'
        },
        
        # Файл для транзакций
        'file_transactions': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filters': ['correlation'],
            'filename': str(LOG_DIR / 'transactions.json.log'),
            'maxBytes': 200 * 1024 * 1024,  # 200MB
            'backupCount': 30,
            'encoding': 'utf-8'
        },
        
        # Файл для правил
        'file_rules': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filters': ['correlation'],
            'filename': str(LOG_DIR / 'rules.json.log'),
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 10,
            'encoding': 'utf-8'
        },
        
        # Файл для уведомлений
        'file_notifications': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filters': ['correlation'],
            'filename': str(LOG_DIR / 'notifications.json.log'),
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 10,
            'encoding': 'utf-8'
        },
        
        # Файл для аудита
        'file_audit': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': str(LOG_DIR / 'audit.json.log'),
            'maxBytes': 100 * 1024 * 1024,  # 100MB
            'backupCount': 50,  # Долгое хранение для аудита
            'encoding': 'utf-8'
        },
        
        # Файл для метрик
        'file_metrics': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': str(LOG_DIR / 'metrics.json.log'),
            'maxBytes': 100 * 1024 * 1024,  # 100MB
            'backupCount': 15,
            'encoding': 'utf-8'
        }
    },
    
    'loggers': {
        # Основной логгер приложения
        '': {
            'level': 'INFO',
            'handlers': ['console_json', 'file_json', 'file_errors'],
            'propagate': False
        },
        
        # Логгер для транзакций
        'transactions': {
            'level': 'INFO',
            'handlers': ['file_transactions', 'console_json'],
            'propagate': False
        },
        
        # Логгер для правил
        'rules': {
            'level': 'INFO',
            'handlers': ['file_rules', 'console_json'],
            'propagate': False
        },
        
        # Логгер для уведомлений
        'notifications': {
            'level': 'INFO',
            'handlers': ['file_notifications', 'console_json'],
            'propagate': False
        },
        
        # Логгер для аудита
        'audit': {
            'level': 'INFO',
            'handlers': ['file_audit'],
            'propagate': False
        },
        
        # Логгер для метрик
        'metrics': {
            'level': 'INFO',
            'handlers': ['file_metrics'],
            'propagate': False
        },
        
        # Внешние библиотеки - снижаем уровень
        'urllib3': {
            'level': 'WARNING'
        },
        'sqlalchemy': {
            'level': 'WARNING'
        }
    }
}

# Development конфигурация (более читаемая)
LOGGING_CONFIG_DEV = LOGGING_CONFIG.copy()
LOGGING_CONFIG_DEV['loggers']['']['handlers'] = ['console_simple', 'file_json', 'file_errors']
LOGGING_CONFIG_DEV['loggers']['transactions']['handlers'] = ['file_transactions', 'console_simple']
LOGGING_CONFIG_DEV['loggers']['rules']['handlers'] = ['file_rules', 'console_simple']
LOGGING_CONFIG_DEV['loggers']['notifications']['handlers'] = ['file_notifications', 'console_simple']


def setup_logging(environment: str = 'production'):
    """
    Инициализирует систему логирования
    
    Args:
        environment: 'production' или 'development'
    """
    config = LOGGING_CONFIG if environment == 'production' else LOGGING_CONFIG_DEV
    logging.config.dictConfig(config)
    
    # Логируем старт системы
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging system initialized in {environment} mode",
        extra={
            'component': 'logging',
            'extra_fields': {
                'log_directory': str(LOG_DIR),
                'environment': environment
            }
        }
    )
