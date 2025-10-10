# Минимальный Python образ
FROM python:3.12-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

EXPOSE 8000

# Запуск FastAPI через uvicorn
CMD ["python", "-m", "app"]
