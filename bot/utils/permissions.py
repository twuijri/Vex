from aiogram import Bot
from aiogram.types import ChatPermissions
import logging

logger = logging.getLogger(__name__)

async def set_group_silent_mode(bot: Bot, chat_id: int, lock: bool) -> bool:
    """
    Lock or Unlock the group by changing ChatPermissions.
    lock=True  -> can_send_messages=False
    lock=False -> can_send_messages=True
    """
    try:
        permissions = ChatPermissions(
            can_send_messages=not lock, # The inverse of lock
            can_send_media_messages=not lock,
            can_send_other_messages=not lock,
            can_send_polls=not lock,
            can_invite_users=True, # Keep invite open usually
            can_pin_messages=False,
            can_change_info=False
        )
        await bot.set_chat_permissions(chat_id, permissions)
        logger.info(f"🔒 Silent Mode {'Enabled' if lock else 'Disabled'} for {chat_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to set permissions for {chat_id}: {e}")
        return False
