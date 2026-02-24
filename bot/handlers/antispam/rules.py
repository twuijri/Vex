"""
Vex - Rules Handler
Group rules management
"""
import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, ContextTypes, filters,
)

from bot.services.group_service import (
    get_rules_config, update_rules_message, toggle_rules,
    get_managed_group,
)

logger = logging.getLogger("vex.handlers.antispam.rules")

EDITING_RULES = 1


async def show_rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show group rules: /rules or #القوانين"""
    chat = update.effective_chat
    if not chat:
        return

    # If in private with deep link
    if chat.type == "private" and context.args:
        group_id = int(context.args[0].replace("rules_", ""))
    else:
        group_id = chat.id

    config = await get_rules_config(group_id)
    if config and config.is_active and config.message:
        await update.effective_message.reply_text(config.message, parse_mode="Markdown")
    else:
        await update.effective_message.reply_text("❌ لا يوجد قوانين")


async def rules_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show rules settings"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    group = await get_managed_group(group_id)
    config = await get_rules_config(group_id)
    if not group:
        return

    status = "✅" if config and config.is_active else "❌"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📃 عرض القوانين", callback_data=f"show_rules#{group_id}"),
            InlineKeyboardButton("📝 تعديل القوانين", callback_data=f"edit_rules#{group_id}"),
        ],
        [InlineKeyboardButton(
            f"♻️ حالة القوانين : {status}",
            callback_data=f"toggle_rules#{group_id}",
        )],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"group_settings#{group_id}")],
    ])

    await query.edit_message_text(
        f"🚩 **اعدادات القوانين:** {group.group_name}",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def show_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current rules"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    config = await get_rules_config(group_id)

    text = f"📃 **القوانين الحالية:**\n\n{config.message}" if config and config.message else "❌ لا يوجد قوانين"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"rules_settings#{group_id}")],
    ])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def toggle_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle rules on/off"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    await toggle_rules(group_id)

    # Re-show rules settings (without modifying query.data)
    await rules_settings_callback(update, context)


async def edit_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing rules"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    context.user_data["editing_rules_group"] = group_id

    await query.edit_message_text("📝 **أرسل القوانين الجديدة:**", parse_mode="Markdown")
    return EDITING_RULES


async def save_rules_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the new rules"""
    group_id = context.user_data.get("editing_rules_group")
    if not group_id:
        return ConversationHandler.END

    result = await update_rules_message(group_id, update.message.text)
    await update.message.reply_text(result, parse_mode="Markdown")
    return ConversationHandler.END


def register_rules_handlers(app: Application):
    """Register rules handlers"""
    app.add_handler(MessageHandler(filters.Regex(r"^[/#]?(القوانين|rules)(?:@\S+)?(?:\s|$)"), show_rules_command))
    app.add_handler(CallbackQueryHandler(rules_settings_callback, pattern=r"^rules_settings#"))
    app.add_handler(CallbackQueryHandler(show_rules_callback, pattern=r"^show_rules#"))
    app.add_handler(CallbackQueryHandler(toggle_rules_callback, pattern=r"^toggle_rules#"))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_rules_callback, pattern=r"^edit_rules#")],
        states={
            EDITING_RULES: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_rules_message)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)
