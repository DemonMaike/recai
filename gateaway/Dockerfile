FROM python:3.9-slim

# Устанавливаем рабочий каталог в контейнере
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .
COPY ../database/ .
COPY ../.env .


# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения в контейнер
COPY ./app /app

# Указываем порт, который будет слушать контейнер
EXPOSE 8000

# Команда для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
