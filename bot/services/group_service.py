"""
Vex - Group Service
Business logic for managed group management
"""
import logging
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from db.database import get_db
from db.models import (
    ManagedGroup, BlockedWord, AllowedWord, GroupSchedule,
    WelcomeConfig, RulesConfig,
)

logger = logging.getLogger("vex.services.group")


async def get_group_by_id(group_db_id: int):
    """Return a ManagedGroup row by its DB primary key."""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(ManagedGroup.id == group_db_id)
        )
        return result.scalar_one_or_none()



# ─── Group CRUD ────────────────────────────────────────────────

async def activate_group(
    telegram_group_id: int,
    group_name: str,
    group_type: str,
    activated_by: int,
) -> str:
    """Activate bot management for a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(
                ManagedGroup.telegram_group_id == telegram_group_id
            )
        )
        if result.scalar_one_or_none():
            return "❎ المجموعة مفعلة مسبقاً"

        group = ManagedGroup(
            telegram_group_id=telegram_group_id,
            group_name=group_name,
            group_type=group_type,
            activated_by=activated_by,
        )
        session.add(group)

        # Create default welcome config
        session.add(WelcomeConfig(group=group))
        # Create default rules config
        session.add(RulesConfig(group=group))
        # Create default schedule config
        session.add(GroupSchedule(group=group))

        return "✅ تم تفعيل المجموعة"


async def deactivate_group(telegram_group_id: int) -> str:
    """Deactivate bot management for a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(
                ManagedGroup.telegram_group_id == telegram_group_id
            )
        )
        group = result.scalar_one_or_none()
        if group:
            await session.delete(group)
            return "☑️ تم الغاء تفعيل المجموعة"
        return "⚠️ المجموعة ليست مفعلة"


async def get_managed_group(telegram_group_id: int) -> Optional[ManagedGroup]:
    """Get a managed group by telegram ID"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(
                selectinload(ManagedGroup.blocked_words),
                selectinload(ManagedGroup.allowed_words),
                selectinload(ManagedGroup.schedule),
                selectinload(ManagedGroup.welcome_config),
                selectinload(ManagedGroup.rules_config),
            )
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        return result.scalar_one_or_none()


async def list_managed_groups() -> List[ManagedGroup]:
    """List all managed groups"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(ManagedGroup.is_active == True)
        )
        return result.scalars().all()


async def is_managed_group(telegram_group_id: int) -> bool:
    """Check if a group is managed"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(
                ManagedGroup.telegram_group_id == telegram_group_id,
                ManagedGroup.is_active == True,
            )
        )
        return result.scalar_one_or_none() is not None


async def get_group_count() -> int:
    """Get managed group count"""
    async with get_db() as session:
        result = await session.execute(
            select(func.count(ManagedGroup.id)).where(ManagedGroup.is_active == True)
        )
        return result.scalar_one()


# ─── Media Settings ────────────────────────────────────────────

async def get_group_media_setting(
    telegram_group_id: int, media_type: str
) -> bool:
    """Get a specific media setting for a group (True=allowed, False=blocked)"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(
                ManagedGroup.telegram_group_id == telegram_group_id
            )
        )
        group = result.scalar_one_or_none()
        if group and group.media_settings:
            return group.media_settings.get(media_type, True)
        return True


async def toggle_media_setting(
    telegram_group_id: int, media_type: str
) -> bool:
    """Toggle a media setting and return the new value"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(
                ManagedGroup.telegram_group_id == telegram_group_id
            )
        )
        group = result.scalar_one_or_none()
        if group:
            settings = dict(group.media_settings)
            current = settings.get(media_type, True)
            settings[media_type] = not current
            group.media_settings = settings
            return settings[media_type]
        return True


# ─── Permission Settings ──────────────────────────────────────

async def get_permission_settings(telegram_group_id: int) -> dict:
    """Get permission settings for a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(
                ManagedGroup.telegram_group_id == telegram_group_id
            )
        )
        group = result.scalar_one_or_none()
        if group:
            return group.permission_settings
        return {}


async def toggle_permission_setting(
    telegram_group_id: int, permission_type: str
) -> bool:
    """Toggle a permission setting and return the new value"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(
                ManagedGroup.telegram_group_id == telegram_group_id
            )
        )
        group = result.scalar_one_or_none()
        if group:
            settings = dict(group.permission_settings)
            current = settings.get(permission_type, True)
            settings[permission_type] = not current
            group.permission_settings = settings
            return settings[permission_type]
        return True


# ─── Blocked Words ─────────────────────────────────────────────

async def add_blocked_word(telegram_group_id: int, word: str) -> str:
    """Add a blocked word to a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(
                ManagedGroup.telegram_group_id == telegram_group_id
            )
        )
        group = result.scalar_one_or_none()
        if not group:
            return "⚠️ المجموعة غير مفعلة"

        # Check duplicate
        existing = await session.execute(
            select(BlockedWord).where(
                BlockedWord.group_id == group.id,
                BlockedWord.word == word,
            )
        )
        if existing.scalar_one_or_none():
            return "⚠️ الكلمة محظورة مسبقاً"

        session.add(BlockedWord(group_id=group.id, word=word))
        return f"✅ تم حظر الكلمة: {word}"


