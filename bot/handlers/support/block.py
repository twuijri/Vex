"""
Boter 2.0 - Block Handler
Block/unblock users from messaging the bot
"""
import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, filters,
)

from bot.services.admin_service import is_admin_group
from bot.services.user_service import (
    block_user, unblock_user, list_blocked_users,
    unblock_all_users, get_support_message_by_admin_msg_id,
)

logger = logging.getLogger("boter.handlers.support.block")


async def block_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Block a user - reply to their forwarded message with #حظر or /block"""
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat or not message.reply_to_message:
        await message.reply_text("⚠️ يجب الرد على رسالة المستخدم")
        return

    if not await is_admin_group(chat.id):
        return

    reply_to = message.reply_to_message
    user_id = None
    username = None

    if reply_to.forward_from:
        user_id = reply_to.forward_from.id
        username = reply_to.forward_from.username or "❌"
    elif reply_to.forward_date:
        support_msg = await get_support_message_by_admin_msg_id(reply_to.message_id)
        if support_msg:
            user_id = support_msg.user_telegram_id
            username = "❌"

    if user_id:
        result = await block_user(user_id)
        await message.reply_text(result, parse_mode="Markdown")
    else:
        await message.reply_text("⚠️ لم يتم التعرف على المستخدم")


async def unblock_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unblock a user"""
    message = update.effective_message
    if not message or not message.reply_to_message:
        await message.reply_text("⚠️ يجب الرد على رسالة المستخدم")
        return

    reply_to = message.reply_to_message
    user_id = None

    if reply_to.forward_from:
        user_id = reply_to.forward_from.id
    elif reply_to.forward_date:
        support_msg = await get_support_message_by_admin_msg_id(reply_to.message_id)
        if support_msg:
            user_id = support_msg.user_telegram_id

    if user_id:
        result = await unblock_user(user_id)
        await message.reply_text(result, parse_mode="Markdown")


async def show_blocked_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of blocked users"""
    users = await list_blocked_users()
    if not users:
        await update.effective_message.reply_text("❌ لا يوجد محظورين")
        return

    keyboard = []
    for u in users:
        name = f"{u.first_name}"
        uname = f"@{u.username}" if u.username else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{name} {uname}",
                callback_data=f"unblock#{u.telegram_id}",
            )
        ])
    keyboard.append([
        InlineKeyboardButton("🗑 حذف كل المحظورين", callback_data="unblock_all")
    ])

    await update.effective_message.reply_text(
        f"🚫 **المحظورين ({len(users)}):**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def unblock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unblock button click"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "unblock_all":
        result = await unblock_all_users()
        await query.edit_message_text(result, parse_mode="Markdown")
    elif data.startswith("unblock#"):
        user_id = int(data.split("#")[1])
        result = await unblock_user(user_id)
        await query.edit_message_text(result, parse_mode="Markdown")


def register_block_handlers(app: Application):
    """Register block-related handlers"""
    app.add_handler(CommandHandler(["حظر", "block"], block_user_command))
    app.add_handler(CommandHandler(["الغاء_حظر", "unblock"], unblock_user_command))
    app.add_handler(CommandHandler(["المحظورين", "blocked"], show_blocked_users))
    app.add_handler(CallbackQueryHandler(unblock_callback, pattern=r"^unblock"))
