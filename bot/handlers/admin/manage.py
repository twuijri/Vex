"""
Vex - Admin Management Handler
Add/remove/list bot admins
"""
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot.services.admin_service import add_admin, remove_admin, list_admins, is_admin

logger = logging.getLogger("vex.handlers.admin.manage")


async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add admin by replying to their message: #اضافة_مشرف"""
    message = update.effective_message
    user = update.effective_user
    if not message or not user:
        return

    if not await is_admin(user.id):
        return

    if not message.reply_to_message:
        await message.reply_text("⚠️ يجب الرد على رسالة العضو المراد رفعه مشرف")
        return

    reply = message.reply_to_message
    target = reply.forward_from or reply.from_user
    if not target:
        await message.reply_text("⚠️ لم يتم التعرف على العضو")
        return

    result = await add_admin(
        telegram_id=target.id,
        first_name=target.first_name,
        last_name=target.last_name,
        username=target.username,
    )
    await message.reply_text(result, parse_mode="Markdown")


async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove admin by replying: #ازالة_مشرف"""
    message = update.effective_message
    user = update.effective_user
    if not message or not user:
        return

    if not await is_admin(user.id):
        return

    if not message.reply_to_message:
        await message.reply_text("⚠️ يجب الرد على رسالة المشرف المراد ازالته")
        return

    reply = message.reply_to_message
    target = reply.forward_from or reply.from_user
    if not target:
        await message.reply_text("⚠️ لم يتم التعرف على العضو")
        return

    result = await remove_admin(target.id)
    await message.reply_text(result, parse_mode="Markdown")


async def list_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all bot admins: #المشرفين"""
    user = update.effective_user
    if not user or not await is_admin(user.id):
        return

    result = await list_admins()
    await update.effective_message.reply_text(result, parse_mode="Markdown")


def register_admin_handlers(app: Application):
    """Register admin management handlers"""
    app.add_handler(MessageHandler(filters.Regex(r"^[/#]?(اضافة_مشرف|add_admin)(?:@\S+)?(?:\s|$)"), add_admin_command))
    app.add_handler(MessageHandler(filters.Regex(r"^[/#]?(ازالة_مشرف|remove_admin)(?:@\S+)?(?:\s|$)"), remove_admin_command))
    app.add_handler(MessageHandler(filters.Regex(r"^[/#]?(المشرفين|admins)(?:@\S+)?(?:\s|$)"), list_admins_command))