async def remove_blocked_word(telegram_group_id: int, word: str) -> str:
    """Remove a blocked word from a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(
                ManagedGroup.telegram_group_id == telegram_group_id
            )
        )
        group = result.scalar_one_or_none()
        if not group:
            return "⚠️ المجموعة غير مفعلة"

        existing = await session.execute(
            select(BlockedWord).where(
                BlockedWord.group_id == group.id,
                BlockedWord.word == word,
            )
        )
        bw = existing.scalar_one_or_none()
        if bw:
            await session.delete(bw)
            return f"✅ تم الغاء حظر الكلمة: {word}"
        return "❌ الكلمة ليست محظورة"


async def list_blocked_words(telegram_group_id: int) -> List[str]:
    """List all blocked words in a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(selectinload(ManagedGroup.blocked_words))
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        group = result.scalar_one_or_none()
        if group:
            return [bw.word for bw in group.blocked_words if bw.is_active]
        return []


async def list_blocked_words_with_ids(group_db_id: int) -> List[dict]:
    """Return blocked words with their DB IDs — used by the web dashboard."""
    async with get_db() as session:
        result = await session.execute(
            select(BlockedWord)
            .where(BlockedWord.group_id == group_db_id, BlockedWord.is_active == True)
            .order_by(BlockedWord.word)
        )
        rows = result.scalars().all()
        return [{"id": bw.id, "word": bw.word} for bw in rows]


async def delete_blocked_word_by_id(word_id: int) -> bool:
    """Delete a blocked word by its DB primary key. Returns True if deleted."""
    async with get_db() as session:
        result = await session.execute(
            select(BlockedWord).where(BlockedWord.id == word_id)
        )
        bw = result.scalar_one_or_none()
        if bw:
            await session.delete(bw)
            return True
        return False


async def clear_blocked_words(telegram_group_id: int) -> str:
    """Remove all blocked words from a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup).where(
                ManagedGroup.telegram_group_id == telegram_group_id
            )
        )
        group = result.scalar_one_or_none()
        if group:
            await session.execute(
                BlockedWord.__table__.delete().where(
                    BlockedWord.group_id == group.id
                )
            )
            return "✅ تم ازالة جميع الكلمات المحظورة"
        return "⚠️ المجموعة غير مفعلة"


async def check_blocked_word(telegram_group_id: int, text: str) -> bool:
    """Check if text contains any blocked word"""
    words = await list_blocked_words(telegram_group_id)
    text_lower = text.lower()
    return any(w.lower() in text_lower for w in words)


# ─── Welcome Config ───────────────────────────────────────────

async def get_welcome_config(telegram_group_id: int) -> Optional[WelcomeConfig]:
    """Get welcome configuration for a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(selectinload(ManagedGroup.welcome_config))
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        group = result.scalar_one_or_none()
        return group.welcome_config if group else None


async def update_welcome_message(telegram_group_id: int, message: str) -> str:
    """Update welcome message for a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(selectinload(ManagedGroup.welcome_config))
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        group = result.scalar_one_or_none()
        if group and group.welcome_config:
            group.welcome_config.message = message
            return "✅ تم تحديث رسالة الترحيب"
        return "⚠️ خطأ في تحديث رسالة الترحيب"


async def toggle_welcome(telegram_group_id: int) -> bool:
    """Toggle welcome message on/off"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(selectinload(ManagedGroup.welcome_config))
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        group = result.scalar_one_or_none()
        if group and group.welcome_config:
            group.welcome_config.is_active = not group.welcome_config.is_active
            return group.welcome_config.is_active
        return False


# ─── Rules Config ─────────────────────────────────────────────

async def get_rules_config(telegram_group_id: int) -> Optional[RulesConfig]:
    """Get rules configuration for a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(selectinload(ManagedGroup.rules_config))
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        group = result.scalar_one_or_none()
        return group.rules_config if group else None


async def update_rules_message(telegram_group_id: int, message: str) -> str:
    """Update rules message for a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(selectinload(ManagedGroup.rules_config))
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        group = result.scalar_one_or_none()
        if group and group.rules_config:
            group.rules_config.message = message
            return "✅ تم تحديث القوانين"
        return "⚠️ خطأ في تحديث القوانين"


async def toggle_rules(telegram_group_id: int) -> bool:
    """Toggle rules on/off"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(selectinload(ManagedGroup.rules_config))
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        group = result.scalar_one_or_none()
        if group and group.rules_config:
            group.rules_config.is_active = not group.rules_config.is_active
            return group.rules_config.is_active
        return False


# ─── Schedule Config ──────────────────────────────────────────

async def get_schedule_config(telegram_group_id: int) -> Optional[GroupSchedule]:
    """Get schedule configuration for a group"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(selectinload(ManagedGroup.schedule))
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        group = result.scalar_one_or_none()
        return group.schedule if group else None


async def set_lock_schedule(
    telegram_group_id: int,
    lock_time: Optional[str] = None,
    unlock_time: Optional[str] = None,
) -> str:
    """Set daily lock/unlock schedule"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(selectinload(ManagedGroup.schedule))
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        group = result.scalar_one_or_none()
        if group and group.schedule:
            if lock_time is not None:
                group.schedule.lock_time = lock_time
            if unlock_time is not None:
                group.schedule.unlock_time = unlock_time
            return "✅ تم تحديث جدول القفل"
        return "⚠️ خطأ في تحديث الجدول"


async def clear_lock_schedule(telegram_group_id: int) -> str:
    """Clear daily lock/unlock schedule"""
    async with get_db() as session:
        result = await session.execute(
            select(ManagedGroup)
            .options(selectinload(ManagedGroup.schedule))
            .where(ManagedGroup.telegram_group_id == telegram_group_id)
        )
        group = result.scalar_one_or_none()
        if group and group.schedule:
            group.schedule.lock_time = None
            group.schedule.unlock_time = None
            group.schedule.timer_minutes = None
            return "✅ تم الغاء جدول القفل"
        return "⚠️ خطأ في الغاء الجدول"
