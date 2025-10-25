# Multi-stage build для оптимизации размера образа
FROM python:3.11-slim as base

# Метаданные
LABEL maintainer="Alexander132770"
LABEL description="Fraud Detection Logging System"
LABEL version="1.0.0"

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage для production
FROM python:3.11-slim as production

WORKDIR /app

# Копируем установленные пакеты из базового образа
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Создаем пользователя без root прав
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Копируем код приложения
COPY --chown=appuser:appuser logging_system/ ./logging_system/
COPY --chown=appuser:appuser config/ ./config/

# Переключаемся на непривилегированного пользователя
USER appuser

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    LOG_DIR=/app/logs \
    LOG_LEVEL=INFO

# Создаем volume для логов
VOLUME ["/app/logs"]

# Expose порты
EXPOSE 8000 9090

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда запуска (будет переопределена в docker-compose)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
