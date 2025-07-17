# 🚀 Быстрый запуск Scheduled Content Editor Bot

## 📋 Что нужно сделать за 5 минут

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Создание конфигурации
```bash
cp env.example .env
```

### 3. Настройка переменных окружения

Отредактируйте файл `.env`:

```env
# ОБЯЗАТЕЛЬНО - получите у @BotFather
BOT_TOKEN=your_telegram_bot_token_here

# ОПЦИОНАЛЬНО - для редактирования текста
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# ОБЯЗАТЕЛЬНО - канал для публикации
TARGET_CHANNEL_ID=@your_channel_username
```

### 4. Тестирование
```bash
python test_bot.py
```

### 5. Запуск
```bash
python main.py
```

## 🔧 Получение токенов

### Telegram Bot Token
1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `BOT_TOKEN`

### Deepseek API Key
1. Зарегистрируйтесь на [Deepseek Platform](https://platform.deepseek.com/)
2. Создайте API ключ
3. Скопируйте в `DEEPSEEK_API_KEY`

### Target Channel
1. Создайте канал в Telegram
2. Добавьте бота как администратора
3. Скопируйте username канала в `TARGET_CHANNEL_ID`

## 📱 Использование

1. Отправьте боту текст и/или медиа
2. Выберите метод редактирования
3. Подтвердите редактирование
4. Укажите время публикации (ДД.ММ.ГГГГ ЧЧ:ММ)
5. Подтвердите финальный пост

## 🆘 Проблемы?

- Проверьте логи: `tail -f bot.log`
- Запустите тесты: `python test_bot.py`
- Убедитесь, что все токены правильные

## 📚 Подробная документация

См. [README.md](README.md) и [DEPLOYMENT.md](DEPLOYMENT.md) 