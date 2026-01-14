"""
Bot initialization and setup using aiogram 3.x
"""
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.core.config import config

logger = logging.getLogger(__name__)


class BotManager:
    """Bot and Dispatcher manager"""
    
    def __init__(self):
        """Initialize bot and dispatcher"""
        # Create bot instance
        self.bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(
                parse_mode=ParseMode.MARKDOWN
            )
        )
        
        # Create dispatcher with FSM storage
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        
        logger.info("Bot and Dispatcher initialized")
    
    async def start(self):
        """Start the bot"""
        from bot.database.connection import init_db
        from bot.services.scheduler import start_scheduler, load_scheduled_tasks
        
        try:
            # Initialize database
            await init_db()
            
            # Start scheduler
            start_scheduler()
            logger.info("Scheduler started")
            
            # Load scheduled tasks from database
            await load_scheduled_tasks(self.bot)
            logger.info("Scheduled tasks loaded")
            
            # Get bot info
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Bot started: @{bot_info.username}")
            logger.info(f"Bot ID: {bot_info.id}")
            logger.info(f"Bot Name: {bot_info.first_name}")
            
            # Start polling
            await self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot"""
        from bot.database.connection import close_db
        from bot.services.scheduler import stop_scheduler
        
        try:
            # Stop scheduler
            stop_scheduler()
            logger.info("Scheduler stopped")
            
            # Close database connection
            await close_db()
            
            # Close bot session
            await self.bot.session.close()
            
            # Close storage
            await self.storage.close()
            
            logger.info("Bot stopped")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    def setup_handlers(self):
        """Setup all handlers"""
        from bot.handlers import setup_handlers
        from bot.keyboards.callbacks import setup_callbacks
        from bot.services.filters import register_filters
        
        setup_handlers(self.dp)
        setup_callbacks(self.dp)
        register_filters(self.dp)
        logger.info("Handlers, Callbacks, and Filters registered")
    
    def setup_middlewares(self):
        """Setup all middlewares"""
        from bot.middlewares import setup_middlewares
        
        setup_middlewares(self.dp)
        logger.info("Middlewares registered")


def create_bot() -> BotManager:
    """Create and configure bot instance"""
    # Validate configuration
    config.validate()
    
    # Create bot manager
    bot_manager = BotManager()
    
    # Setup middlewares
    bot_manager.setup_middlewares()
    
    # Setup handlers
    bot_manager.setup_handlers()
    
    return bot_manager
