"""
Helper functions and utilities
"""
from typing import Optional
from datetime import datetime
from aiogram.types import User as TelegramUser
from bot.database.models import User, Admin, Group


async def get_or_create_user(telegram_user: TelegramUser) -> User:
    """Get existing user or create new one"""
    user = await User.find_one(User.user_id == telegram_user.id)
    
    if not user:
        user = User(
            user_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
        )
        await user.insert()
    
    return user


async def is_user_admin(user_id: int) -> bool:
    """Check if user is bot admin"""
    from bot.core.config import config
    
    # Check super admins
    if user_id in config.SUPER_ADMINS:
        return True
    
    # Check database
    admin = await Admin.find_one(Admin.user_id == user_id)
    return admin is not None


async def is_group_active(chat_id: int) -> bool:
    """Check if group is active"""
    group = await Group.find_one(Group.chat_id == chat_id)
    return group is not None and group.active


async def get_group(chat_id: int) -> Optional[Group]:
    """Get group by chat_id"""
    return await Group.find_one(Group.chat_id == chat_id)


def format_user_mention(user_id: int, first_name: str) -> str:
    """Format user mention for Markdown"""
    return f"[{first_name}](tg://user?id={user_id})"


def format_time(time_str: str) -> str:
    """Validate and format time string (HH:MM)"""
    try:
        datetime.strptime(time_str, "%H:%M")
        return time_str
    except ValueError:
        raise ValueError("Invalid time format. Use HH:MM (e.g., 23:00)")


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to minutes
    Examples: "30m", "2h", "1d"
    """
    duration_str = duration_str.lower().strip()
    
    if duration_str.endswith('m'):
        return int(duration_str[:-1])
    elif duration_str.endswith('h'):
        return int(duration_str[:-1]) * 60
    elif duration_str.endswith('d'):
        return int(duration_str[:-1]) * 60 * 24
    else:
        # Assume minutes if no unit
        return int(duration_str)


def format_duration(minutes: int) -> str:
    """Format minutes to human-readable string"""
    if minutes < 60:
        return f"{minutes} دقيقة"
    elif minutes < 1440:
        hours = minutes // 60
        return f"{hours} ساعة"
    else:
        days = minutes // 1440
        return f"{days} يوم"


def escape_markdown(text: str) -> str:
    """Escape special characters for Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


async def get_admin_group_id() -> Optional[int]:
    """Get admin group chat_id"""
    from bot.database.models import AdminGroup
    
    admin_group = await AdminGroup.find_one()
    return admin_group.chat_id if admin_group else None


def contains_blocked_word(text: str, blocked_words: list) -> bool:
    """Check if text contains any blocked word"""
    if not text or not blocked_words:
        return False
    
    text_lower = text.lower()
    for word in blocked_words:
        if word.lower() in text_lower:
            return True
    return False


def contains_allowed_word(text: str, allowed_words: list) -> bool:
    """Check if text contains any allowed word (whitelist)"""
    if not text or not allowed_words:
        return False
    
    text_lower = text.lower()
    for word in allowed_words:
        if word.lower() in text_lower:
            return True
    return False


def is_arabic(text: str) -> bool:
    """Check if text contains Arabic characters"""
    return any('\u0600' <= char <= '\u06FF' for char in text)


def is_english(text: str) -> bool:
    """Check if text contains English characters"""
    return any('a' <= char.lower() <= 'z' for char in text)


def is_persian(text: str) -> bool:
    """Check if text contains Persian characters"""
    persian_chars = ['\u06A9', '\u06AF', '\u06CC', '\u067E', '\u0686', '\u0698']
    return any(char in text for char in persian_chars)


def is_urdu(text: str) -> bool:
    """Check if text contains Urdu characters"""
    return any('\u0600' <= char <= '\u06FF' for char in text)
