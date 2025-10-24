"""
Вспомогательные функции и классы для логирования
Специфичные для домена fraud detection
"""

import logging
import time
import functools
from typing import Any, Dict, Optional, Callable
from datetime import datetime
from enum import Enum

from .context import (
    set_correlation_id, 
    get_correlation_id,
    set_transaction_id,
    set_extra_field,
    LoggingContext
)


class LogEvent(str, Enum):
    """Стандартизированные события для логирования"""
    
    # Транзакции
    TRANSACTION_RECEIVED = "transaction.received"
    TRANSACTION_VALIDATED = "transaction.validated"
    TRANSACTION_VALIDATION_FAILED = "transaction.validation_failed"
    TRANSACTION_QUEUED = "transaction.queued"
    TRANSACTION_PROCESSING_STARTED = "transaction.processing.started"
    TRANSACTION_PROCESSING_COMPLETED = "transaction.processing.completed"
    TRANSACTION_PROCESSING_FAILED = "transaction.processing.failed"
    
    # Правила
    RULE_CREATED = "rule.created"
    RULE_UPDATED = "rule.updated"
    RULE_DELETED = "rule.deleted"
    RULE_ENABLED = "rule.enabled"
    RULE_DISABLED = "rule.disabled"
    RULE_EXECUTED = "rule.executed"
    RULE_MATCHED = "rule.matched"
    RULE_NOT_MATCHED = "rule.not_matched"
    RULE_EXECUTION_ERROR = "rule.execution.error"
    
    # ML модель
    ML_MODEL_LOADED = "ml.model.loaded"
    ML_MODEL_PREDICTION = "ml.model.prediction"
    ML_MODEL_ERROR = "ml.model.error"
    
    # Уведомления
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"
    NOTIFICATION_RETRY = "notification.retry"
    
    # Очередь
    QUEUE_MESSAGE_ADDED = "queue.message.added"
    QUEUE_MESSAGE_PROCESSED = "queue.message.processed"
    QUEUE_MESSAGE_FAILED = "queue.message.failed"
    QUEUE_MESSAGE_RETRY = "queue.message.retry"
    
    # Система
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    HEALTH_CHECK = "health.check"
    
    # Аудит
    AUDIT_USER_ACTION = "audit.user.action"
    AUDIT_DATA_ACCESS = "audit.data.access"
    AUDIT_CONFIG_CHANGE = "audit.config.change"


class StructuredLogger:
    """
    Обертка над стандартным logger с поддержкой структурированного логирования
    """
    
    def __init__(self, name: str, component: str):
        self.logger = logging.getLogger(name)
        self.component = component
    
    def _log(
        self,
        level: int,
        message: str,
        event: Optional[LogEvent] = None,
        correlation_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        **extra_fields
    ):
        """Внутренний метод для логирования"""
        extra = {
            'component': self.component,
            'extra_fields': extra_fields.copy()
        }
        
        if event:
            extra['extra_fields']['event'] = event.value
        
        if correlation_id:
            extra['correlation_id'] = correlation_id
        elif get_correlation_id():
            extra['correlation_id'] = get_correlation_id()
        
        if transaction_id:
            extra['transaction_id'] = transaction_id
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, event: Optional[LogEvent] = None, **extra_fields):
        self._log(logging.DEBUG, message, event, **extra_fields)
    
    def info(self, message: str, event: Optional[LogEvent] = None, **extra_fields):
        self._log(logging.INFO, message, event, **extra_fields)
    
    def warning(self, message: str, event: Optional[LogEvent] = None, **extra_fields):
        self._log(logging.WARNING, message, event, **extra_fields)
    
    def error(self, message: str, event: Optional[LogEvent] = None, exc_info=None, **extra_fields):
        extra = {
            'component': self.component,
            'extra_fields': extra_fields.copy()
        }
        if event:
            extra['extra_fields']['event'] = event.value
        if get_correlation_id():
            extra['correlation_id'] = get_correlation_id()
        
        self.logger.error(message, extra=extra, exc_info=exc_info)
    
    def critical(self, message: str, event: Optional[LogEvent] = None, exc_info=None, **extra_fields):
        extra = {
            'component': self.component,
            'extra_fields': extra_fields.copy()
        }
        if event:
            extra['extra_fields']['event'] = event.value
        if get_correlation_id():
            extra['correlation_id'] = get_correlation_id()
        
        self.logger.critical(message, extra=extra, exc_info=exc_info)


