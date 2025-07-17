import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

from config import Config
from database.database import init_db, create_default_templates, get_db
from services.scheduler_service import SchedulerService
from handlers.user_handlers import router as user_router, init_user_handlers

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ScheduledContentEditorBot:
    def __init__(self):
        self.bot = Bot(token=Config.BOT_TOKEN, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.scheduler_service = SchedulerService(self.bot)
        self.user_handlers = init_user_handlers(self.scheduler_service)
        
    async def start(self):
        """Start the bot"""
        try:
            # Initialize database
            logger.info("Initializing database...")
            init_db()
            
            # Create default templates
            db = next(get_db())
            create_default_templates(db)
            
            # Test Deepseek API connection
            from services.deepseek_service import DeepseekService
            deepseek_service = DeepseekService()
            if await deepseek_service.test_connection():
                logger.info("Deepseek API connection successful")
            else:
                logger.warning("Deepseek API connection failed. Check your API key.")
                
            # Start scheduler service
            await self.scheduler_service.start()
            
            # Register routers
            self.dp.include_router(user_router)
            
            # Start polling
            logger.info("Starting bot...")
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            raise
            
    async def stop(self):
        """Stop the bot"""
        try:
            await self.scheduler_service.stop()
            await self.bot.session.close()
            logger.info("Bot stopped")
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")

async def main():
    """Main function"""
    bot = ScheduledContentEditorBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    # Check required configuration
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN not configured. Please set it in environment variables.")
        sys.exit(1)
        
    if not Config.DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY not configured. Text editing will not work.")
        
    if not Config.TARGET_CHANNEL_ID:
        logger.warning("TARGET_CHANNEL_ID not configured. Posts will not be published.")
        
    # Run the bot
    asyncio.run(main()) 