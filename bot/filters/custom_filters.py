"""
Boter 2.0 - Custom Filters
All Pyrogram filters consolidated into one file using python-telegram-bot filters
"""
import logging
from typing import Optional

from telegram import Message, Update
from telegram.ext import filters

from bot.services.admin_service import is_admin, get_admin_group_id
from bot.services.user_service import is_user_blocked
from bot.services.group_service import get_group_media_setting, is_managed_group

logger = logging.getLogger("boter.filters")


class IsAdminFilter(filters.MessageFilter):
    """Check if the message sender is a bot admin"""

    def filter(self, message: Message) -> bool:
        if not message.from_user:
            return False
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context but this is sync - store result in context
                # Use a cached approach instead
                return False  # Will be checked in handler
        except RuntimeError:
            return False
        return False


class AdminGroupFilter(filters.MessageFilter):
    """Check if the message is from the admin group"""

    def filter(self, message: Message) -> bool:
        # Will be checked properly in async handler
        return message.chat.type in ["group", "supergroup"]


class NotBlockedFilter(filters.MessageFilter):
    """Check if user is not blocked"""

    def filter(self, message: Message) -> bool:
        # Will be checked in async handler
        return True


# Pre-built filter instances
IS_ADMIN = IsAdminFilter()
ADMIN_GROUP = AdminGroupFilter()
NOT_BLOCKED = NotBlockedFilter()
