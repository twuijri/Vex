"""
Vex - Welcome Handler
Welcome message for new group members
"""
import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters,
)

from bot.services.group_service import (
    is_managed_group, get_welcome_config, update_welcome_message,
    toggle_welcome, get_managed_group,
)

logger = logging.getLogger("vex.handlers.antispam.welcome")

# Conversation states
EDITING_WELCOME = 1


async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message to new group members"""
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat or not message.new_chat_members:
        return

    if not await is_managed_group(chat.id):
        return

    config = await get_welcome_config(chat.id)
    if not config or not config.is_active or not config.message:
        return

    for member in message.new_chat_members:
        if member.is_bot:
            continue

        # Replace placeholders
        welcome_text = config.message.replace(
            "{name}", member.first_name or ""
        ).replace(
            "{username}", f"@{member.username}" if member.username else member.first_name or ""
        ).replace(
            "{group}", chat.title or ""
        )

        try:
            sent = await chat.send_message(welcome_text, parse_mode="Markdown")

            # Delete previous welcome message if configured
            if config.delete_last_message and config.last_message_id:
                try:
                    await context.bot.delete_message(chat.id, config.last_message_id)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Error sending welcome: {e}")


async def welcome_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show welcome settings"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    group = await get_managed_group(group_id)
    config = await get_welcome_config(group_id)

    if not group:
        return

    status = "✅" if config and config.is_active else "❌"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📃 عرض الترحيب", callback_data=f"show_welcome#{group_id}"),
            InlineKeyboardButton("📝 تعديل الترحيب", callback_data=f"edit_welcome#{group_id}"),
        ],
        [InlineKeyboardButton(
            f"♻️ حالة الترحيب : {status}",
            callback_data=f"toggle_welcome#{group_id}",
        )],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"group_settings#{group_id}")],
    ])

    await query.edit_message_text(
        f"🎊 **اعدادات الترحيب:** {group.group_name}",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def show_welcome_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current welcome message"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    config = await get_welcome_config(group_id)

    if config and config.message:
        text = f"📃 **رسالة الترحيب الحالية:**\n\n{config.message}"
    else:
        text = "❌ لا يوجد رسالة ترحيب"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"welcome_settings#{group_id}")],
    ])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def toggle_welcome_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle welcome on/off"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    await toggle_welcome(group_id)

    # Re-show welcome settings (without modifying query.data)
    await welcome_settings_callback(update, context)


async def edit_welcome_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing welcome message"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    context.user_data["editing_welcome_group"] = group_id

    await query.edit_message_text(
        "📝 **أرسل رسالة الترحيب الجديدة:**\n\n"
        "المتغيرات المتاحة:\n"
        "`{name}` - اسم العضو\n"
        "`{username}` - معرف العضو\n"
        "`{group}` - اسم المجموعة",
        parse_mode="Markdown",
    )
    return EDITING_WELCOME


async def save_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the new welcome message"""
    group_id = context.user_data.get("editing_welcome_group")
    if not group_id:
        return ConversationHandler.END

    result = await update_welcome_message(group_id, update.message.text)
    await update.message.reply_text(result, parse_mode="Markdown")
    return ConversationHandler.END


def register_welcome_handlers(app: Application):
    """Register welcome-related handlers"""
    # Welcome message on new members
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_members,
        ),
        group=5,
    )

    # Settings callbacks
    app.add_handler(CallbackQueryHandler(welcome_settings_callback, pattern=r"^welcome_settings#"))
    app.add_handler(CallbackQueryHandler(show_welcome_callback, pattern=r"^show_welcome#"))
    app.add_handler(CallbackQueryHandler(toggle_welcome_callback, pattern=r"^toggle_welcome#"))

    # Conversation for editing welcome
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_welcome_callback, pattern=r"^edit_welcome#")],
        states={
            EDITING_WELCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_welcome_message)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)
