"""
Vex - User Service
Business logic for user management
"""
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func

from db.database import get_db
from db.models import User, SupportMessage

logger = logging.getLogger("vex.services.user")


async def register_user(
    telegram_id: int,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
) -> None:
    """Register a new user or update existing"""
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
            session.add(user)
        else:
            # Update user info
            user.first_name = first_name
            user.last_name = last_name
            user.username = username


async def is_user_blocked(telegram_id: int) -> bool:
    """Check if a user is blocked"""
    async with get_db() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id,
                User.is_blocked == True,
            )
        )
        return result.scalar_one_or_none() is not None


async def block_user(telegram_id: int) -> str:
    """Block a user from messaging the bot"""
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.is_blocked = True
            user.blocked_at = datetime.utcnow()
            return f"🚫 تم حظر المستخدم: [{user.first_name}](tg://user?id={telegram_id})"
        return "⚠️ المستخدم غير موجود"


async def unblock_user(telegram_id: int) -> str:
    """Unblock a user"""
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user and user.is_blocked:
            user.is_blocked = False
            user.blocked_at = None
            return f"✅ تم الغاء حظر المستخدم: [{user.first_name}](tg://user?id={telegram_id})"
        return "⚠️ المستخدم غير محظور"


async def list_blocked_users() -> List[User]:
    """List all blocked users"""
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.is_blocked == True)
        )
        return result.scalars().all()


async def unblock_all_users() -> str:
    """Unblock all blocked users"""
    async with get_db() as session:
        result = await session.execute(
            select(User).where(User.is_blocked == True)
        )
        users = result.scalars().all()
        for user in users:
            user.is_blocked = False
            user.blocked_at = None
        return f"✅ تم ازالة الحظر عن {len(users)} مستخدم"


async def save_support_message(
    telegram_id: int,
    admin_group_message_id: int,
    content_preview: Optional[str] = None,
    is_media: bool = False,
) -> None:
    """Save a support message for tracking"""
    async with get_db() as session:
        # Get or create user
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return

        msg = SupportMessage(
            user_id=user.id,
            user_telegram_id=telegram_id,
            admin_group_message_id=admin_group_message_id,
            content_preview=content_preview,
            is_media=is_media,
        )
        session.add(msg)


async def get_support_message_by_admin_msg_id(
    admin_group_message_id: int,
) -> Optional[SupportMessage]:
    """Find the original user from a forwarded message in admin group"""
    async with get_db() as session:
        result = await session.execute(
            select(SupportMessage).where(
                SupportMessage.admin_group_message_id == admin_group_message_id
            )
        )
        return result.scalar_one_or_none()


async def get_user_count() -> int:
    """Get total user count"""
    async with get_db() as session:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar_one()


async def get_blocked_count() -> int:
    """Get blocked user count"""
    async with get_db() as session:
        result = await session.execute(
            select(func.count(User.id)).where(User.is_blocked == True)
        )
        return result.scalar_one()
