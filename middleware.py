"""
Middleware для автоматического логирования HTTP запросов
Поддерживает Flask, FastAPI и другие фреймворки
"""

import time
import logging
from typing import Callable, Optional
from datetime import datetime
import json

from .context import set_correlation_id, get_correlation_id, LoggingContext
from .helpers import StructuredLogger


class HTTPLoggingMiddleware:
    """
    Middleware для логирования HTTP запросов и ответов
    """
    
    def __init__(self, app, service_name: str = "fraud-detection"):
        self.app = app
        self.logger = StructuredLogger('http', 'http')
        self.service_name = service_name
    
    def _extract_correlation_id(self, headers) -> str:
        """Извлекает или создает correlation ID из заголовков"""
        # Пробуем различные варианты заголовков
        correlation_headers = [
            'X-Correlation-ID',
            'X-Request-ID',
            'X-Trace-ID',
            'Correlation-ID',
            'Request-ID'
        ]
        
        for header in correlation_headers:
            value = headers.get(header)
            if value:
                return value
        
        # Генерируем новый если не найден
        from .context import generate_correlation_id
        return generate_correlation_id()
    
    def _should_log_body(self, content_type: Optional[str], path: str) -> bool:
        """Определяет, нужно ли логировать тело запроса/ответа"""
        # Не логируем binary content
        if not content_type:
            return False
        
        # Логируем только JSON и text
        log_types = ['application/json', 'text/', 'application/xml']
        return any(content_type.startswith(t) for t in log_types)
    
    def _sanitize_body(self, body: str, max_length: int = 10000) -> str:
        """Очищает тело от чувствительных данных"""
        if len(body) > max_length:
            body = body[:max_length] + '... [truncated]'
        
        # Пытаемся парсить JSON и скрыть чувствительные поля
        try:
            data = json.loads(body)
            sensitive_fields = ['password', 'token', 'secret', 'api_key', 'apiKey']
            
            def sanitize_dict(d):
                if isinstance(d, dict):
                    return {
                        k: '***REDACTED***' if k.lower() in sensitive_fields else sanitize_dict(v)
                        for k, v in d.items()
                    }
                elif isinstance(d, list):
                    return [sanitize_dict(item) for item in d]
                return d
            
            return json.dumps(sanitize_dict(data))
        except:
            # Если не JSON, возвращаем как есть
            return body


class FlaskLoggingMiddleware(HTTPLoggingMiddleware):
    """Middleware для Flask"""
    
    def __call__(self, environ, start_response):
        from flask import request, g
        
        # Извлекаем correlation ID
        correlation_id = self._extract_correlation_id(request.headers)
        set_correlation_id(correlation_id)
        
        # Сохраняем в g для доступа в views
        g.correlation_id = correlation_id
        
        start_time = time.time()
        
        # Логируем начало запроса
        self.logger.info(
            f"HTTP Request: {request.method} {request.path}",
            correlation_id=correlation_id,
            method=request.method,
            path=request.path,
            query_string=request.query_string.decode('utf-8'),
            remote_addr=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            content_type=request.content_type,
            content_length=request.content_length
        )
        
        # Логируем тело запроса если нужно
        if self._should_log_body(request.content_type, request.path):
            try:
                body = request.get_data(as_text=True)
                if body:
                    sanitized_body = self._sanitize_body(body)
                    self.logger.debug(
                        "Request body",
                        correlation_id=correlation_id,
                        body=sanitized_body
                    )
            except Exception as e:
                self.logger.warning(f"Failed to log request body: {e}")
        
        # Перехватываем response
        def custom_start_response(status, headers, exc_info=None):
            duration_ms = (time.time() - start_time) * 1000
            status_code = int(status.split()[0])
            
            # Логируем ответ
            self.logger.info(
                f"HTTP Response: {status_code} {request.method} {request.path}",
                correlation_id=correlation_id,
                method=request.method,
                path=request.path,
                status_code=status_code,
                duration_ms=duration_ms
            )
            
            # Добавляем correlation ID в заголовки ответа
            headers.append(('X-Correlation-ID', correlation_id))
            
            return start_response(status, headers, exc_info)
        
        return self.app(environ, custom_start_response)


