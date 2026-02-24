"""
Boter 2.0 - Start Handler
Handles /start command in private and group chats
"""
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from bot.services.user_service import register_user
from bot.services.admin_service import is_admin, get_admin_group_id, set_admin_group
from bot.services.group_service import activate_group

logger = logging.getLogger("boter.handlers.start")

WELCOME_USER = "اهلا بك في البوت 😄\nأرسل رسالتك وسيتم توجيهها للمشرفين"
WELCOME_ADMIN = "اهلا بك في لوحة التحكم 😄\nأرسل #الاعدادات للوصول للإعدادات"


async def start_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start in private chat"""
    user = update.effective_user
    if not user:
        return

    # Register user
    await register_user(
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )

    # Check if admin
    if await is_admin(user.id):
        await update.message.reply_text(WELCOME_ADMIN, parse_mode="Markdown")
    else:
        await update.message.reply_text(WELCOME_USER, parse_mode="Markdown")


async def start_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start in groups - used for activating group management"""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    # Check if this is an activation request (deep link)
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith("addGroup"):
            # Only admins can activate groups
            if not await is_admin(user.id):
                return

            result = await activate_group(
                telegram_group_id=chat.id,
                group_name=chat.title or "Unknown",
                group_type=str(chat.type),
                activated_by=user.id,
            )

            # Notify admin group
            admin_group_id = await get_admin_group_id()
            if admin_group_id:
                try:
                    await context.bot.send_message(
                        admin_group_id, f"**{result}**\n📎 {chat.title}",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass

            await update.message.reply_text(result, parse_mode="Markdown")


async def set_admin_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle #مجموعة_المشرفين or /مجموعة_المشرفين
    Sets current group as the admin control group
    """
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    if chat.type == "private":
        await update.message.reply_text("⚠️ هذا الأمر يعمل فقط في المجموعات")
        return

    if not await is_admin(user.id):
        return

    result = await set_admin_group(
        telegram_group_id=chat.id,
        group_name=chat.title or "Unknown",
    )
    await update.message.reply_text(result, parse_mode="Markdown")


def register_start_handlers(app: Application):
    """Register start-related handlers"""
    app.add_handler(CommandHandler("start", start_private, filters=~_group_filter()))
    app.add_handler(CommandHandler("start", start_group, filters=_group_filter()))
    app.add_handler(
        CommandHandler(
            ["مجموعة_المشرفين", "set_admin_group"],
            set_admin_group_command,
        )
    )


def _group_filter():
    from telegram.ext import filters
    return filters.ChatType.GROUPS
