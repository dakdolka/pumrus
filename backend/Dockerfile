# Минимальный Python образ
FROM python:3.12-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 appuser

# Копируем код приложения
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/media && chown -R appuser:appuser /app/media

USER appuser

EXPOSE 8000

# Запуск FastAPI через uvicorn
CMD ["python", "-m", "app"]
