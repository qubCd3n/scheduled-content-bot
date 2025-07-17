# Инструкции по развертыванию

## 🚀 Быстрый старт

### 1. Подготовка окружения

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd scheduled-content-editor

# Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка конфигурации

```bash
# Скопируйте пример конфигурации
cp env.example .env

# Отредактируйте файл .env
notepad .env  # Windows
nano .env     # Linux/Mac
```

### 3. Получение необходимых токенов

#### Telegram Bot Token

1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота
   - Введите username бота (должен заканчиваться на 'bot')
4. Скопируйте полученный токен в `BOT_TOKEN`

#### Deepseek API Key

1. Зарегистрируйтесь на [Deepseek Platform](https://platform.deepseek.com/)
2. Перейдите в раздел API Keys
3. Создайте новый API ключ
4. Скопируйте ключ в `DEEPSEEK_API_KEY`

#### Target Channel ID

1. Создайте канал в Telegram
2. Добавьте бота как администратора с правами:
   - Отправка сообщений
   - Редактирование сообщений
3. Скопируйте username канала (с @) в `TARGET_CHANNEL_ID`

### 4. Тестирование

```bash
# Запустите тесты
python test_bot.py
```

### 5. Запуск бота

```bash
# Запустите бота
python main.py
```

## 🔧 Детальная настройка

### Настройка базы данных

По умолчанию используется SQLite. Для продакшена рекомендуется PostgreSQL:

```env
# SQLite (по умолчанию)
DATABASE_URL=sqlite:///scheduled_content_editor.db

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/sce_bot

# MySQL
DATABASE_URL=mysql://user:password@localhost/sce_bot
```

### Настройка логирования

```env
# Уровни логирования
LOG_LEVEL=DEBUG    # Подробные логи
LOG_LEVEL=INFO     # Основная информация
LOG_LEVEL=WARNING  # Только предупреждения
LOG_LEVEL=ERROR    # Только ошибки
```

### Настройка администратора

```env
# ID администратора (ваш Telegram ID)
ADMIN_USER_ID=123456789
```

## 🐳 Docker развертывание

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - TARGET_CHANNEL_ID=${TARGET_CHANNEL_ID}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### Запуск с Docker

```bash
# Создайте .env файл
cp env.example .env
# Отредактируйте .env

# Запустите с Docker Compose
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

## 🌐 Развертывание на сервере

### Ubuntu/Debian

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите Python и зависимости
sudo apt install python3 python3-pip python3-venv git

# Клонируйте репозиторий
git clone <repository-url>
cd scheduled-content-editor

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Настройте конфигурацию
cp env.example .env
nano .env

# Создайте systemd сервис
sudo nano /etc/systemd/system/sce-bot.service
```

### systemd сервис

```ini
[Unit]
Description=Scheduled Content Editor Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/scheduled-content-editor
Environment=PATH=/path/to/scheduled-content-editor/venv/bin
ExecStart=/path/to/scheduled-content-editor/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Управление сервисом

```bash
# Включите автозапуск
sudo systemctl enable sce-bot

# Запустите сервис
sudo systemctl start sce-bot

# Проверьте статус
sudo systemctl status sce-bot

# Просмотр логов
sudo journalctl -u sce-bot -f
```

## 🔒 Безопасность

### Переменные окружения

- Никогда не коммитьте `.env` файл
- Используйте разные ключи для разработки и продакшена
- Регулярно обновляйте API ключи

### Права доступа

```bash
# Установите правильные права
chmod 600 .env
chmod 755 main.py
```

### Firewall

```bash
# Настройте firewall (если необходимо)
sudo ufw allow ssh
sudo ufw enable
```

## 📊 Мониторинг

### Логи

```bash
# Просмотр логов в реальном времени
tail -f bot.log

# Поиск ошибок
grep ERROR bot.log
```

### Метрики

Бот логирует следующие события:
- Создание постов
- Редактирование текста
- Публикация постов
- Ошибки API
- Ошибки базы данных

## 🔄 Обновления

```bash
# Остановите бота
sudo systemctl stop sce-bot

# Обновите код
git pull origin main

# Установите новые зависимости
source venv/bin/activate
pip install -r requirements.txt

# Запустите бота
sudo systemctl start sce-bot
```

## 🆘 Устранение неполадок

### Бот не отвечает

1. Проверьте токен:
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
```

2. Проверьте логи:
```bash
tail -f bot.log
```

### Ошибки базы данных

1. Проверьте права доступа к файлу БД
2. Пересоздайте БД:
```bash
rm scheduled_content_editor.db
python main.py
```

### Ошибки API

1. Проверьте баланс Deepseek API
2. Проверьте правильность API ключа
3. Проверьте доступность API

### Проблемы с публикацией

1. Убедитесь, что бот - администратор канала
2. Проверьте права бота на публикацию
3. Проверьте правильность ID канала

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи в `bot.log`
2. Запустите тесты: `python test_bot.py`
3. Создайте Issue в репозитории с описанием проблемы 