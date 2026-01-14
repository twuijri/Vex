#!/usr/bin/env python3
"""
Quick health check script for CoffeeBot
اختبار سريع لتأكد من أن كل شيء يعمل
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def check_config():
    """Check configuration"""
    print("🔍 Checking configuration...")
    try:
        from bot.core.config import config
        
        checks = [
            ("BOT_TOKEN", config.BOT_TOKEN[:20] + "..."),
            ("MONGO_URI", config.MONGO_URI.split("://")[1][:30] + "..."),
            ("MONGO_DB_NAME", config.MONGO_DB_NAME),
            ("LOG_LEVEL", config.LOG_LEVEL),
        ]
        
        for name, value in checks:
            status = "✅" if value else "❌"
            print(f"  {status} {name}: {value}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

async def check_database():
    """Check database connection"""
    print("\n🗄️  Checking MongoDB connection...")
    try:
        from bot.core.config import config
        from motor.motor_asyncio import AsyncIOMotorClient
        
        client = AsyncIOMotorClient(config.MONGO_URI)
        await client.admin.command('ping')
        
        # Check database
        db = client[config.MONGO_DB_NAME]
        collections = await db.list_collection_names()
        
        print(f"  ✅ Connected to: {config.MONGO_DB_NAME}")
        print(f"  📊 Collections: {len(collections)} found")
        if collections:
            print(f"     - {', '.join(collections[:5])}")
        
        client.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

async def check_bot():
    """Check bot token validity"""
    print("\n🤖 Checking bot token...")
    try:
        from bot.core.config import config
        from aiogram import Bot
        
        bot = Bot(token=config.BOT_TOKEN)
        me = await bot.get_me()
        
        print(f"  ✅ Bot: @{me.username}")
        print(f"     ID: {me.id}")
        print(f"     Name: {me.first_name}")
        
        await bot.session.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

async def main():
    """Run all checks"""
    print("=" * 50)
    print("CoffeeBot Health Check 🏥")
    print("=" * 50 + "\n")
    
    results = []
    
    results.append(await check_config())
    results.append(await check_database())
    results.append(await check_bot())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✅ All checks passed! Bot is ready to run")
        print("=" * 50)
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
