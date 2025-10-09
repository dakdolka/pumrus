# Используем минимальный Node образ
FROM node:20-alpine

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем весь код проекта
COPY . .

# Экспонируем порт разработки
EXPOSE 3000

# Команда запуска
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
