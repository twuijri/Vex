"""
Boter 2.0 - Settings Handler
Main settings menu accessed via #الاعدادات in admin group
"""
import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes,
)

from bot.services.admin_service import is_admin, is_admin_group
from bot.services.group_service import (
    list_managed_groups, get_managed_group, deactivate_group,
    toggle_media_setting, get_group_media_setting,
)

logger = logging.getLogger("boter.handlers.admin.settings")

# Media type labels in Arabic
MEDIA_LABELS = {
    "text": "📝 النصوص",
    "document": "🗂 الملفات",
    "photo": "🎆 الصور",
    "video": "🎥 الفيديو",
    "voice": "🎙 تسجيلات الصوت",
    "audio": "🎶 الموسيقى",
    "sticker": "🌠 الملصقات",
    "video_note": "🎥 ملاحظات الفيديو",
    "gif": "🎭 الصور المتحركة",
    "forward": "🔄 اعادة التوجيه",
    "telegram_link": "📣 روابط تيليجرام",
    "link": "🔗 الروابط",
    "mobile": "📱 ارقام الجوال",
    "tag": "📍 التاقات",
    "hashtag": "#️⃣ الهاشتاق",
    "bots": "🤖 بوتات",
    "join_service": "🔻 اشعارات الدخول",
    "left_service": "🔺 اشعارات الخروج",
    "location": "🗺 المواقع",
    "games": "🎮 العاب",
}


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main settings entry point: #الاعدادات"""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    if not await is_admin(user.id):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 اعدادات المجموعات", callback_data="settings_groups")],
        [InlineKeyboardButton("🤖 اعدادات البوت", callback_data="settings_bot")],
        [InlineKeyboardButton("❌ الخروج من الإعدادات", callback_data="exit_settings")],
    ])
    await update.effective_message.reply_text(
        "⚙️ **الاعدادات**", reply_markup=keyboard, parse_mode="Markdown"
    )


async def settings_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of managed groups"""
    query = update.callback_query
    await query.answer()

    groups = await list_managed_groups()
    if not groups:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_main_settings")],
        ])
        await query.edit_message_text(
            "❌ لا يوجد مجموعات مفعلة", reply_markup=keyboard
        )
        return

    keyboard = []
    for g in groups:
        keyboard.append([
            InlineKeyboardButton(
                g.group_name,
                callback_data=f"group_settings#{g.telegram_group_id}",
            )
        ])
    keyboard.append([
        InlineKeyboardButton("🔙 رجوع", callback_data="back_main_settings")
    ])
    keyboard.append([
        InlineKeyboardButton("❌ الخروج", callback_data="exit_settings")
    ])

    await query.edit_message_text(
        "👥 **قائمة المجموعات المفعلة:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def group_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings for a specific group"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    group = await get_managed_group(group_id)
    if not group:
        await query.edit_message_text("⚠️ المجموعة غير مفعلة")
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌌 اعدادات الوسائط", callback_data=f"media_settings#{group_id}"),
            InlineKeyboardButton("🚫 الكلمات المحظورة", callback_data=f"blocked_words#{group_id}"),
        ],
        [
            InlineKeyboardButton("🔕 قفل المجموعة", callback_data=f"lock_settings#{group_id}"),
            InlineKeyboardButton("🏷 الصلاحيات", callback_data=f"perm_settings#{group_id}"),
        ],
        [
            InlineKeyboardButton("🎊 الترحيب", callback_data=f"welcome_settings#{group_id}"),
            InlineKeyboardButton("🚩 القوانين", callback_data=f"rules_settings#{group_id}"),
        ],
        [
            InlineKeyboardButton(
                "⛔️ حذف إدارة المجموعة",
                callback_data=f"deactivate_group#{group_id}",
            ),
        ],
        [InlineKeyboardButton("🔙 الرجوع للمجموعات", callback_data="settings_groups")],
        [InlineKeyboardButton("❌ الخروج", callback_data="exit_settings")],
    ])

    await query.edit_message_text(
        f"⚙️ **اعدادات المجموعة:** {group.group_name}",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def media_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show media settings for a group"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    group = await get_managed_group(group_id)
    if not group:
        return

    keyboard = []
    settings = group.media_settings or {}
    for key, label in MEDIA_LABELS.items():
        status = "✅" if settings.get(key, True) else "❌"
        keyboard.append([
            InlineKeyboardButton(status, callback_data=f"toggle_media#{group_id}#{key}"),
            InlineKeyboardButton(label, callback_data=f"noop"),
        ])
    keyboard.append([
        InlineKeyboardButton("🔙 رجوع", callback_data=f"group_settings#{group_id}")
    ])

    await query.edit_message_text(
        f"🌌 **اعدادات الوسائط:** {group.group_name}\n\n✅ : مسموح\n❌ : ممنوع",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def toggle_media_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle a media setting"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split("#")
    group_id = int(parts[1])
    media_type = parts[2]

    await toggle_media_setting(group_id, media_type)

    # Re-render the media settings
    group = await get_managed_group(group_id)
    if not group:
        return

    keyboard = []
    settings = group.media_settings or {}
    for key, label in MEDIA_LABELS.items():
        status = "✅" if settings.get(key, True) else "❌"
        keyboard.append([
            InlineKeyboardButton(status, callback_data=f"toggle_media#{group_id}#{key}"),
            InlineKeyboardButton(label, callback_data=f"noop"),
        ])
    keyboard.append([
        InlineKeyboardButton("🔙 رجوع", callback_data=f"group_settings#{group_id}")
    ])

    await query.edit_message_text(
        f"🌌 **اعدادات الوسائط:** {group.group_name}\n\n✅ : مسموح\n❌ : ممنوع",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def settings_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot settings menu"""
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 المحظورين", callback_data="blocked_settings")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main_settings")],
        [InlineKeyboardButton("❌ الخروج", callback_data="exit_settings")],
    ])
    await query.edit_message_text("⚙️ **اعدادات البوت**", reply_markup=keyboard, parse_mode="Markdown")


