"""
Dynamic keyboard builders for inline keyboards
"""
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils.constants import (
    EMOJI_CHECK, EMOJI_CROSS, EMOJI_BACK, EMOJI_EXIT,
    MEDIA_NAMES, PERMISSION_NAMES, CB_BACK, CB_EXIT
)


def build_main_settings_keyboard() -> InlineKeyboardMarkup:
    """Build main settings menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="⚙️ إعدادات المجموعات",
            callback_data="settings:groups_list"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👨‍💼 إعدادات البوت",
            callback_data="settings:bot"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗄️ قاعدة البيانات",
            callback_data="db_settings:view"
        )
    )
    
    return builder.as_markup()


def build_bot_settings_keyboard() -> InlineKeyboardMarkup:
    """Build bot settings keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🗑 حذف رسالة تم إرسالها",
            callback_data="bot_settings:delete_messages"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🚫 المحظورين",
            callback_data="bot_settings:blocked_users"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_BACK} الرجوع",
            callback_data=f"{CB_BACK}:main"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_EXIT} الخروج من الإعدادات",
            callback_data=CB_EXIT
        )
    )
    
    return builder.as_markup()


def build_groups_list_keyboard(groups: List[dict], bot_username: str) -> InlineKeyboardMarkup:
    """
    Build groups list keyboard
    
    Args:
        groups: List of group dicts with 'chat_id' and 'chat_title'
        bot_username: Bot username for add group URL
    """
    builder = InlineKeyboardBuilder()
    
    # Add group buttons
    for group in groups:
        builder.row(
            InlineKeyboardButton(
                text=group['chat_title'],
                callback_data=f"group:{group['chat_id']}"
            )
        )
    
    # Add new group button
    builder.row(
        InlineKeyboardButton(
            text="➕ إضافة مجموعة جديدة",
            url=f"https://t.me/{bot_username}?startgroup=new"
        )
    )
    
    # Navigation buttons
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_BACK} الرجوع",
            callback_data=f"{CB_BACK}:main"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_EXIT} الخروج",
            callback_data=CB_EXIT
        )
    )
    
    return builder.as_markup()


def build_group_settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Build group settings keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🌌 إعدادات الوسائط",
            callback_data=f"group_settings:media:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🚫 الكلمات المحظورة",
            callback_data=f"group_settings:blocked_words:{chat_id}"
        ),
        InlineKeyboardButton(
            text="✅ الكلمات المسموح بها",
            callback_data=f"group_settings:allowed_words:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔕 قفل المجموعة",
            callback_data=f"group_settings:silent:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎊 الترحيب",
            callback_data=f"group_settings:welcome:{chat_id}"
        ),
        InlineKeyboardButton(
            text="🚩 القوانين",
            callback_data=f"group_settings:rules:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚠️ التحذيرات",
            callback_data=f"group_settings:warn:{chat_id}"
        ),
        InlineKeyboardButton(
            text="🌊 منع التكرار",
            callback_data=f"group_settings:flood:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔐 التحقق (Captcha)",
            callback_data=f"group_settings:captcha:{chat_id}"
        ),
        InlineKeyboardButton(
            text="🌐 اللغات",
            callback_data=f"group_settings:language:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⛔️ حذف إدارة المجموعة",
            callback_data=f"group_settings:deactivate:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_BACK} الرجوع",
            callback_data=f"{CB_BACK}:groups_list"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_EXIT} الخروج",
            callback_data=CB_EXIT
        )
    )
    
    return builder.as_markup()


def build_media_settings_keyboard(chat_id: int, media_filters: dict) -> InlineKeyboardMarkup:
    """
    Build media settings keyboard with toggle buttons
    
    Args:
        chat_id: Group chat ID
        media_filters: Dict of media types and their status (bool)
    """
    builder = InlineKeyboardBuilder()
    
    # Create rows of 2 buttons each
    media_types = list(MEDIA_NAMES.keys())
    
    for i in range(0, len(media_types), 2):
        row_buttons = []
        
        for j in range(2):
            if i + j < len(media_types):
                media_type = media_types[i + j]
                status = EMOJI_CHECK if media_filters.get(media_type, True) else EMOJI_CROSS
                
                row_buttons.append(
                    InlineKeyboardButton(
                        text=f"{status}",
                        callback_data=f"media:toggle:{chat_id}:{media_type}"
                    )
                )
                row_buttons.append(
                    InlineKeyboardButton(
                        text=MEDIA_NAMES[media_type],
                        callback_data=f"media:info:{media_type}"
                    )
                )
        
        builder.row(*row_buttons)
    
    # Navigation
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_BACK} الرجوع",
            callback_data=f"{CB_BACK}:group:{chat_id}"
        )
    )
    
    return builder.as_markup()