class TransactionLogger:
    """Специализированный логгер для транзакций"""
    
    def __init__(self):
        self.logger = StructuredLogger('transactions', 'transactions')
    
    def log_received(self, transaction_id: str, transaction_data: Dict[str, Any]):
        """Логирует получение транзакции"""
        with LoggingContext(transaction_id=transaction_id):
            self.logger.info(
                f"Transaction received: {transaction_id}",
                event=LogEvent.TRANSACTION_RECEIVED,
                transaction_id=transaction_id,
                amount=transaction_data.get('amount'),
                from_account=transaction_data.get('from'),
                to_account=transaction_data.get('to'),
                transaction_type=transaction_data.get('type'),
                timestamp=transaction_data.get('timestamp')
            )
    
    def log_validation_failed(self, transaction_id: str, errors: list):
        """Логирует ошибку валидации"""
        with LoggingContext(transaction_id=transaction_id):
            self.logger.warning(
                f"Transaction validation failed: {transaction_id}",
                event=LogEvent.TRANSACTION_VALIDATION_FAILED,
                transaction_id=transaction_id,
                errors=errors
            )
    
    def log_queued(self, transaction_id: str, queue_name: str):
        """Логирует постановку в очередь"""
        with LoggingContext(transaction_id=transaction_id):
            self.logger.info(
                f"Transaction queued: {transaction_id}",
                event=LogEvent.TRANSACTION_QUEUED,
                transaction_id=transaction_id,
                queue=queue_name
            )
    
    def log_processing_started(self, transaction_id: str):
        """Логирует начало обработки"""
        with LoggingContext(transaction_id=transaction_id):
            self.logger.info(
                f"Transaction processing started: {transaction_id}",
                event=LogEvent.TRANSACTION_PROCESSING_STARTED,
                transaction_id=transaction_id,
                started_at=datetime.utcnow().isoformat()
            )
    
    def log_processing_completed(
        self,
        transaction_id: str,
        duration_ms: float,
        rules_matched: list,
        status: str
    ):
        """Логирует завершение обработки"""
        with LoggingContext(transaction_id=transaction_id):
            self.logger.info(
                f"Transaction processing completed: {transaction_id}",
                event=LogEvent.TRANSACTION_PROCESSING_COMPLETED,
                transaction_id=transaction_id,
                duration_ms=duration_ms,
                rules_matched=rules_matched,
                rules_count=len(rules_matched),
                status=status,
                completed_at=datetime.utcnow().isoformat()
            )
    
    def log_processing_failed(self, transaction_id: str, error: str):
        """Логирует ошибку обработки"""
        with LoggingContext(transaction_id=transaction_id):
            self.logger.error(
                f"Transaction processing failed: {transaction_id}",
                event=LogEvent.TRANSACTION_PROCESSING_FAILED,
                transaction_id=transaction_id,
                error=error,
                failed_at=datetime.utcnow().isoformat()
            )


class RuleLogger:
    """Специализированный логгер для правил"""
    
    def __init__(self):
        self.logger = StructuredLogger('rules', 'rules')
    
    def log_executed(
        self,
        rule_id: str,
        rule_name: str,
        rule_type: str,
        transaction_id: str,
        matched: bool,
        execution_time_ms: float,
        details: Optional[Dict] = None
    ):
        """Логирует выполнение правила"""
        event = LogEvent.RULE_MATCHED if matched else LogEvent.RULE_NOT_MATCHED
        
        log_data = {
            'rule_id': rule_id,
            'rule_name': rule_name,
            'rule_type': rule_type,
            'transaction_id': transaction_id,
            'matched': matched,
            'execution_time_ms': execution_time_ms
        }
        
        if details:
            log_data.update(details)
        
        self.logger.info(
            f"Rule executed: {rule_name} ({'matched' if matched else 'not matched'})",
            event=event,
            **log_data
        )
    
    def log_created(self, rule_id: str, rule_name: str, rule_type: str, user_id: Optional[str] = None):
        """Логирует создание правила"""
        self.logger.info(
            f"Rule created: {rule_name}",
            event=LogEvent.RULE_CREATED,
            rule_id=rule_id,
            rule_name=rule_name,
            rule_type=rule_type,
            user_id=user_id,
            created_at=datetime.utcnow().isoformat()
        )
    
    def log_updated(self, rule_id: str, rule_name: str, changes: Dict, user_id: Optional[str] = None):
        """Логирует обновление правила"""
        self.logger.info(
            f"Rule updated: {rule_name}",
            event=LogEvent.RULE_UPDATED,
            rule_id=rule_id,
            rule_name=rule_name,
            changes=changes,
            user_id=user_id,
            updated_at=datetime.utcnow().isoformat()
        )
    
    def log_deleted(self, rule_id: str, rule_name: str, user_id: Optional[str] = None):
        """Логирует удаление правила"""
        self.logger.info(
            f"Rule deleted: {rule_name}",
            event=LogEvent.RULE_DELETED,
            rule_id=rule_id,
            rule_name=rule_name,
            user_id=user_id,
            deleted_at=datetime.utcnow().isoformat()
        )
    
    def log_execution_error(self, rule_id: str, rule_name: str, transaction_id: str, error: str):
        """Логирует ошибку выполнения правила"""
        self.logger.error(
            f"Rule execution error: {rule_name}",
            event=LogEvent.RULE_EXECUTION_ERROR,
            rule_id=rule_id,
            rule_name=rule_name,
            transaction_id=transaction_id,
            error=error
        )