async def deactivate_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deactivate group management"""
    query = update.callback_query
    await query.answer()

    group_id = int(query.data.split("#")[1])
    result = await deactivate_group(group_id)
    await query.edit_message_text(result, parse_mode="Markdown")


async def back_main_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main settings"""
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 اعدادات المجموعات", callback_data="settings_groups")],
        [InlineKeyboardButton("🤖 اعدادات البوت", callback_data="settings_bot")],
        [InlineKeyboardButton("❌ الخروج من الإعدادات", callback_data="exit_settings")],
    ])
    await query.edit_message_text("⚙️ **الاعدادات**", reply_markup=keyboard, parse_mode="Markdown")


async def exit_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close settings"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("☑️ **تم اغلاق الاعدادات**", parse_mode="Markdown")


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """No-op callback for labels"""
    await update.callback_query.answer()


def register_settings_handlers(app: Application):
    """Register settings handlers"""
    app.add_handler(CommandHandler(["الاعدادات", "settings"], settings_command))
    app.add_handler(CallbackQueryHandler(settings_groups_callback, pattern=r"^settings_groups$"))
    app.add_handler(CallbackQueryHandler(group_settings_callback, pattern=r"^group_settings#"))
    app.add_handler(CallbackQueryHandler(media_settings_callback, pattern=r"^media_settings#"))
    app.add_handler(CallbackQueryHandler(toggle_media_callback, pattern=r"^toggle_media#"))
    app.add_handler(CallbackQueryHandler(settings_bot_callback, pattern=r"^settings_bot$"))
    app.add_handler(CallbackQueryHandler(deactivate_group_callback, pattern=r"^deactivate_group#"))
    app.add_handler(CallbackQueryHandler(back_main_settings_callback, pattern=r"^back_main_settings$"))
    app.add_handler(CallbackQueryHandler(exit_settings_callback, pattern=r"^exit_settings$"))
    app.add_handler(CallbackQueryHandler(noop_callback, pattern=r"^noop$"))
