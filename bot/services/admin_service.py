"""
Boter 2.0 - Admin Service
Business logic for admin management
"""
import logging
from typing import Optional, List

from sqlalchemy import select, delete

from db.database import get_db
from db.models import Admin, AdminGroup

logger = logging.getLogger("boter.services.admin")


async def is_admin(telegram_id: int) -> bool:
    """Check if a user is a bot admin"""
    async with get_db() as session:
        result = await session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none() is not None


async def add_admin(
    telegram_id: int,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    is_super: bool = False,
) -> str:
    """Add a new bot admin"""
    async with get_db() as session:
        existing = await session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        if existing.scalar_one_or_none():
            return "⚠️ العضو تم رفعه مشرف مسبقاً"

        admin = Admin(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            is_super_admin=is_super,
        )
        session.add(admin)
        return f"✅ تم اضافة مشرف جديد : [{first_name}](tg://user?id={telegram_id})"


async def remove_admin(telegram_id: int) -> str:
    """Remove a bot admin"""
    async with get_db() as session:
        result = await session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        admin = result.scalar_one_or_none()
        if admin:
            name = admin.first_name
            await session.delete(admin)
            return f"☑️ تم ازالة المشرف : [{name}](tg://user?id={telegram_id})"
        return "⚠️ العضو ليس مشرف في البوت"


async def list_admins() -> str:
    """List all bot admins"""
    async with get_db() as session:
        result = await session.execute(select(Admin))
        admins = result.scalars().all()
        if not admins:
            return "❌ لا يوجد مشرفين في البوت"

        lines = [f"▫️ [{a.first_name}](tg://user?id={a.telegram_id})" for a in admins]
        return "📜 **مشرفين البوت :**\n\n" + "\n".join(lines)


async def get_admin_group_id() -> Optional[int]:
    """Get the admin group telegram ID"""
    async with get_db() as session:
        result = await session.execute(select(AdminGroup).limit(1))
        group = result.scalar_one_or_none()
        return group.telegram_group_id if group else None


async def set_admin_group(telegram_group_id: int, group_name: str) -> str:
    """Set or update the admin group"""
    async with get_db() as session:
        result = await session.execute(select(AdminGroup).limit(1))
        existing = result.scalar_one_or_none()

        if existing:
            if existing.telegram_group_id == telegram_group_id:
                return "⚠️ هذه المجموعة للمشرفين بالفعل"
            existing.telegram_group_id = telegram_group_id
            existing.group_name = group_name
            return "✅ تم تحديث مجموعة المشرفين"

        group = AdminGroup(
            telegram_group_id=telegram_group_id,
            group_name=group_name,
        )
        session.add(group)
        return "✅ تم تعيين مجموعة المشرفين"


async def is_admin_group(chat_id: int) -> bool:
    """Check if a chat is the admin group"""
    group_id = await get_admin_group_id()
    return group_id is not None and group_id == chat_id
