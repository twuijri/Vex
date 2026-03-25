"""
Vex - Application Entry Point
Starts both the Telegram bot and the web dashboard
"""
import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import init_db
from bot.core.config import load_bot_config
from web.app import start_web_server

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("vex.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("vex")


async def main():
    """Main entry point - starts DB, Web, and Bot"""
    # 1. Initialize database tables
    logger.info("🗄 Initializing database...")
    await init_db()

    # 2. Check if setup is complete
    config = await load_bot_config()

    if config and config.is_setup_complete:
        # 3a. Setup complete → start bot + web dashboard
        logger.info("✅ Bot configuration found. Starting bot and web dashboard...")
        from bot.core.bot import create_bot_application

        app = await create_bot_application(config)

        # Start web server in background
        web_task = asyncio.create_task(
            start_web_server(bot_app=app)
        )

        webhook_url = os.getenv("WEBHOOK_URL")

        # Start bot
        logger.info(f"🤖 Starting bot @{config.bot_username}...")
        async with app:
            await app.start()
            
            if webhook_url:
                # Webhook Mode
                logger.info(f"🔗 Starting in Webhook mode. URL: {webhook_url}/telegram-update")
                await app.bot.set_webhook(url=f"{webhook_url}/telegram-update", drop_pending_updates=True)
                logger.info("🚀 Bot is running (Webhooks enabled)!")
            else:
                # Polling Mode
                logger.info("📡 Starting in Polling mode (No WEBHOOK_URL found)")
                await app.bot.delete_webhook(drop_pending_updates=True)
                await app.updater.start_polling(drop_pending_updates=True)
                logger.info("🚀 Bot is running (Polling)!")

            # Wait until interrupted
            try:
                await web_task
            except asyncio.CancelledError:
                pass
            finally:
                if not webhook_url:
                    await app.updater.stop()
                await app.stop()
    else:
        # 3b. Setup not complete → start only web dashboard (setup wizard)
        logger.info("⚙️ Setup not complete. Starting Setup Wizard on web...")
        logger.info("🌐 Open http://localhost:8080 to configure the bot")
        await start_web_server(bot_app=None)


if __name__ == "__main__":
    asyncio.run(main())
