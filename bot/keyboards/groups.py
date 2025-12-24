from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """
    Main Settings Dashboard Keyboard.
    🔹 لوحة تحكم الإعدادات الرئيسية.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📷 الوسائط", callback_data=f"settings_media:{chat_id}"),
            InlineKeyboardButton(text="🚫 المحظورات", callback_data=f"settings_banned:{chat_id}")
        ],
        [
            InlineKeyboardButton(text="👋 الترحيب", callback_data=f"settings_welcome:{chat_id}"),
            InlineKeyboardButton(text="🔇 الوضع الصامت", callback_data=f"settings_lock:{chat_id}")
        ],
        [
            InlineKeyboardButton(text="📜 القوانين", callback_data=f"settings_rules:{chat_id}"),
            InlineKeyboardButton(text="🏳️ القائمة البيضاء", callback_data=f"settings_whitelist:{chat_id}")
        ],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="close_settings")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_media_settings_keyboard(chat_id: int, current_settings: dict) -> InlineKeyboardMarkup:
    """
    Media Permissions Settings.
    🔹 إعدادات وسائط المجموعة.
    """
    media = current_settings.get("media", {}) # Updated key
    
    # Helper to get status emoji
    def status(key):
        return "✅" if media.get(key, True) else "❌"

    keyboard = [
        # --- Content Types ---
        [
            InlineKeyboardButton(text=f"{status('text')} النصوص", callback_data=f"toggle_media:{chat_id}:text"),
            InlineKeyboardButton(text=f"{status('link')} روابط عامة", callback_data=f"toggle_media:{chat_id}:link")
        ],
        [
            InlineKeyboardButton(text=f"{status('photo')} صور", callback_data=f"toggle_media:{chat_id}:photo"),
            InlineKeyboardButton(text=f"{status('video')} فيديو", callback_data=f"toggle_media:{chat_id}:video")
        ],
        [
            InlineKeyboardButton(text=f"{status('sticker')} ملصقات", callback_data=f"toggle_media:{chat_id}:sticker"),
            InlineKeyboardButton(text=f"{status('audio')} صوتيات (Music)", callback_data=f"toggle_media:{chat_id}:audio")
        ],
        [
            InlineKeyboardButton(text=f"{status('voice')} بصمات", callback_data=f"toggle_media:{chat_id}:voice"),
            InlineKeyboardButton(text=f"{status('video_note')} فيديو دائري", callback_data=f"toggle_media:{chat_id}:video_note")
        ],
        [
            InlineKeyboardButton(text=f"{status('document')} ملفات", callback_data=f"toggle_media:{chat_id}:document"),
            InlineKeyboardButton(text=f"{status('animation')} متحركة (GIF)", callback_data=f"toggle_media:{chat_id}:animation")
        ],
        # --- Filters ---
        [
            InlineKeyboardButton(text=f"{status('forward')} إعادة توجيه", callback_data=f"toggle_media:{chat_id}:forward"),
            InlineKeyboardButton(text=f"{status('mention')} منشن (@)", callback_data=f"toggle_media:{chat_id}:mention")
        ],
        [
            InlineKeyboardButton(text=f"{status('hashtag')} هاشتاق (#)", callback_data=f"toggle_media:{chat_id}:hashtag"),
            InlineKeyboardButton(text=f"{status('telegram_link')} روابط تيليجرام", callback_data=f"toggle_media:{chat_id}:telegram_link")
        ],
        # --- Interactive ---
        [
            InlineKeyboardButton(text=f"{status('poll')} تصويت", callback_data=f"toggle_media:{chat_id}:poll"),
            InlineKeyboardButton(text=f"{status('game')} ألعاب", callback_data=f"toggle_media:{chat_id}:game")
        ],
        [
            InlineKeyboardButton(text=f"{status('location')} مواقع", callback_data=f"toggle_media:{chat_id}:location"),
            InlineKeyboardButton(text=f"{status('contact')} جهات اتصال", callback_data=f"toggle_media:{chat_id}:contact")
        ],
        # --- Notifications & Bots ---
        [
            InlineKeyboardButton(text=f"{status('bot_invite')} إضافة بوتات", callback_data=f"toggle_media:{chat_id}:bot_invite")
        ],
        [
            InlineKeyboardButton(text=f"{status('entry_msg')} إشعار دخول", callback_data=f"toggle_media:{chat_id}:entry_msg"),
            InlineKeyboardButton(text=f"{status('exit_msg')} إشعار خروج", callback_data=f"toggle_media:{chat_id}:exit_msg")
        ],
        # Back
        [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"back_to_main:{chat_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_silent_mode_keyboard(chat_id: int, current_settings: dict) -> InlineKeyboardMarkup:
    """
    Advanced Silent Mode Dashboard.
    🔹 لوحة تحكم الوضع الصامت (القفل).
    """
    silent = current_settings.get("silent", {})
    is_locked = silent.get("is_locked", False)
    
    # Schedule info
    schedule = silent.get("schedule", {})
    sched_active = schedule.get("active", False)
    open_t = schedule.get("open_time", "08:00")
    close_t = schedule.get("close_time", "23:00")
    
    # Timer info
    timer = silent.get("timer", {})
    timer_active = timer.get("active", False)
    
    # Status Text
    status_icon = "🔴" if is_locked else "🟢"
    status_text = "مغلقة (Locked)" if is_locked else "مفتوحة (Open)"
    
    keyboard = [
        # 1. Manual Toggle (Big Button)
        [InlineKeyboardButton(text=f"{status_icon} الحالة: {status_text}", callback_data=f"silent_toggle:{chat_id}")],
        
        # 2. Timer Options (Row)
        [
            InlineKeyboardButton(text="⏱️ قفل 1h", callback_data=f"silent_timer:{chat_id}:1h"),
            InlineKeyboardButton(text="⏱️ قفل 4h", callback_data=f"silent_timer:{chat_id}:4h"),
            InlineKeyboardButton(text="⏱️ قفل 12h", callback_data=f"silent_timer:{chat_id}:12h")
        ],
        
        # 3. Schedule Toggle
        [InlineKeyboardButton(text=f"{'✅' if sched_active else '❌'} الجدولة اليومية ({open_t} - {close_t})", callback_data=f"silent_schedule_toggle:{chat_id}")],
        
        # 4. Edit Schedule (If active)
        [
            InlineKeyboardButton(text="✏️ الجدول", callback_data=f"silent_schedule_edit:{chat_id}"),
            InlineKeyboardButton(text="💬 الرسائل", callback_data=f"silent_msg_menu:{chat_id}")
        ],
        
        [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"back_to_main:{chat_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_silent_messages_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """
    Menu to select which silent mode message to edit.
    """
    keyboard = [
        [InlineKeyboardButton(text="🔓 رسالة الفتح اليومي", callback_data=f"silent_msg_edit:{chat_id}:daily_open")],
        [InlineKeyboardButton(text="🔒 رسالة القفل اليومي", callback_data=f"silent_msg_edit:{chat_id}:daily_close")],
        [InlineKeyboardButton(text="⏱️ رسالة المؤقت", callback_data=f"silent_msg_edit:{chat_id}:timer_lock")],
        [InlineKeyboardButton(text="👮 قفل المشرفين (يدوي)", callback_data=f"silent_msg_edit:{chat_id}:manual_lock")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"settings_lock:{chat_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_welcome_settings_keyboard(chat_id: int, current_settings: dict) -> InlineKeyboardMarkup:
    """
    Welcome Message Settings.
    🔹 إعدادات الترحيب.
    """
    welcome = current_settings.get("welcome_message", {})
    enabled = welcome.get("enabled", True)
    
    status = "✅ مفعل (On)" if enabled else "❌ معطل (Off)"
    
    keyboard = [
        [InlineKeyboardButton(text=f"الحالة: {status}", callback_data=f"toggle_welcome:{chat_id}:enabled")],
        [InlineKeyboardButton(text="📝 تعديل نص الترحيب (Edit Text)", callback_data=f"edit_welcome_text:{chat_id}")],
        [InlineKeyboardButton(text="🔙 رجوع (Back)", callback_data=f"back_to_main:{chat_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_banned_words_keyboard(chat_id: int, current_settings: dict) -> InlineKeyboardMarkup:
    """
    Banned Words Management Keyboard.
    🔹 إدارة الكلمات المحظورة.
    """
    words = current_settings.get("banned_words", [])
    
    keyboard = []
    # Show words (limit to last 10 for simplicity in this view)
    # Ideally should use pagination if list is long
    for word in words[-10:]:
        # Click to delete
        keyboard.append([InlineKeyboardButton(text=f"🗑️ حذف: {word}", callback_data=f"del_word:{chat_id}:{word}")])
        
    keyboard.append([InlineKeyboardButton(text="➕ إضافة كلمة (Add Word)", callback_data=f"add_word:{chat_id}")])
    keyboard.append([InlineKeyboardButton(text="🔙 رجوع (Back)", callback_data=f"back_to_main:{chat_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_whitelist_keyboard(chat_id: int, current_settings: dict) -> InlineKeyboardMarkup:
    """
    Whitelist Management Keyboard.
    🔹 إدارة القائمة البيضاء.
    """
    whitelist = current_settings.get("whitelist", [])
    
    keyboard = []
    for item in whitelist[-10:]:
        keyboard.append([InlineKeyboardButton(text=f"🗑️ حذف: {item}", callback_data=f"del_whitelist:{chat_id}:{item}")])
        
    keyboard.append([InlineKeyboardButton(text="➕ إضافة (Add User/Link)", callback_data=f"add_whitelist:{chat_id}")])
    keyboard.append([InlineKeyboardButton(text="🔙 رجوع (Back)", callback_data=f"back_to_main:{chat_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_groups_list_keyboard(groups: list) -> InlineKeyboardMarkup:
    """
    List active groups for remote management.
    """
    keyboard = []
    for group in groups:
        chat_id = group.get("chat_id")
        title = group.get("title", f"Group {chat_id}")
        
        keyboard.append([InlineKeyboardButton(text=f"📂 {title}", callback_data=f"manage_group:{chat_id}")])
    
    keyboard.append([InlineKeyboardButton(text="❌ إغلاق", callback_data="close_settings")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_time_selection_keyboard(chat_id: int, mode: str) -> InlineKeyboardMarkup:
    """
    Generate a grid of time slots (30-min intervals).
    mode: 'open' or 'close'
    """
    keyboard = []
    
    # Generate times: 00:00 to 23:30
    hours = range(0, 24)
    minutes = [0, 30]
    
    row = []
    for h in hours:
        for m in minutes:
            time_str = f"{h:02d}:{m:02d}"
            
            # Format display (e.g., 1:00 PM)
            display_h = h if h <= 12 else h - 12
            display_h = 12 if display_h == 0 else display_h
            ampm = "AM" if h < 12 else "PM"
            display = f"{display_h}:{m:02d} {ampm}"
            
            row.append(InlineKeyboardButton(text=display, callback_data=f"time_pick:{chat_id}:{mode}:{time_str}"))
            
            if len(row) == 4: # 4 columns
                keyboard.append(row)
                row = []
                
    if row:
        keyboard.append(row)
        
    # Cancel button
    keyboard.append([InlineKeyboardButton(text="🔙 إلغاء", callback_data=f"manage_group:{chat_id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
