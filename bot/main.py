import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config_loader import load_config
from bot.services.db import db
from bot.handlers import groups, private, support, enforcement


# ==============================================================================
# 📄 File: bot/main.py
# 📝 Description: Main entry point for the Telegram Bot.
# 📝 الوصف: نقطة الدخول الرئيسية لبوت تيليجرام.
# ==============================================================================

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Boter 2025...")

    # 1. Load Config (Wait for Setup)
    # بما أن إعداد النظام قد يحدث بعد تشغيل البوت، ننتظر حتى توفر التوكن.
    config = load_config()
    while not config.bot_token:
        logger.warning("Bot Token not found! Waiting for Setup via Dashboard...")
        await asyncio.sleep(10)
        config = load_config()
    
    logger.info("Token found. Initializing Bot...")

    # 2. Connect to Database & Auto-Init
    # الاتصال بقاعدة البيانات وتهيئتها (إنشاء الفهارس)
    logger.info("Connecting to Database...")
    await db.connect()
    await db.init_database()

    from aiogram.client.default import DefaultBotProperties

    # 3. Initialize Bot & Dispatcher
    # 🔄 Sync Admins from Cloud to Local Config (Source of Truth: MongoDB)
    try:
        cloud_admins = await db.get_admins()
        if cloud_admins:
            import sqlite3
            import json
            import os
            
            # Update SQLite for legacy config_loader support
            db_path = "/app/data/config.db"
            if not os.path.exists(db_path):
                 db_path = os.path.join(os.getcwd(), "data", "config.db")
                 
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                new_json = json.dumps(cloud_admins)
                # Check exist
                cursor.execute("SELECT value FROM system_config WHERE key='telegram_admin_ids'")
                if cursor.fetchone():
                    cursor.execute("UPDATE system_config SET value=? WHERE key='telegram_admin_ids'", (new_json,))
                else:
                    cursor.execute("INSERT INTO system_config (key, value) VALUES ('telegram_admin_ids', ?)", (new_json,))
                conn.commit()
            
            logger.info(f"🔄 Synced {len(cloud_admins)} Admins from Cloud to Local Config.")
    except Exception as e:
        logger.error(f"⚠️ Failed to sync admins from cloud: {e}")

    # Reload config to apply changes
    config = load_config()

    from aiogram.client.default import DefaultBotProperties
    
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # 4. Register Handlers
    dp.include_router(support.router) # Support System (First priority)
    dp.include_router(groups.router)
    dp.include_router(enforcement.router) # Media/Words/Lock Checks
    dp.include_router(private.router)
    
    from bot.handlers import errors
    dp.include_router(errors.router) # Catch-all for errors
    
    # 5. Start Background Scheduler
    from bot.services.scheduler import scheduler_task
    asyncio.create_task(scheduler_task(bot))

    # 6. Start Polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info(f"✅ Bot started as @{(await bot.get_me()).username}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
