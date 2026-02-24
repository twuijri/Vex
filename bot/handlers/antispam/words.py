"""
Boter 2.0 - Blocked Words Handler
Manage blocked words list and check incoming messages
"""
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CallbackQueryHandler, ConversationHandler,
    MessageHandler, ContextTypes, filters
)

from bot.services.group_service import (
    get_managed_group, add_blocked_word, remove_blocked_word,
    list_blocked_words, clear_blocked_words
)
from bot.services.admin_service import get_admin_group_id

logger = logging.getLogger("boter.handlers.antispam.words")

ADDING_WORD, REMOVING_WORD = range(2)

async def blocked_words_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show blocked words menu"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    group = await get_managed_group(group_id)
    if not group:
        return

    words = await list_blocked_words(group_id)
    
    # Format the words list
    if words:
        words_list = "\n".join([f"• {w}" for w in words])
        text = f"🚫 **الكلمات المحظورة في مجموعة:** {group.group_name}\n\n{words_list}"
    else:
        text = f"🚫 **الكلمات المحظورة في مجموعة:** {group.group_name}\n\nلا يوجد أي كلمات محظورة حالياً."

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ إضافة كلمة", callback_data=f"add_word#{group_id}"),
            InlineKeyboardButton("➖ حذف كلمة", callback_data=f"remove_word#{group_id}"),
        ],
        [InlineKeyboardButton("🗑 حذف جميع الكلمات", callback_data=f"clear_words#{group_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"group_settings#{group_id}")],
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
    return ConversationHandler.END


async def start_add_word_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding a blocked word"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    context.user_data["editing_words_group"] = group_id

    await query.edit_message_text("📝 **أرسل الكلمة التي تريد حظرها:**", parse_mode="Markdown")
    return ADDING_WORD

async def save_add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the new blocked word"""
    group_id = context.user_data.get("editing_words_group")
    if not group_id:
        return ConversationHandler.END

    word = update.message.text.strip()
    result = await add_blocked_word(group_id, word)
    
    # Notify admin
    await update.message.reply_text(result, parse_mode="Markdown")
    return ConversationHandler.END

async def start_remove_word_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start removing a blocked word"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    context.user_data["editing_words_group"] = group_id

    await query.edit_message_text("📝 **أرسل الكلمة التي تريد إزالتها من الحظر:**", parse_mode="Markdown")
    return REMOVING_WORD

async def save_remove_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the removed blocked word"""
    group_id = context.user_data.get("editing_words_group")
    if not group_id:
        return ConversationHandler.END

    word = update.message.text.strip()
    result = await remove_blocked_word(group_id, word)
    
    # Notify admin
    await update.message.reply_text(result, parse_mode="Markdown")
    return ConversationHandler.END

async def clear_words_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all blocked words"""
    query = update.callback_query
    
    group_id = int(query.data.split("#")[1])
    result = await clear_blocked_words(group_id)
    
    # Show success alert and re-render menu (without modifying query.data)
    await query.answer(result, show_alert=True)
    await blocked_words_settings_callback(update, context)


def register_words_handlers(app: Application):
    """Register blocked words handlers"""
    # Just standard callback for settings menu
    app.add_handler(CallbackQueryHandler(blocked_words_settings_callback, pattern=r"^blocked_words#"))
    app.add_handler(CallbackQueryHandler(clear_words_callback, pattern=r"^clear_words#"))

    # Conversation for Adding word
    add_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_word_callback, pattern=r"^add_word#")],
        states={
            ADDING_WORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_add_word)],
        },
        fallbacks=[],
        per_message=False,
    )
    
    # Conversation for Removing word
    remove_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_remove_word_callback, pattern=r"^remove_word#")],
        states={
            REMOVING_WORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_remove_word)],
        },
        fallbacks=[],
        per_message=False,
    )
    
    app.add_handler(add_conv_handler)
    app.add_handler(remove_conv_handler)