class NotificationLogger:
    """Специализированный логгер для уведомлений"""
    
    def __init__(self):
        self.logger = StructuredLogger('notifications', 'notifications')
    
    def log_sent(
        self,
        notification_id: str,
        channel: str,
        recipient: str,
        transaction_id: str,
        duration_ms: float
    ):
        """Логирует успешную отправку уведомления"""
        self.logger.info(
            f"Notification sent via {channel}",
            event=LogEvent.NOTIFICATION_SENT,
            notification_id=notification_id,
            channel=channel,
            recipient=recipient,
            transaction_id=transaction_id,
            duration_ms=duration_ms,
            sent_at=datetime.utcnow().isoformat()
        )
    
    def log_failed(
        self,
        notification_id: str,
        channel: str,
        recipient: str,
        transaction_id: str,
        error: str,
        retry_count: int = 0
    ):
        """Логирует неудачную отправку уведомления"""
        self.logger.error(
            f"Notification failed via {channel}",
            event=LogEvent.NOTIFICATION_FAILED,
            notification_id=notification_id,
            channel=channel,
            recipient=recipient,
            transaction_id=transaction_id,
            error=error,
            retry_count=retry_count,
            failed_at=datetime.utcnow().isoformat()
        )
    
    def log_retry(self, notification_id: str, channel: str, attempt: int):
        """Логирует повторную попытку отправки"""
        self.logger.info(
            f"Notification retry #{attempt} via {channel}",
            event=LogEvent.NOTIFICATION_RETRY,
            notification_id=notification_id,
            channel=channel,
            attempt=attempt
        )


class AuditLogger:
    """Специализированный логгер для аудита"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ):
        """Логирует действие пользователя"""
        log_data = {
            'component': 'audit',
            'extra_fields': {
                'event': LogEvent.AUDIT_USER_ACTION.value,
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        if details:
            log_data['extra_fields']['details'] = details
        if ip_address:
            log_data['extra_fields']['ip_address'] = ip_address
        
        self.logger.info(
            f"User action: {user_id} {action} {resource_type}/{resource_id}",
            extra=log_data
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        access_type: str  # 'read', 'write', 'delete'
    ):
        """Логирует доступ к данным"""
        log_data = {
            'component': 'audit',
            'extra_fields': {
                'event': LogEvent.AUDIT_DATA_ACCESS.value,
                'user_id': user_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'access_type': access_type,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        self.logger.info(
            f"Data access: {user_id} {access_type} {resource_type}/{resource_id}",
            extra=log_data
        )
    
    def log_config_change(
        self,
        user_id: str,
        config_key: str,
        old_value: Any,
        new_value: Any
    ):
        """Логирует изменение конфигурации"""
        log_data = {
            'component': 'audit',
            'extra_fields': {
                'event': LogEvent.AUDIT_CONFIG_CHANGE.value,
                'user_id': user_id,
                'config_key': config_key,
                'old_value': str(old_value),
                'new_value': str(new_value),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        self.logger.info(
            f"Config change: {config_key} by {user_id}",
            extra=log_data
        )


class MetricsLogger:
    """Специализированный логгер для метрик"""
    
    def __init__(self):
        self.logger = logging.getLogger('metrics')
    
    def log_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_type: str,  # 'counter', 'gauge', 'histogram'
        tags: Optional[Dict[str, str]] = None
    ):
        """Логирует метрику"""
        log_data = {
            'component': 'metrics',
            'extra_fields': {
                'metric_name': metric_name,
                'metric_value': metric_value,
                'metric_type': metric_type,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        if tags:
            log_data['extra_fields']['tags'] = tags
        
        self.logger.info(
            f"Metric: {metric_name}={metric_value}",
            extra=log_data
        )


def log_execution_time(logger: StructuredLogger, operation_name: str):
    """
    Декоратор для логирования времени выполнения функции
    
    Usage:
        @log_execution_time(logger, 'process_transaction')
        def process_transaction(tx):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"{operation_name} completed",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    status='success'
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"{operation_name} failed",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    status='error',
                    error=str(e),
                    exc_info=True
                )
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"{operation_name} completed",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    status='success'
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"{operation_name} failed",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    status='error',
                    error=str(e),
                    exc_info=True
                )
                raise
        
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x100:
            return async_wrapper
        return wrapper
    
    return decorator


def log_method_call(logger: StructuredLogger):
    """
    Декоратор для автоматического логирования вызовов методов
    
    Usage:
        class MyService:
            @log_method_call(logger)
            def process(self, data):
                ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(
                f"Method called: {func_name}",
                method=func_name,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(
                f"Method called: {func_name}",
                method=func_name,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            return await func(*args, **kwargs)
        
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x100:
            return async_wrapper
        return wrapper
    
    return decorator


# Создаем глобальные экземпляры логгеров для удобства
transaction_logger = TransactionLogger()
rule_logger = RuleLogger()
notification_logger = NotificationLogger()
audit_logger = AuditLogger()
metrics_logger = MetricsLogger()
