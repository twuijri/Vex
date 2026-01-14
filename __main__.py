"""
Main entry point for the Telegram Bot
"""
import asyncio
import logging
import sys
from bot.core.bot import create_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main function"""
    logger.info("=" * 50)
    logger.info("Starting Telegram Group Management Bot")
    logger.info("=" * 50)
    
    try:
        # Create bot instance
        bot_manager = create_bot()
        
        # Start bot
        await bot_manager.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if 'bot_manager' in locals():
            await bot_manager.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
