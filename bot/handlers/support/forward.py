"""
Vex - Forward Handler
Forwards user messages from private chat to admin group
"""
import logging

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from bot.services.admin_service import get_admin_group_id
from bot.services.user_service import is_user_blocked, save_support_message, register_user

logger = logging.getLogger("vex.handlers.support.forward")


async def forward_to_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forward private messages to admin group"""
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return

    # Check if user is blocked
    if await is_user_blocked(user.id):
        return

    # Register/update user
    await register_user(
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )

    # Get admin group
    admin_group_id = await get_admin_group_id()
    if not admin_group_id:
        await message.reply_text("🚫 التواصل متوقف حالياً")
        return

    try:
        # Forward the message to admin group
        forwarded = await message.forward(admin_group_id)

        # Track the message
        is_media = message.photo or message.video or message.document or \
                   message.voice or message.audio or message.sticker or \
                   message.video_note or message.animation
        content_preview = message.text or message.caption or \
                         ("ملف ميديا" if is_media else None)

        await save_support_message(
            telegram_id=user.id,
            admin_group_message_id=forwarded.message_id,
            content_preview=content_preview[:200] if content_preview else None,
            is_media=bool(is_media),
        )
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")
        await message.reply_text("⚠️ حدث خطأ في إرسال رسالتك")


def register_forward_handlers(app: Application):
    """Register forward handlers"""
    # Handle all private messages except commands
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND,
            forward_to_admins,
        ),
        group=1,  # Lower priority than commands
    )
