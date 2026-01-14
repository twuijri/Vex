#!/usr/bin/env python3
"""نقطة البدء - لوحة setup أول مرة"""
import asyncio
import sys
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "data" / "config.json"

def main():
    if not CONFIG_FILE.exists():
        # لوحة الإعداد
        import subprocess
        subprocess.run([sys.executable, "-m", "uvicorn", "bot.setup:app",
                       "--host", "0.0.0.0", "--port", "8000"])
    else:
        # البوت
        from bot.core.bot import create_bot
        try:
            bot_manager = create_bot()
            asyncio.run(bot_manager.start())
        except KeyboardInterrupt:
            print("\nتم الإيقاف")

if __name__ == "__main__":
    main()
