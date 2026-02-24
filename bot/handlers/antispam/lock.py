"""
Vex - Lock Handler
Group lock/unlock with timer and schedule support
"""
import logging
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from telegram.ext import (
    Application, CallbackQueryHandler, ConversationHandler,
    MessageHandler, ContextTypes, filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.services.group_service import (
    get_managed_group, get_schedule_config, set_lock_schedule,
    clear_lock_schedule, get_permission_settings, toggle_permission_setting,
)
from bot.services.admin_service import is_admin_group

logger = logging.getLogger("vex.handlers.antispam.lock")

# Global scheduler
scheduler = AsyncIOScheduler(timezone="Asia/Riyadh")
scheduler.start()

# Permission labels
PERM_LABELS = {
    "can_send_messages": "✉️ إرسال الرسائل",
    "can_send_audios": "🎵 الصوتيات",
    "can_send_documents": "📄 الملفات",
    "can_send_photos": "🖼 الصور",
    "can_send_videos": "🎥 الفيديو",
    "can_send_video_notes": "📹 الملاحظات المرئية",
    "can_send_voice_notes": "🎙 البصمات الصوتية",
    "can_send_other_messages": "🖼 الملصقات والمتحركة",
    "can_send_polls": "📊 الاستفتاءات",
    "can_add_web_page_previews": "🔍 الروابط",
    "can_change_info": "📝 تغيير معلومات المجموعة",
    "can_invite_users": "👥 إضافة الأعضاء",
    "can_pin_messages": "📌 تثبيت الرسائل",
}


async def close_group(bot, chat_id, message_text=None):
    """Lock a group (disable all sending)"""
    try:
        await bot.set_chat_permissions(chat_id, ChatPermissions())
        if message_text:
            await bot.send_message(chat_id, message_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error closing group {chat_id}: {e}")


async def open_group(bot, chat_id, message_text=None):
    """Unlock a group (restore permissions from DB)"""
    try:
        perms = await get_permission_settings(chat_id)
        await bot.set_chat_permissions(
            chat_id,
            ChatPermissions(
                can_send_messages=perms.get("can_send_messages", True),
                can_send_audios=perms.get("can_send_audios", True),
                can_send_documents=perms.get("can_send_documents", True),
                can_send_photos=perms.get("can_send_photos", True),
                can_send_videos=perms.get("can_send_videos", True),
                can_send_video_notes=perms.get("can_send_video_notes", True),
                can_send_voice_notes=perms.get("can_send_voice_notes", True),
                can_send_other_messages=perms.get("can_send_other_messages", True),
                can_send_polls=perms.get("can_send_polls", True),
                can_add_web_page_previews=perms.get("can_add_web_page_previews", True),
                can_change_info=perms.get("can_change_info", True),
                can_invite_users=perms.get("can_invite_users", True),
                can_pin_messages=perms.get("can_pin_messages", True),
            ),
        )
        if message_text:
            await bot.send_message(chat_id, message_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error opening group {chat_id}: {e}")


async def lock_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show lock settings for a group"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    group = await get_managed_group(group_id)
    if not group:
        return

    # Get current lock status
    try:
        chat = await context.bot.get_chat(group_id)
        is_locked = not chat.permissions.can_send_messages if chat.permissions else False
    except Exception:
        is_locked = False

    lock_status = "🔕" if is_locked else "🔔"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"🔘 حالة القفل : {lock_status}",
            callback_data=f"toggle_lock#{group_id}",
        )],
        [
            InlineKeyboardButton("📆 قفل يومي", callback_data=f"daily_lock#{group_id}"),
            InlineKeyboardButton("⏰ قفل مؤقت", callback_data=f"timer_lock#{group_id}"),
        ],
        [InlineKeyboardButton(
            "🏷 ضبط الصلاحيات",
            callback_data=f"perm_settings#{group_id}",
        )],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"group_settings#{group_id}")],
    ])

    await query.edit_message_text(
        f"🔕 **اعدادات قفل المجموعة:** {group.group_name}",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def toggle_lock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle group lock/unlock"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])

    try:
        chat = await context.bot.get_chat(group_id)
        is_locked = not chat.permissions.can_send_messages if chat.permissions else False

        if is_locked:
            await open_group(context.bot, group_id)
        else:
            await close_group(context.bot, group_id)

        # Re-show lock settings (without modifying query.data)
        await lock_settings_callback(update, context)
    except Exception as e:
        logger.error(f"Error toggling lock: {e}")


async def perm_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show permission settings for a group"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    perms = await get_permission_settings(group_id)

    keyboard = []
    for key, label in PERM_LABELS.items():
        status = "✅" if perms.get(key, True) else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{label}  {status}",
                callback_data=f"toggle_perm#{group_id}#{key}",
            )
        ])
    keyboard.append([
        InlineKeyboardButton("🔙 رجوع", callback_data=f"lock_settings#{group_id}")
    ])

    await query.edit_message_text(
        f"🏷 **ضبط الصلاحيات:**\n\n✅ : مسموح\n❌ : ممنوع",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def toggle_perm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle a permission setting"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split("#")
    group_id = int(parts[1])
    perm_type = parts[2]

    await toggle_permission_setting(group_id, perm_type)

    # Re-render permissions (without modifying query.data)
    await perm_settings_callback(update, context)


def register_lock_handlers(app: Application):
    """Register lock-related handlers"""
    app.add_handler(CallbackQueryHandler(lock_settings_callback, pattern=r"^lock_settings#"))
    app.add_handler(CallbackQueryHandler(toggle_lock_callback, pattern=r"^toggle_lock#"))
    app.add_handler(CallbackQueryHandler(perm_settings_callback, pattern=r"^perm_settings#"))
    app.add_handler(CallbackQueryHandler(toggle_perm_callback, pattern=r"^toggle_perm#"))


async def restore_schedules(bot):
    """Restore scheduled jobs from database on bot startup"""
    from bot.services.group_service import list_managed_groups

    groups = await list_managed_groups()
    for group in groups:
        schedule = group.schedule if hasattr(group, 'schedule') else None
        if not schedule:
            continue

        group_id = group.telegram_group_id

        if schedule.lock_time:
            hour, minute = schedule.lock_time.split(":")
            scheduler.add_job(
                close_group, 'cron',
                hour=int(hour), minute=int(minute),
                args=[bot, group_id, schedule.lock_message],
                id=f"lock_{group_id}",
                replace_existing=True,
            )

        if schedule.unlock_time:
            hour, minute = schedule.unlock_time.split(":")
            scheduler.add_job(
                open_group, 'cron',
                hour=int(hour), minute=int(minute),
                args=[bot, group_id, schedule.unlock_message],
                id=f"unlock_{group_id}",
                replace_existing=True,
            )
