"""
Boter 2.0 - Media Filter Handler
Single handler replaces 14 separate filter files from the original bot.
Deletes messages containing blocked media types in managed groups.
"""
import logging

from telegram import Update, ChatMemberAdministrator, ChatMemberOwner
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from bot.services.group_service import is_managed_group, get_group_media_setting
from bot.services.admin_service import is_admin

logger = logging.getLogger("boter.handlers.antispam.media_filter")


async def _is_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the message sender is a group admin"""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
    except Exception:
        return False


async def filter_media_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check incoming group messages against media filter settings"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not chat or not user:
        return

    # Skip if not a managed group
    if not await is_managed_group(chat.id):
        return

    # Skip admins
    if await is_admin(user.id) or await _is_group_admin(update, context):
        return

    # Determine message media type
    media_type = None
    if message.photo:
        media_type = "photo"
    elif message.video:
        media_type = "video"
    elif message.voice:
        media_type = "voice"
    elif message.audio:
        media_type = "audio"
    elif message.sticker:
        media_type = "sticker"
    elif message.document:
        media_type = "document"
    elif message.video_note:
        media_type = "video_note"
    elif message.animation:
        media_type = "gif"
    elif message.forward_date:
        media_type = "forward"
    elif message.location or message.venue:
        media_type = "location"
    elif message.game:
        media_type = "games"
    elif message.new_chat_members:
        media_type = "join_service"
    elif message.left_chat_member:
        media_type = "left_service"

    # Check text-based entities
    if message.entities or message.caption_entities:
        entities = message.entities or message.caption_entities
        for entity in entities:
            if entity.type in ("url", "text_link"):
                if not await get_group_media_setting(chat.id, "link"):
                    await _delete_message(message)
                    return
            elif entity.type == "phone_number":
                if not await get_group_media_setting(chat.id, "mobile"):
                    await _delete_message(message)
                    return
            elif entity.type == "hashtag":
                if not await get_group_media_setting(chat.id, "hashtag"):
                    await _delete_message(message)
                    return
            elif entity.type == "mention":
                if not await get_group_media_setting(chat.id, "tag"):
                    await _delete_message(message)
                    return

    # Check media type filter
    if media_type and not await get_group_media_setting(chat.id, media_type):
        await _delete_message(message)
        return


async def _delete_message(message):
    """Safely delete a message"""
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Could not delete message: {e}")


def register_media_filter_handlers(app: Application):
    """Register media filter handlers"""
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & ~filters.COMMAND,
            filter_media_messages,
        ),
        group=10,  # High group number = lower priority, runs after other handlers
    )
