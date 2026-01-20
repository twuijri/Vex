from pydantic import BaseModel
from typing import Optional

# ==============================================================================
# 📄 File: backend/models/config.py
# 📝 Description: Defines the data models for system configuration.
# 📝 الوصف: تعريف نماذج البيانات لإعدادات النظام.
# ==============================================================================

class SystemConfig(BaseModel):
    """
    Configuration for the System (stored in SQLite).
    🔹 إعدادات النظام (تخزن في SQLite).
    
    Attributes:
        admin_username (str): Username for dashboard login. | اسم المستخدم للدخول للوحة التحكم.
        admin_password_hash (str): Hashed password for security. | كلمة المرور المشفرة.
        mongo_uri (str): Connection string for MongoDB. | رابط الاتصال بقاعدة بيانات مونجو.
        bot_token (str): Telegram Bot API Token. | توكن البوت من @BotFather.
        support_group_id (int): Telegram Group ID for support tickets. | آيدي مجموعة الدعم الفني.
        log_channel_id (int): Telegram Channel ID for error logs. | آيدي قناة السجلات.
        is_setup_complete (bool): Flag to check if setup is done. | مؤشر لاكتمال الإعداد.
    """
    admin_username: str
    admin_password_hash: str
    mongo_uri: Optional[str] = None
    mongo_db_name: Optional[str] = "Vex_db"
    bot_token: Optional[str] = None
    support_group_id: Optional[int] = None
    log_channel_id: Optional[int] = None
    telegram_admin_ids: list[int] = [] 
    is_setup_complete: bool = False


class GroupSettings(BaseModel):
    """
    Settings for a Telegram Group (stored in MongoDB).
    🔹 إعدادات المجموعة (تخزن في MongoDB).
    
    Attributes:
        is_locked (bool): Lock group chat? | هل المجموعة مقفلة؟
        anti_spam_enabled (bool): Enable anti-spam features? | تفعيل مكافحة السبام؟
        welcome_message (str): Text sent when user joins. | رسالة الترحيب.
        allow_bots (bool): Allow adding other bots? | السماح بإضافة بوتات أخرى؟
        language (str): Bot language for this group. | لغة البوت في هذه المجموعة.
    """
    is_locked: bool = False
    anti_spam_enabled: bool = True
    welcome_message: Optional[str] = "مرحباً بك في المجموعة!"
    allow_bots: bool = False
    language: str = "ar"
