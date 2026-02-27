"""
Vex - Database Models
SQLAlchemy models for PostgreSQL
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, ForeignKey, Float, Integer, JSON,
    String, Text, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BotConfig(Base):
    """Bot configuration - stores setup wizard data"""
    __tablename__ = "bot_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_token: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    api_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    api_hash: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bot_username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    log_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_setup_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    # Custom AI prompt — None means use the built-in default
    ai_prompt_override: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class User(Base):
    """Users who interacted with the bot via private messages"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    blocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    support_messages: Mapped[List["SupportMessage"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Admin(Base):
    """Bot administrators"""
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AdminGroup(Base):
    """The admin control group where bot management happens"""
    __tablename__ = "admin_group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_group_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    group_name: Mapped[str] = mapped_column(String(255))
    set_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ManagedGroup(Base):
    """Groups managed by the bot (antispam, filters, etc.)"""
    __tablename__ = "managed_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_group_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    group_name: Mapped[str] = mapped_column(String(255))
    group_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    activated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Media filter settings (JSON: {"photo": true, "video": true, ...})
    media_settings: Mapped[dict] = mapped_column(
        JSON, default=lambda: {
            "text": True, "document": True, "photo": True, "video": True,
            "voice": True, "audio": True, "sticker": True, "video_note": True,
            "gif": True, "forward": True, "telegram_link": True, "link": True,
            "mobile": True, "tag": True, "hashtag": True, "bots": True,
            "join_service": True, "left_service": True, "location": True,
            "games": True,
        }
    )

    # Permission settings (JSON: {"can_send_messages": true, ...})
    permission_settings: Mapped[dict] = mapped_column(
        JSON, default=lambda: {
            "can_send_messages": True, "can_send_media_messages": True,
            "can_send_other_messages": True, "can_send_polls": True,
            "can_add_web_page_previews": True, "can_change_info": True,
            "can_invite_users": True, "can_pin_messages": True,
        }
    )

    activated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    blocked_words: Mapped[List["BlockedWord"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    allowed_words: Mapped[List["AllowedWord"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    schedule: Mapped[Optional["GroupSchedule"]] = relationship(
        back_populates="group", uselist=False, cascade="all, delete-orphan"
    )
    welcome_config: Mapped[Optional["WelcomeConfig"]] = relationship(
        back_populates="group", uselist=False, cascade="all, delete-orphan"
    )
    rules_config: Mapped[Optional["RulesConfig"]] = relationship(
        back_populates="group", uselist=False, cascade="all, delete-orphan"
    )


class BlockedWord(Base):
    """Blocked words per group"""
    __tablename__ = "blocked_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("managed_groups.id", ondelete="CASCADE"), index=True
    )
    word: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    group: Mapped["ManagedGroup"] = relationship(back_populates="blocked_words")


class AllowedWord(Base):
    """Allowed words (whitelist) per group"""
    __tablename__ = "allowed_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("managed_groups.id", ondelete="CASCADE"), index=True
    )
    word: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    group: Mapped["ManagedGroup"] = relationship(back_populates="allowed_words")


class GroupSchedule(Base):
    """Scheduled lock/unlock times for a group"""
    __tablename__ = "group_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("managed_groups.id", ondelete="CASCADE"), unique=True
    )
    lock_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # "HH:MM"
    unlock_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # "HH:MM"
    timer_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lock_message: Mapped[str] = mapped_column(Text, default="🔕 تم قفل المجموعة")
    unlock_message: Mapped[str] = mapped_column(Text, default="🔔 تم الغاء قفل المجموعة")
    timer_lock_message: Mapped[str] = mapped_column(Text, default="🔕 تم قفل المجموعة")
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Riyadh")

    group: Mapped["ManagedGroup"] = relationship(back_populates="schedule")


class WelcomeConfig(Base):
    """Welcome message configuration per group"""
    __tablename__ = "welcome_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("managed_groups.id", ondelete="CASCADE"), unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delete_last_message: Mapped[bool] = mapped_column(Boolean, default=False)
    last_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    group: Mapped["ManagedGroup"] = relationship(back_populates="welcome_config")


class RulesConfig(Base):
    """Group rules configuration"""
    __tablename__ = "rules_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("managed_groups.id", ondelete="CASCADE"), unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permission: Mapped[str] = mapped_column(String(20), default="ADMINS")  # ADMINS | ALL
    display_place: Mapped[str] = mapped_column(String(20), default="GROUP")  # GROUP | PRIVATE

    group: Mapped["ManagedGroup"] = relationship(back_populates="rules_config")


class SupportMessage(Base):
    """Tracking messages between users and admin group"""
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    # Message ID in the admin group (the forwarded message)
    admin_group_message_id: Mapped[int] = mapped_column(BigInteger, index=True)
    # Message ID sent back to user (if admin replied)
    reply_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    content_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_media: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="support_messages")


class AIProviderStat(Base):
    """Daily usage statistics per AI provider key"""
    __tablename__ = "ai_provider_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Provider name: 'gemini_1', 'gemini_2', 'gemini_3', 'huggingface'
    provider_key: Mapped[str] = mapped_column(String(50), index=True)
    stat_date: Mapped[datetime] = mapped_column(Date, index=True)
    requests_count: Mapped[int] = mapped_column(Integer, default=0)
    # 'ok', 'rate_limit_minute', 'rate_limit_day', 'error'
    last_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class AIProvider(Base):
    """AI provider entries managed from the web dashboard"""
    __tablename__ = "ai_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Human-readable label, e.g. 'Gemini Key 1'
    name: Mapped[str] = mapped_column(String(100))
    # Provider type: 'google_studio' | 'blackbox' | 'huggingface'
    provider_type: Mapped[str] = mapped_column(String(30))
    # API key
    api_key: Mapped[str] = mapped_column(Text)
    # Model name, e.g. 'gemini-1.5-flash', 'gpt-4o', 'aubmindlab/bert-base-arabertv02'
    model: Mapped[str] = mapped_column(String(200))
    # Lower number = tried first
    priority: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
