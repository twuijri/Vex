"""
Vex - Configuration Loader
Loads bot config from database instead of env variables
"""
import logging
from typing import Optional

from sqlalchemy import select

from db.database import get_db
from db.models import BotConfig

logger = logging.getLogger("vex.config")


async def load_bot_config() -> Optional[BotConfig]:
    """Load bot configuration from database"""
    async with get_db() as session:
        result = await session.execute(select(BotConfig).limit(1))
        config = result.scalar_one_or_none()
        return config


async def save_bot_config(
    bot_token: str,
    api_id: int,
    api_hash: str,
    bot_username: str,
    log_channel_id: Optional[int] = None,
) -> BotConfig:
    """Save or update bot configuration"""
    async with get_db() as session:
        result = await session.execute(select(BotConfig).limit(1))
        config = result.scalar_one_or_none()

        if config:
            config.bot_token = bot_token
            config.api_id = api_id
            config.api_hash = api_hash
            config.bot_username = bot_username
            config.log_channel_id = log_channel_id
            config.is_setup_complete = True
        else:
            config = BotConfig(
                bot_token=bot_token,
                api_id=api_id,
                api_hash=api_hash,
                bot_username=bot_username,
                log_channel_id=log_channel_id,
                is_setup_complete=True,
            )
            session.add(config)

        return config


async def mark_setup_complete() -> None:
    """Mark the setup wizard as complete"""
    async with get_db() as session:
        result = await session.execute(select(BotConfig).limit(1))
        config = result.scalar_one_or_none()
        if config:
            config.is_setup_complete = True


async def get_ai_prompt_override() -> Optional[str]:
    """Return the custom AI prompt if set, otherwise None (use built-in default)."""
    async with get_db() as session:
        result = await session.execute(select(BotConfig).limit(1))
        config = result.scalar_one_or_none()
        return config.ai_prompt_override if config else None


async def set_ai_prompt_override(prompt: Optional[str]) -> None:
    """Save a custom AI prompt. Pass None to reset to default."""
    async with get_db() as session:
        result = await session.execute(select(BotConfig).limit(1))
        config = result.scalar_one_or_none()
        if config:
            config.ai_prompt_override = prompt


async def get_ai_debug_channel_id() -> Optional[int]:
    """Return the configured AI debug channel ID, or None if not set."""
    async with get_db() as session:
        result = await session.execute(select(BotConfig).limit(1))
        config = result.scalar_one_or_none()
        return config.ai_debug_channel_id if config else None


async def set_ai_debug_channel_id(channel_id: Optional[int]) -> None:
    """Save or clear the AI debug channel ID."""
    async with get_db() as session:
        result = await session.execute(select(BotConfig).limit(1))
        config = result.scalar_one_or_none()
        if config:
            config.ai_debug_channel_id = channel_id