def build_words_settings_keyboard(chat_id: int, words_type: str, active: bool) -> InlineKeyboardMarkup:
    """
    Build blocked/allowed words settings keyboard
    
    Args:
        chat_id: Group chat ID
        words_type: "blocked" or "allowed"
        active: Whether the system is active
    """
    builder = InlineKeyboardBuilder()
    
    status = EMOJI_CHECK if active else EMOJI_CROSS
    emoji = "🚫" if words_type == "blocked" else "✅"
    
    builder.row(
        InlineKeyboardButton(
            text=f"♻️ حالة النظام: {status}",
            callback_data=f"words:toggle_status:{chat_id}:{words_type}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"📃 عرض الكلمات",
            callback_data=f"words:list:{chat_id}:{words_type}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="➕ إضافة كلمة",
            callback_data=f"words:add:{chat_id}:{words_type}"
        ),
        InlineKeyboardButton(
            text="➖ حذف كلمة",
            callback_data=f"words:remove:{chat_id}:{words_type}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚠️ حذف جميع الكلمات",
            callback_data=f"words:remove_all:{chat_id}:{words_type}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_BACK} الرجوع",
            callback_data=f"{CB_BACK}:group:{chat_id}"
        )
    )
    
    return builder.as_markup()


def build_silent_settings_keyboard(chat_id: int, is_locked: bool) -> InlineKeyboardMarkup:
    """Build silent mode settings keyboard"""
    builder = InlineKeyboardBuilder()
    
    lock_emoji = "🔕" if is_locked else "🔔"
    lock_text = "مقفولة" if is_locked else "مفتوحة"
    
    builder.row(
        InlineKeyboardButton(
            text=f"🔘 حالة المجموعة: {lock_emoji} {lock_text}",
            callback_data=f"silent:toggle:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📆 قفل يومي",
            callback_data=f"silent:daily:{chat_id}"
        ),
        InlineKeyboardButton(
            text="⏰ قفل مؤقت",
            callback_data=f"silent:timer:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏷 ضبط الصلاحيات",
            callback_data=f"silent:permissions:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📨 ضبط رسائل القفل",
            callback_data=f"silent:messages:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_BACK} الرجوع",
            callback_data=f"{CB_BACK}:group:{chat_id}"
        )
    )
    
    return builder.as_markup()


def build_permissions_keyboard(chat_id: int, permissions: dict) -> InlineKeyboardMarkup:
    """Build permissions settings keyboard"""
    builder = InlineKeyboardBuilder()
    
    for perm_key, perm_name in PERMISSION_NAMES.items():
        status = EMOJI_CHECK if permissions.get(perm_key, True) else EMOJI_CROSS
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {perm_name}",
                callback_data=f"permissions:toggle:{chat_id}:{perm_key}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_BACK} الرجوع",
            callback_data=f"{CB_BACK}:silent:{chat_id}"
        )
    )
    
    return builder.as_markup()


def build_welcome_settings_keyboard(chat_id: int, active: bool) -> InlineKeyboardMarkup:
    """Build welcome settings keyboard"""
    builder = InlineKeyboardBuilder()
    
    status = EMOJI_CHECK if active else EMOJI_CROSS
    
    builder.row(
        InlineKeyboardButton(
            text=f"♻️ حالة الترحيب: {status}",
            callback_data=f"welcome:toggle:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📃 عرض الترحيب",
            callback_data=f"welcome:show:{chat_id}"
        ),
        InlineKeyboardButton(
            text="📝 تعديل الترحيب",
            callback_data=f"welcome:edit:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="➕ إضافة زر",
            callback_data=f"welcome:add_button:{chat_id}"
        ),
        InlineKeyboardButton(
            text="🗑 حذف الأزرار",
            callback_data=f"welcome:clear_buttons:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_BACK} الرجوع",
            callback_data=f"{CB_BACK}:group:{chat_id}"
        )
    )
    
    return builder.as_markup()


def build_rules_settings_keyboard(chat_id: int, active: bool) -> InlineKeyboardMarkup:
    """Build rules settings keyboard"""
    builder = InlineKeyboardBuilder()
    
    status = EMOJI_CHECK if active else EMOJI_CROSS
    
    builder.row(
        InlineKeyboardButton(
            text=f"♻️ حالة القوانين: {status}",
            callback_data=f"rules:toggle:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📃 عرض القوانين",
            callback_data=f"rules:show:{chat_id}"
        ),
        InlineKeyboardButton(
            text="📝 تعديل القوانين",
            callback_data=f"rules:edit:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔐 الصلاحيات",
            callback_data=f"rules:permissions:{chat_id}"
        ),
        InlineKeyboardButton(
            text="📍 مكان الإرسال",
            callback_data=f"rules:place:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="➕ إضافة زر",
            callback_data=f"rules:add_button:{chat_id}"
        ),
        InlineKeyboardButton(
            text="🗑 حذف الأزرار",
            callback_data=f"rules:clear_buttons:{chat_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{EMOJI_BACK} الرجوع",
            callback_data=f"{CB_BACK}:group:{chat_id}"
        )
    )
    
    return builder.as_markup()


def build_confirmation_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    """Build confirmation keyboard for dangerous actions"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ نعم، تأكيد",
            callback_data=f"confirm:{action}:{data}"
        ),
        InlineKeyboardButton(
            text="❌ إلغاء",
            callback_data=f"cancel:{action}"
        )
    )
    
    return builder.as_markup()


def build_cancel_keyboard() -> InlineKeyboardMarkup:
    """Build simple cancel keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="❌ إلغاء",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()
