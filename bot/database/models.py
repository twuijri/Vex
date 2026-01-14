"""
MongoDB Models using Beanie ODM
"""
from datetime import datetime
from typing import List, Optional, Dict
from beanie import Document, Indexed
from pydantic import Field


class MediaFilters(Document):
    """Media filter settings embedded in Group"""
    document: bool = True
    photo: bool = True
    video: bool = True
    voice: bool = True
    audio: bool = True
    sticker: bool = True
    video_note: bool = True
    gif: bool = True
    forward: bool = True
    telegram_link: bool = True
    link: bool = True
    mobile: bool = True
    tag: bool = True
    hashtag: bool = True
    bots: bool = True
    join_service: bool = True
    left_service: bool = True
    location: bool = True
    games: bool = True
    text: bool = True


class WordList(Document):
    """Word list (blocked or allowed)"""
    active: bool = False
    words: List[str] = Field(default_factory=list)


class DailySchedule(Document):
    """Daily schedule for silent mode"""
    enabled: bool = False
    from_time: Optional[str] = None  # "HH:MM"
    to_time: Optional[str] = None    # "HH:MM"
    timezone: str = "Asia/Riyadh"


class SilentMessages(Document):
    """Custom messages for silent mode"""
    lock: str = "🔕 تم قفل المجموعة"
    unlock: str = "🔔 تم فتح المجموعة"
    timer_lock: str = "🔕 تم قفل المجموعة مؤقتاً"


class Permissions(Document):
    """Group permissions"""
    can_send_messages: bool = True
    can_send_media_messages: bool = True
    can_send_other_messages: bool = True
    can_send_polls: bool = True
    can_add_web_page_previews: bool = True
    can_change_info: bool = True
    can_invite_users: bool = True
    can_pin_messages: bool = True


class Silent(Document):
    """Silent mode configuration"""
    active: bool = False
    daily_schedule: DailySchedule = Field(default_factory=DailySchedule)
    messages: SilentMessages = Field(default_factory=SilentMessages)
    permissions: Permissions = Field(default_factory=Permissions)
    timer_end: Optional[datetime] = None  # For temporary lock


class Button(Document):
    """Inline button"""
    text: str
    url: str


class Welcome(Document):
    """Welcome message configuration"""
    active: bool = False
    message: str = "مرحباً بك في المجموعة! 👋"
    delete_previous: bool = False
    last_message_id: Optional[int] = None
    with_rules: bool = False
    buttons: List[Button] = Field(default_factory=list)


class Rules(Document):
    """Rules configuration"""
    active: bool = False
    message: str = "قوانين المجموعة"
    permission: str = "all"  # "all" or "admins"
    place: str = "group"     # "group" or "private"
    buttons: List[Button] = Field(default_factory=list)


class WarnUser(Document):
    """User warn record"""
    user_id: int
    warns: int = 0
    last_warn: Optional[datetime] = None


class Warn(Document):
    """Warn system configuration"""
    active: bool = False
    max_warns: int = 3
    action: str = "kick"  # "kick", "ban", "mute"
    users: List[WarnUser] = Field(default_factory=list)


class FloodUser(Document):
    """User flood record"""
    user_id: int
    message_count: int = 0
    first_message_time: Optional[datetime] = None


class Flood(Document):
    """Flood control configuration"""
    active: bool = False
    max_messages: int = 5
    time_window: int = 5  # seconds
    action: str = "mute"  # "kick", "ban", "mute", "delete"
    delete_messages: bool = True
    users: List[FloodUser] = Field(default_factory=list)


class Captcha(Document):
    """Captcha configuration"""
    active: bool = False
    type: str = "button"  # "button", "math", "text"
    timeout: int = 60  # seconds
    action: str = "kick"  # "kick" or "ban"


class LanguageSettings(Document):
    """Language filter settings"""
    arabic: bool = True
    english: bool = True
    persian: bool = True
    urdu: bool = True
    other: bool = True


class Group(Document):
    """Group/Supergroup document"""
    chat_id: Indexed(int, unique=True)
    chat_title: str
    chat_type: str  # "group" or "supergroup"
    activated_by: int
    activated_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True
    
    # Database configuration
    mongo_db_name: str = "Vex_db"  # اسم قاعدة البيانات المستخدمة (default)
    
    # Settings
    media_filters: MediaFilters = Field(default_factory=MediaFilters)
    blocked_words: WordList = Field(default_factory=WordList)
    allowed_words: WordList = Field(default_factory=WordList)
    silent: Silent = Field(default_factory=Silent)
    welcome: Welcome = Field(default_factory=Welcome)
    rules: Rules = Field(default_factory=Rules)
    warn: Warn = Field(default_factory=Warn)
    flood: Flood = Field(default_factory=Flood)
    captcha: Captcha = Field(default_factory=Captcha)
    language_settings: LanguageSettings = Field(default_factory=LanguageSettings)
    
    class Settings:
        name = "groups"
        indexes = [
            "chat_id",
        ]


class Admin(Document):
    """Bot admin document"""
    user_id: Indexed(int, unique=True)
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    added_at: datetime = Field(default_factory=datetime.utcnow)
    added_by: int
    
    class Settings:
        name = "admins"
        indexes = [
            "user_id",
        ]


class AdminGroup(Document):
    """Admin group configuration (only one)"""
    chat_id: Indexed(int, unique=True)
    chat_title: str
    set_at: datetime = Field(default_factory=datetime.utcnow)
    set_by: int
    
    class Settings:
        name = "admin_group"
        indexes = [
            "chat_id",
        ]


class SupportTicket(Document):
    """Support ticket for message relay"""
    user_id: Indexed(int)
    admin_message_id: Indexed(int)  # Message ID in admin group
    user_message_id: int            # Message ID in private chat
    message_text: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "support_tickets"
        indexes = [
            "user_id",
            "admin_message_id",
        ]


class BlockedUser(Document):
    """Blocked user from support"""
    user_id: Indexed(int, unique=True)
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    reason: Optional[str] = None
    blocked_at: datetime = Field(default_factory=datetime.utcnow)
    blocked_by: int
    
    class Settings:
        name = "blocked_users"
        indexes = [
            "user_id",
        ]


class User(Document):
    """User document for statistics"""
    user_id: Indexed(int, unique=True)
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        indexes = [
            "user_id",
        ]
