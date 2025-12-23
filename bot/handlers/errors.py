from aiogram import Router, F
from aiogram.types import ErrorEvent
from bot.config_loader import load_config
import logging
import traceback

router = Router()
logger = logging.getLogger(__name__)

@router.error()
async def global_error_handler(event: ErrorEvent):
    """
    Catch all unhandled exceptions and log them to the configured Log Channel.
    """
    logger.error(f"🚨 Unhandled Error: {event.exception}", exc_info=True)
    
    config = load_config()
    channel_id = config.log_channel_id
    
    if channel_id:
        try:
            # Extract basic info
            err_name = type(event.exception).__name__
            err_msg = str(event.exception)
            tb = traceback.format_exc()
            
            # Shorten traceback
            tb_short = tb[-1000:] if len(tb) > 1000 else tb
            
            # Try to identify user if update is a message
            user_info = "Unknown"
            if event.update.message:
                user = event.update.message.from_user
                user_info = f"{user.full_name} (@{user.username}) [ID:{user.id}]"
            elif event.update.callback_query:
                user = event.update.callback_query.from_user
                user_info = f"{user.full_name} (@{user.username}) [ID:{user.id}]"
                
            text = (
                f"🔥 <b>CRITICAL ERROR REPORT</b>\n\n"
                f"👤 <b>Trigger:</b> {user_info}\n"
                f"🛑 <b>Error:</b> <code>{err_name}: {err_msg}</code>\n\n"
                f"📜 <b>Traceback:</b>\n<pre>{tb_short}</pre>"
            )
            
            await event.update.bot.send_message(channel_id, text)
            
        except Exception as e:
            logger.critical(f"❌ Failed to send error log to channel: {e}")
