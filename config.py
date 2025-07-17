import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Deepseek API Configuration
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///scheduled_content_editor.db')
    
    # Target Channel/Group ID for publishing posts
    TARGET_CHANNEL_ID = os.getenv('TARGET_CHANNEL_ID')
    
    # Bot Configuration
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Default templates for text editing
    DEFAULT_TEMPLATES = {
        "formal": "Ты — главный редактор и журналист авторского Telegram-канала Kaluga-ru, который освещает новости города Калуга. Ты пишешь тексты для публикации в канале. Текст должен быть написан на русском языке, не содержать ошибок и быть понятным для широкой аудитории. Текст должен быть написан в формальном стиле, сохранив основную мысль, а так-же убери все возможные отсылки к другим каналам",
        "casual": "Перепиши этот текст в разговорном стиле, сделав его более дружелюбным и неформальным, а так-же убери все возможные отсылки к другим каналам",
        "professional": "Перепиши этот текст в профессиональном стиле для деловой аудитории, а так-же убери все возможные отсылки к другим каналам",
        "creative": "Перепиши этот текст в креативном стиле, добавив яркие образы, а так-же убери все возможные отсылки к другим каналам",
        "concise": "Сократи этот текст, оставив только самое важное, а так-же убери все возможные отсылки к другим каналам",
        "expand": "Расширь этот текст, добавив больше деталей и объяснений:"
    } 