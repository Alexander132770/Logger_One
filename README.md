# Система логирования для Fraud Detection Service

## Обзор

Надежная и масштабируемая система структурированного логирования для сервиса обнаружения мошенничества в финансовых транзакциях.

## Основные возможности

### 🎯 Ключевые характеристики

- **Структурированное логирование** в формате JSON
- **Correlation ID** для трассировки запросов через все компоненты
- **Специализированные логгеры** для разных доменов (транзакции, правила, уведомления)
- **Автоматическое логирование HTTP** через middleware
- **Аудит действий пользователей** с полной историей
- **Метрики производительности** для всех операций
- **Централизованный сбор логов** (Graylog/Loki/ELK)
- **Визуализация в реальном времени** через Grafana
- **Ротация и архивация** логов

### 📊 Типы логов

1. **Application logs** - общие логи приложения
2. **Transaction logs** - логи обработки транзакций
3. **Rule logs** - логи выполнения правил
4. **Notification logs** - логи отправки уведомлений
5. **Audit logs** - логи действий пользователей
6. **Metrics logs** - метрики производительности
7. **Error logs** - все ошибки системы

## Структура проекта

```
logging_system/
├── __init__.py
├── config.py              # Конфигурация логирования
├── context.py             # Управление контекстом (correlation_id, etc.)
├── helpers.py             # Вспомогательные функции и специализированные логгеры
├── middleware.py          # HTTP middleware для Flask/FastAPI
└── usage_example.py       # Примеры использования

config/
├── prometheus.yml         # Конфигурация Prometheus
├── alerts.yml            # Правила алертов
├── loki-config.yml       # Конфигурация Loki
├── promtail-config.yml   # Конфигурация Promtail
├── filebeat.yml          # Конфигурация Filebeat
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   └── dashboards/
    └── dashboards/

logs/
├── application.json.log   # Основные логи
├── transactions.json.log  # Логи транзакций
├── rules.json.log        # Логи правил
├── notifications.json.log # Логи уведомлений
├── audit.json.log        # Аудит
├── metrics.json.log      # Метрики
└── errors.json.log       # Ошибки
```

## Быстрый старт

### 1. Инициализация системы

```python
from logging_system.config import setup_logging
import os

# В начале приложения
environment = os.getenv('ENVIRONMENT', 'production')
setup_logging(environment)
```

### 2. Базовое использование

```python
from logging_system.helpers import StructuredLogger, LogEvent

# Создаем логгер для компонента
logger = StructuredLogger('my_service', 'component_name')

# Логируем с событием
logger.info(
    "Processing started",
    event=LogEvent.TRANSACTION_PROCESSING_STARTED,
    transaction_id="tx123",
    amount=1000.0
)
```

### 3. Использование контекста

```python
from logging_system.context import LoggingContext

# Автоматическая установка correlation_id
with LoggingContext(
    correlation_id="abc-123",
    transaction_id="tx-456",
    user_id="user789"
):
    # Все логи внутри будут содержать эти ID
    logger.info("Processing transaction")
    process_transaction()
```

### 4. Специализированные логгеры

```python
from logging_system.helpers import (
    transaction_logger,
    rule_logger,
    notification_logger,
    audit_logger
)

# Логирование транзакции
transaction_logger.log_received(
    transaction_id="tx123",
    transaction_data={"amount": 1000, "from": "acc1", "to": "acc2"}
)

# Логирование правила
rule_logger.log_executed(
    rule_id="rule1",
    rule_name="High Amount Threshold",
    rule_type="threshold",
    transaction_id="tx123",
    matched=True,
    execution_time_ms=5.2
)

# Логирование уведомления
notification_logger.log_sent(
    notification_id="notif1",
    channel="email",
    recipient="admin@example.com",
    transaction_id="tx123",
    duration_ms=150.0
)

# Аудит действий пользователя
audit_logger.log_user_action(
    user_id="admin1",
    action="create",
    resource_type="rule",
    resource_id="rule123",
    details={"name": "New Rule"}
)
```

### 5. HTTP Middleware

#### FastAPI

```python
from fastapi import FastAPI
from logging_system.middleware import FastAPILoggingMiddleware

app = FastAPI()
app.middleware("http")(FastAPILoggingMiddleware())

@app.post("/transactions")
async def create_transaction(data: dict, request: Request):
    # correlation_id автоматически установлен
    correlation_id = request.state.correlation_id
    return {"status": "ok", "correlation_id": correlation_id}
```

#### Flask