class FastAPILoggingMiddleware:
    """Middleware для FastAPI"""
    
    def __init__(self, service_name: str = "fraud-detection"):
        self.logger = StructuredLogger('http', 'http')
        self.service_name = service_name
    
    async def __call__(self, request, call_next):
        from fastapi import Request
        
        # Извлекаем correlation ID
        correlation_id = self._extract_correlation_id(request.headers)
        set_correlation_id(correlation_id)
        
        # Добавляем в state для доступа в endpoints
        request.state.correlation_id = correlation_id
        
        start_time = time.time()
        
        # Логируем начало запроса
        self.logger.info(
            f"HTTP Request: {request.method} {request.url.path}",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent')
        )
        
        # Логируем тело запроса для POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8')
                    sanitized_body = self._sanitize_body(body_str)
                    self.logger.debug(
                        "Request body",
                        correlation_id=correlation_id,
                        body=sanitized_body
                    )
            except Exception as e:
                self.logger.warning(f"Failed to log request body: {e}")
        
        # Обрабатываем запрос
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Логируем ответ
            self.logger.info(
                f"HTTP Response: {response.status_code} {request.method} {request.url.path}",
                correlation_id=correlation_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            # Добавляем correlation ID в заголовки
            response.headers['X-Correlation-ID'] = correlation_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.error(
                f"HTTP Request failed: {request.method} {request.url.path}",
                correlation_id=correlation_id,
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error=str(e),
                exc_info=True
            )
            raise
    
    def _extract_correlation_id(self, headers) -> str:
        """Извлекает или создает correlation ID"""
        correlation_headers = [
            'x-correlation-id',
            'x-request-id',
            'x-trace-id'
        ]
        
        for header in correlation_headers:
            value = headers.get(header)
            if value:
                return value
        
        from .context import generate_correlation_id
        return generate_correlation_id()
    
    def _sanitize_body(self, body: str, max_length: int = 10000) -> str:
        """Очищает тело от чувствительных данных"""
        if len(body) > max_length:
            body = body[:max_length] + '... [truncated]'
        
        try:
            data = json.loads(body)
            sensitive_fields = ['password', 'token', 'secret', 'api_key']
            
            def sanitize_dict(d):
                if isinstance(d, dict):
                    return {
                        k: '***REDACTED***' if k.lower() in sensitive_fields else sanitize_dict(v)
                        for k, v in d.items()
                    }
                elif isinstance(d, list):
                    return [sanitize_dict(item) for item in d]
                return d
            
            return json.dumps(sanitize_dict(data))
        except:
            return body


class ErrorLoggingMiddleware:
    """
    Middleware для перехвата и логирования необработанных исключений
    """
    
    def __init__(self):
        self.logger = StructuredLogger('errors', 'errors')
    
    async def __call__(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            correlation_id = get_correlation_id()
            
            self.logger.error(
                f"Unhandled exception: {type(e).__name__}",
                correlation_id=correlation_id,
                exception_type=type(e).__name__,
                exception_message=str(e),
                path=request.url.path,
                method=request.method,
                exc_info=True
            )
            
            # Пробрасываем исключение дальше
            raise


def log_slow_requests(threshold_ms: float = 1000):
    """
    Декоратор для логирования медленных запросов
    
    Usage:
        @app.before_request
        @log_slow_requests(threshold_ms=500)
        def before_request():
            ...
    """
    def decorator(func: Callable) -> Callable:
        logger = StructuredLogger('performance', 'http')
        
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            if duration_ms > threshold_ms:
                logger.warning(
                    f"Slow request detected: {duration_ms:.2f}ms",
                    duration_ms=duration_ms,
                    threshold_ms=threshold_ms
                )
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            if duration_ms > threshold_ms:
                logger.warning(
                    f"Slow request detected: {duration_ms:.2f}ms",
                    duration_ms=duration_ms,
                    threshold_ms=threshold_ms
                )
            
            return result
        
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x100:
            return async_wrapper
        return sync_wrapper
    
    return decorator
