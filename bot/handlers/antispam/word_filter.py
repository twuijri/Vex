"""
Vex - Word Filter Handler
Checks messages for blocked words and deletes them
"""
import logging

from telegram import Update, ChatMemberAdministrator, ChatMemberOwner
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from bot.services.group_service import is_managed_group, check_blocked_word
from bot.services.admin_service import is_admin

logger = logging.getLogger("vex.handlers.antispam.word_filter")


async def filter_blocked_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if a message contains blocked words"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not chat or not user:
        return

    # Skip if not a managed group
    if not await is_managed_group(chat.id):
        return

    # Skip admins
    if await is_admin(user.id):
        return

    # Skip group admins
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if isinstance(member, (ChatMemberAdministrator, ChatMemberOwner)):
            return
    except Exception:
        pass

    # Get text to check
    text = message.text or message.caption
    if not text:
        return

    # Check against blocked words
    if await check_blocked_word(chat.id, text):
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Could not delete blocked word message: {e}")


def register_word_filter_handlers(app: Application):
    """Register word filter handlers"""
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
            filter_blocked_words,
        ),
        group=11,
    )