```python
from flask import Flask
from logging_system.middleware import FlaskLoggingMiddleware

app = Flask(__name__)
app.wsgi_app = FlaskLoggingMiddleware(app.wsgi_app)

@app.route('/transactions', methods=['POST'])
def create_transaction():
    # correlation_id доступен в g.correlation_id
    return {"status": "ok"}
```

### 6. Декораторы

```python
from logging_system.helpers import log_execution_time, log_method_call

logger = StructuredLogger('service', 'processing')

@log_execution_time(logger, 'process_transaction')
def process_transaction(tx):
    # Время выполнения будет автоматически залогировано
    return process(tx)

@log_method_call(logger)
def some_method(self, param1, param2):
    # Вызов метода будет залогирован
    pass
```

## Формат логов

### Структура JSON лога

```json
{
  "timestamp": "2025-10-25T10:30:45.123456Z",
  "level": "INFO",
  "logger": "transactions",
  "component": "transactions",
  "message": "Transaction received: tx123",
  "service": "fraud-detection-service",
  "hostname": "app-server-01",
  "thread": 12345,
  "thread_name": "MainThread",
  "correlation_id": "abc-123-def-456",
  "transaction_id": "tx123",
  "location": {
    "file": "/app/services/transaction_service.py",
    "line": 45,
    "function": "process_transaction",
    "module": "transaction_service"
  },
  "extra_fields": {
    "event": "transaction.received",
    "amount": 1000.0,
    "from_account": "acc1",
    "to_account": "acc2",
    "transaction_type": "transfer"
  }
}
```

### События (LogEvent)

Стандартизированные события для единообразного логирования:

```python
# Транзакции
LogEvent.TRANSACTION_RECEIVED
LogEvent.TRANSACTION_VALIDATED
LogEvent.TRANSACTION_VALIDATION_FAILED
LogEvent.TRANSACTION_QUEUED
LogEvent.TRANSACTION_PROCESSING_STARTED
LogEvent.TRANSACTION_PROCESSING_COMPLETED
LogEvent.TRANSACTION_PROCESSING_FAILED

# Правила
LogEvent.RULE_CREATED
LogEvent.RULE_UPDATED
LogEvent.RULE_DELETED
LogEvent.RULE_EXECUTED
LogEvent.RULE_MATCHED
LogEvent.RULE_NOT_MATCHED

# Уведомления
LogEvent.NOTIFICATION_SENT
LogEvent.NOTIFICATION_FAILED
LogEvent.NOTIFICATION_RETRY

# Аудит
LogEvent.AUDIT_USER_ACTION
LogEvent.AUDIT_DATA_ACCESS
LogEvent.AUDIT_CONFIG_CHANGE
```

## Развертывание

### Docker Compose

```bash
# Запуск всех сервисов логирования
docker-compose -f docker-compose.logging.yml up -d

# Проверка статуса
docker-compose -f docker-compose.logging.yml ps

# Просмотр логов
docker-compose -f docker-compose.logging.yml logs -f fraud-detection-app
```

### Доступ к сервисам

- **Приложение**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9091
- **Graylog**: http://localhost:9000 (admin/admin)
- **Loki**: http://localhost:3100

## Мониторинг и визуализация

### Grafana Dashboards

После запуска доступны следующие дашборды:

1. **Transaction Processing Dashboard**
   - Количество обработанных транзакций
   - Время обработки (p50, p95, p99)
   - Rate обработки
   - Количество ошибок

2. **Rules Execution Dashboard**
   - Количество срабатываний правил
   - Время выполнения правил
   - Топ правил по частоте срабатывания

3. **Alerts Dashboard**
   - Количество алертов
   - Распределение по типам
   - Время отправки уведомлений

4. **System Health Dashboard**
   - Размер очереди
   - CPU и память
   - Latency
   - Error rate

### Поиск в логах (Graylog/Loki)

#### Примеры запросов в Graylog:

```
# Все ошибки за последний час
level:ERROR

# Транзакции конкретного пользователя
transaction_id:tx123

# Трассировка по correlation_id
correlation_id:"abc-123-def-456"

# Медленные транзакции (>1000ms)
duration_ms:>1000 AND component:processing

# Срабатывания конкретного правила
rule_name:"High Amount Threshold" AND event:rule.matched

# Неудачные уведомления
event:notification.failed AND channel:email
```

#### Примеры запросов в Loki (LogQL):

