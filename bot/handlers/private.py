from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from bot.services.db import db
from bot.config_loader import load_config


# ==============================================================================
# 📄 File: bot/handlers/private.py
# 📝 Description: Handles private messages and user initialization.
# 📝 الوصف: معالجة الرسائل الخاصة وتهيئة المستخدمين.
# ==============================================================================

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handle /start command in private chats.
    🔹 معالجة أمر البداية في المحادثات الخاصة.
    """
    user = message.from_user
    
    # 1. Save User to Database | حفظ المستخدم في قاعدة البيانات
    user_data = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "language_code": user.language_code,
        "is_bot": user.is_bot,
        "last_seen": message.date
    }
    await db.add_or_update_user(user_data)
    
    # 2. Check if Admin | التحقق إذا كان مديراً

    config = load_config()
    is_admin = user.id in config.telegram_admin_ids
    
    # 3. Reply | الرد
    if is_admin:
        await message.answer(
            f"👋 مرحباً بك يا قائد! ({user.first_name})\n\n"
            "أنت مسجل كمدير للبوت ✅.\n"
            "نظامك يعمل بشكل جيد وقاعدة البيانات متصلة."
        )
    else:
        await message.answer(
            f"👋 مرحباً {user.first_name}!\n\n"
            "أنا بوت إدارة المجموعات 🛡️.\n"
            "أضفني إلى مجموعتك وسأساعدك في إدارتها."
        )
