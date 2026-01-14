"""
Constants and emojis used throughout the bot
"""

# Emojis
EMOJI_CHECK = "✅"
EMOJI_CROSS = "❌"
EMOJI_SETTINGS = "⚙️"
EMOJI_BACK = "🔙"
EMOJI_EXIT = "❌"
EMOJI_LOCK = "🔕"
EMOJI_UNLOCK = "🔔"
EMOJI_MEDIA = "🌌"
EMOJI_WORDS = "🚫"
EMOJI_SILENT = "🔕"
EMOJI_WELCOME = "🎊"
EMOJI_RULES = "🚩"
EMOJI_SUPPORT = "💬"
EMOJI_ADMIN = "👨‍💼"
EMOJI_GROUP = "👥"
EMOJI_ADD = "➕"
EMOJI_REMOVE = "➖"
EMOJI_LIST = "📃"
EMOJI_EDIT = "📝"
EMOJI_WARNING = "⚠️"
EMOJI_INFO = "ℹ️"
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_LOADING = "⏳"
EMOJI_TIMER = "⏰"
EMOJI_CALENDAR = "📆"
EMOJI_MESSAGE = "📨"
EMOJI_PERMISSIONS = "🏷"
EMOJI_BLOCKED = "🚫"
EMOJI_ALLOWED = "✅"
EMOJI_BOT = "🤖"
EMOJI_USER = "👤"
EMOJI_CAPTCHA = "🔐"
EMOJI_WARN = "⚠️"
EMOJI_FLOOD = "🌊"
EMOJI_LANGUAGE = "🌐"

# Media Types
MEDIA_TYPES = [
    "document",
    "photo", 
    "video",
    "voice",
    "audio",
    "sticker",
    "video_note",
    "gif",
    "forward",
    "telegram_link",
    "link",
    "mobile",
    "tag",
    "hashtag",
    "bots",
    "join_service",
    "left_service",
    "location",
    "games",
    "text"
]

# Media Type Names (Arabic)
MEDIA_NAMES = {
    "document": "🗂 الملفات",
    "photo": "🎆 الصور",
    "video": "🎥 الفيديو",
    "voice": "🎙 تسجيلات الصوت",
    "audio": "🎶 الموسيقى",
    "sticker": "🌠 الملصقات",
    "video_note": "🎥 ملاحظات الفيديو",
    "gif": "🎭 الصور المتحركة",
    "forward": "🔄 إعادة التوجيه",
    "telegram_link": "📣 روابط تيليجرام",
    "link": "🔗 الروابط",
    "mobile": "📱 أرقام الجوال",
    "tag": "📍 التاقات",
    "hashtag": "#️⃣ الهاشتاق",
    "bots": "🤖 البوتات",
    "join_service": "🔻 إشعارات الدخول",
    "left_service": "🔺 إشعارات الخروج",
    "location": "🗺 المواقع",
    "games": "🎮 الألعاب",
    "text": "📝 النصوص"
}

# Permission Names (Arabic)
PERMISSION_NAMES = {
    "can_send_messages": "✉️ إرسال الرسائل",
    "can_send_media_messages": "🎆 إرسال الوسائط",
    "can_send_other_messages": "🖼 إرسال الملصقات والصور المتحركة",
    "can_send_polls": "📊 إرسال الاستفتاءات",
    "can_add_web_page_previews": "🔍 معاينة الروابط",
    "can_change_info": "📝 تغيير معلومات المجموعة",
    "can_invite_users": "👥 إضافة الأعضاء",
    "can_pin_messages": "📌 تثبيت الرسائل"
}

# Actions
WARN_ACTIONS = {
    "kick": "طرد",
    "ban": "حظر",
    "mute": "كتم"
}

FLOOD_ACTIONS = {
    "kick": "طرد",
    "ban": "حظر",
    "mute": "كتم",
    "delete": "حذف الرسائل فقط"
}

# Messages
MSG_WELCOME_USER = "مرحباً بك في البوت! 👋"
MSG_WELCOME_ADMIN = "مرحباً بك في لوحة التحكم! 👨‍💼"
MSG_GROUP_ACTIVATED = "✅ تم تفعيل المجموعة بنجاح"
MSG_GROUP_ALREADY_ACTIVE = "⚠️ المجموعة مفعلة مسبقاً"
MSG_GROUP_DEACTIVATED = "☑️ تم إلغاء تفعيل المجموعة"
MSG_GROUP_NOT_ACTIVE = "⚠️ المجموعة غير مفعلة"
MSG_NOT_ADMIN = "⚠️ هذا الأمر للمشرفين فقط"
MSG_SUPPORT_DISABLED = "🚫 التواصل متوقف حالياً"
MSG_USER_BLOCKED = "🚫 أنت محظور من المراسلة"
MSG_SETTINGS_CLOSED = "☑️ تم إغلاق الإعدادات"

# Callback Data Prefixes
CB_SETTINGS = "settings"
CB_GROUPS = "groups"
CB_GROUP_SETTINGS = "group_settings"
CB_MEDIA = "media"
CB_WORDS = "words"
CB_SILENT = "silent"
CB_WELCOME = "welcome"
CB_RULES = "rules"
CB_SUPPORT = "support"
CB_ADMIN = "admin"
CB_BACK = "back"
CB_EXIT = "exit"
CB_TOGGLE = "toggle"
CB_ADD = "add"
CB_REMOVE = "remove"
CB_LIST = "list"
CB_EDIT = "edit"

# Time Formats
TIME_FORMAT = "%H:%M"
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
