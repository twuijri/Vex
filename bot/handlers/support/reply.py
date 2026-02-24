"""
Boter 2.0 - Reply Handler
Handles admin replies to user messages in admin group
"""
import logging

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from bot.services.admin_service import is_admin_group
from bot.services.user_service import get_support_message_by_admin_msg_id

logger = logging.getLogger("boter.handlers.support.reply")


async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    When an admin replies to a forwarded message in the admin group,
    copy the admin's message to the original user
    """
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat or not message.reply_to_message:
        return

    # Must be in admin group
    if not await is_admin_group(chat.id):
        return

    # Skip commands
    if message.text and message.text.startswith(("/", "#")):
        return

    reply_to = message.reply_to_message
    user_id = None

    # In API 7.0+, forward_from is replaced by forward_origin
    if getattr(reply_to, "forward_origin", None):
        if reply_to.forward_origin.type == "user":
            user_id = reply_to.forward_origin.sender_user.id
        else: # "hidden_user" or others
            # Look up from our tracking database
            support_msg = await get_support_message_by_admin_msg_id(reply_to.message_id)
            if support_msg:
                user_id = support_msg.user_telegram_id

    if not user_id:
        return

    try:
        # Copy the admin's reply to the user
        await message.copy(user_id)
    except Exception as e:
        error_msg = str(e)
        if "blocked" in error_msg.lower() or "Forbidden" in error_msg:
            await message.reply_text("⚠️ المستخدم قام بحظر البوت")
        else:
            logger.error(f"Error replying to user {user_id}: {e}")
            await message.reply_text("⚠️ حدث خطأ في إرسال الرد")


def register_reply_handlers(app: Application):
    """Register reply handlers"""
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.REPLY & ~filters.COMMAND,
            reply_to_user,
        ),
        group=2,
    )