```
# Все логи приложения
{job="fraud-detection"}

# Только ошибки
{job="fraud-detection"} |= "ERROR"

# Фильтр по correlation_id
{job="fraud-detection"} | json | correlation_id="abc-123"

# Транзакции с конкретным статусом
{job="fraud-detection-transactions"} | json | status="alerted"

# Подсчет ошибок за период
sum(rate({job="fraud-detection"} |= "ERROR" [5m]))
```

## Best Practices

### 1. Всегда используйте correlation_id

```python
# ✅ Правильно
with LoggingContext(correlation_id=request_id):
    process_request()

# ❌ Неправильно
process_request()  # Нет контекста
```

### 2. Логируйте структурированные данные

```python
# ✅ Правильно
logger.info(
    "Transaction processed",
    transaction_id=tx_id,
    amount=amount,
    duration_ms=duration
)

# ❌ Неправильно
logger.info(f"Transaction {tx_id} processed, amount: {amount}")
```

### 3. Используйте правильные уровни

- **DEBUG**: Детальная информация для отладки
- **INFO**: Обычные операции, события бизнес-логики
- **WARNING**: Неожиданные ситуации, которые не мешают работе
- **ERROR**: Ошибки, требующие внимания
- **CRITICAL**: Критические ошибки, требующие немедленного реагирования

### 4. Не логируйте чувствительные данные

```python
# ✅ Правильно
logger.info("User authenticated", user_id=user.id)

# ❌ Неправильно
logger.info("User authenticated", password=user.password)
```

### 5. Логируйте начало и конец операций

```python
logger.info("Starting transaction processing", transaction_id=tx_id)
try:
    result = process()
    logger.info("Transaction processing completed", 
                transaction_id=tx_id, 
                result=result)
except Exception as e:
    logger.error("Transaction processing failed",
                 transaction_id=tx_id,
                 error=str(e),
                 exc_info=True)
```

## Troubleshooting

### Логи не появляются в Graylog

1. Проверьте подключение:
```bash
docker-compose logs fraud-detection-app | grep graylog
```

2. Проверьте Graylog inputs:
   - Перейдите в System → Inputs
   - Убедитесь, что GELF UDP input запущен

3. Проверьте firewall:
```bash
telnet localhost 12201
```

### Высокое потребление диска

1. Проверьте размер логов:
```bash
du -sh logs/
```

2. Настройте ротацию в `config.py`:
```python
'maxBytes': 100 * 1024 * 1024,  # 100MB
'backupCount': 10
```

3. Очистите старые логи:
```bash
find logs/ -name "*.log.*" -mtime +30 -delete
```

### Метрики не отображаются в Grafana

1. Проверьте Prometheus targets:
   - http://localhost:9091/targets
   - Все targets должны быть UP

2. Проверьте datasource в Grafana:
   - Configuration → Data Sources → Prometheus
   - Test connection

3. Проверьте экспорт метрик:
```bash
curl http://localhost:9090/metrics
```

## Performance Optimization

### 1. Асинхронное логирование

```python
from logging.handlers import QueueHandler, QueueListener
import queue

# Создаем очередь для асинхронной записи
log_queue = queue.Queue(-1)
queue_handler = QueueHandler(log_queue)

# Добавляем handler
logger.addHandler(queue_handler)

# Запускаем listener
listener = QueueListener(log_queue, file_handler)
listener.start()
```

### 2. Батчинг логов

```python
# Для высоконагруженных систем используйте батчинг
# в конфигурации Filebeat/Promtail
```

### 3. Sampling для debug логов

```python
import random

def should_log_debug():
    return random.random() < 0.01  # 1% sampling

if should_log_debug():
    logger.debug("Detailed debug info", ...)
```

## Maintenance

### Регулярные задачи

1. **Ежедневно**: Проверка размера логов
2. **Еженедельно**: Анализ error rate
3. **Ежемесячно**: Архивация старых логов
4. **Ежеквартально**: Ревью retention policy

### Backup логов

```bash
#!/bin/bash
# backup_logs.sh
DATE=$(date +%Y%m%d)
tar -czf logs_backup_$DATE.tar.gz logs/
aws s3 cp logs_backup_$DATE.tar.gz s3://backups/logs/
```

## Заключение

Эта система логирования обеспечивает:

✅ Полную трассируемость всех операций  
✅ Быстрый поиск и анализ проблем  
✅ Соответствие требованиям аудита  
✅ Мониторинг производительности в реальном времени  
✅ Масштабируемость и надежность  

Для вопросов и предложений создавайте issues в репозитории проекта.
