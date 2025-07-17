#!/usr/bin/env python3
"""
Тестовый скрипт для проверки основных функций бота
"""

import asyncio
import logging
from config import Config
from database.database import init_db, create_default_templates, get_db
from services.deepseek_service import DeepseekService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_deepseek_api():
    """Тест подключения к Deepseek API"""
    print("🔍 Тестирование Deepseek API...")
    
    deepseek_service = DeepseekService()
    
    if not Config.DEEPSEEK_API_KEY:
        print("❌ DEEPSEEK_API_KEY не настроен")
        return False
        
    # Тест подключения
    if await deepseek_service.test_connection():
        print("✅ Подключение к Deepseek API успешно")
        
        # Тест редактирования текста
        test_text = "Привет, как дела?"
        test_prompt = "Перепиши этот текст в формальном стиле:"
        
        edited_text = await deepseek_service.edit_text(test_text, test_prompt)
        if edited_text:
            print(f"✅ Редактирование текста успешно:")
            print(f"Исходный: {test_text}")
            print(f"Отредактированный: {edited_text}")
            return True
        else:
            print("❌ Ошибка при редактировании текста")
            return False
    else:
        print("❌ Не удалось подключиться к Deepseek API")
        return False

async def test_database():
    """Тест базы данных"""
    print("\n🗄️ Тестирование базы данных...")
    
    try:
        # Инициализация БД
        init_db()
        print("✅ База данных инициализирована")
        
        # Создание шаблонов
        db = next(get_db())
        create_default_templates(db)
        print("✅ Шаблоны созданы")
        
        # Проверка шаблонов
        from database.models import Template
        templates = db.query(Template).filter(Template.is_default == True).all()
        print(f"✅ Найдено {len(templates)} шаблонов:")
        for template in templates:
            print(f"  - {template.name}")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка базы данных: {str(e)}")
        return False

async def test_config():
    """Тест конфигурации"""
    print("\n⚙️ Проверка конфигурации...")
    
    issues = []
    
    if not Config.BOT_TOKEN:
        issues.append("BOT_TOKEN не настроен")
    else:
        print("✅ BOT_TOKEN настроен")
        
    if not Config.DEEPSEEK_API_KEY:
        issues.append("DEEPSEEK_API_KEY не настроен (редактирование текста недоступно)")
    else:
        print("✅ DEEPSEEK_API_KEY настроен")
        
    if not Config.TARGET_CHANNEL_ID:
        issues.append("TARGET_CHANNEL_ID не настроен (публикация недоступна)")
    else:
        print("✅ TARGET_CHANNEL_ID настроен")
        
    if issues:
        print("⚠️ Предупреждения:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Все обязательные настройки выполнены")
        
    return len(issues) == 0

async def main():
    """Основная функция тестирования"""
    print("🧪 Запуск тестов Scheduled Content Editor Bot...\n")
    
    # Тест конфигурации
    config_ok = await test_config()
    
    # Тест базы данных
    db_ok = await test_database()
    
    # Тест Deepseek API
    api_ok = await test_deepseek_api()
    
    print("\n📊 Результаты тестирования:")
    print(f"Конфигурация: {'✅' if config_ok else '❌'}")
    print(f"База данных: {'✅' if db_ok else '❌'}")
    print(f"Deepseek API: {'✅' if api_ok else '❌'}")
    
    if config_ok and db_ok:
        print("\n🎉 Бот готов к запуску!")
        print("Запустите: python main.py")
    else:
        print("\n⚠️ Исправьте ошибки перед запуском бота")

if __name__ == "__main__":
    asyncio.run(main()) 