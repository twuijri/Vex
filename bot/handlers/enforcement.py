from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import BaseFilter
import logging
from bot.services.db import db
from datetime import datetime, timedelta

router = Router()
logger = logging.getLogger(__name__)

# Filter for Groups
class IsGroup(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type in ["group", "supergroup"]

async def is_admin(message: Message) -> bool:
    """Check if user is admin or creator."""
    if not message.from_user:
        return False
    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status in ["administrator", "creator"]
    except Exception:
        return False

@router.message(IsGroup())
async def enforcement_handler(message: Message):
    """
    Global Enforcement Handler for Groups.
    Checks: Lock, Media, Banned Words.
    """
    chat_id = message.chat.id
    
    # 1. Get Settings (Cached or DB)
    settings = await db.get_group_settings(chat_id)
    if not settings:
        return # Should not happen if DB is working, but safe fallback
    
    # 🛑 CHECK ACTIVATION STATUS
    if not settings.get("is_active", False):
        return # Bot is not active in this group
    
    # 🕵️‍♂️ Bypass for Admins (Check Admin ONLY if necessary to save API calls)
    # Optimization: Check checks first, then check is_admin if a violation is found?
    # No, usually we trust admins. Checking allowlist might be faster than API call.
    # But let's check admin for now to be safe and standard.
    user_is_admin = await is_admin(message)
    if user_is_admin:
        return # Admins can do anything

    # -------------------------------------------------------------------------
    # 🔒 1. GROUP LOCK CHECK
    # -------------------------------------------------------------------------
    lock_settings = settings.get("lock_settings", {})
    if lock_settings.get("is_locked", False):
        try:
            await message.delete()
            # Optional: Send "Group is locked" generic message every X seconds? 
            # Better to just delete silently or rely on pinned message.
        except Exception as e:
            logger.error(f"Failed to delete msg in locked group {chat_id}: {e}")
        return # Stop processing

    # -------------------------------------------------------------------------
    # 📷 2. MEDIA & CONTENT CHECK (The Guard)
    # -------------------------------------------------------------------------
    media_settings = settings.get("media", {})
    
    # A. Content Type Check
    msg_type = message.content_type
    
    # Map dictionary: content_type -> settings_key
    media_map = {
        "photo": "photo",
        "video": "video",
        "sticker": "sticker",
        "document": "document",
        "voice": "voice",
        "audio": "audio",
        "animation": "animation",
        "video_note": "video_note"
    }
    
    # Check Basic Media Types
    if msg_type in media_map:
        perm_key = media_map[msg_type]
        if not media_settings.get(perm_key, True): # Default to True if missing, but DB has defaults
            try:
                await message.delete()
            except:
                pass
            return

    # B. Link Check (URLs)
    # Check TEXT entities and CAPTION entities for links
    text_entities = message.entities or []
    caption_entities = message.caption_entities or []
    all_entities = text_entities + caption_entities
    
    has_link = any(e.type in ["url", "text_link", "mention"] for e in all_entities) 
    # NOTE: "mention" is @username. User said "link". Usually implies http. 
    # Let's stick to url/text_link as requested: "link: false // URLs in text blocked"
    has_url = any(e.type in ["url", "text_link"] for e in all_entities)
    
    if has_url and not media_settings.get("link", False): # Default False (Blocked) in new schema?
        # User said: "Default state for new groups is usually "True" (Allowed) for basic types."
        # But for 'link', 'forward', 'sticker' he said "False // Blocked".
        # So logic: IF has_url AND allowed=False -> Delete.
        try:
            await message.delete()
        except:
            pass
        return

    # C. Forward Check
    # Aiogram 3.x uses message.forward_origin usually, or check detection.
    # message.forward_date is legacy but still works for simple detection?
    # Better: check if message.forward_origin is not None.
    is_forward = message.forward_origin is not None
    
    if is_forward and not media_settings.get("forward", False):
        try:
            await message.delete()
        except:
            pass
        return

    # -------------------------------------------------------------------------
    # 🚫 3. BANNED WORDS CHECK
    # -------------------------------------------------------------------------
    text = message.text or message.caption or ""
    banned_words = settings.get("banned_words", [])
    
    if text and banned_words:
        for word in banned_words:
            if word in text: # Simple substring check. Regex is better but complex for user input.
                # Violation Found!
                try:
                    await message.delete()
                    
                    # Handle Violation logic (Mute etc.)
                    action = settings.get("banned_words_action", "delete")
                    
                    if action == "mute":
                        threshold = settings.get("violation_threshold", 3)
                        # We need to track violations. DB? Redis?
                        # For now, let's simple delete. 
                        # TODO: Implement violation tracking properly.
                        await message.answer(f"⚠️ **تم حذف رسالتك لاحتوائها على كلمة محظورة.**\n@{message.from_user.username}", delete_after=5)

                except Exception as e:
                    logger.error(f"Failed to enforce banned word {chat_id}: {e}")
                return

# -----------------------------------------------------------------------------
# 👋 WELCOME MESSAGE
# -----------------------------------------------------------------------------
@router.message(F.new_chat_members)
async def welcome_handler(message: Message):
    """
    Handle New Chat Members:
    1. Check 'bot_invite' permission (Kick unauthorized bots)
    2. Send Welcome Message if enabled
    """
    chat_id = message.chat.id
    settings = await db.get_group_settings(chat_id)
    
    if not settings or not settings.get("is_active", False):
        return
    
    # Check for new members
    for new_member in message.new_chat_members:
        # Check if it's a bot
        if new_member.is_bot:
            # Check bot_invite permission
            media_settings = settings.get("media", {})
            if not media_settings.get("bot_invite", False):
                try:
                    # Kick the bot
                    await message.chat.ban(new_member.id)
                    await message.chat.unban(new_member.id)
                    await message.answer(f"🚫 تم طرد البوت @{new_member.username} - البوتات غير مسموحة.")
                except Exception as e:
                    logger.error(f"Failed to kick bot: {e}")
        else:
            # Send welcome message for users
            welcome_config = settings.get("welcome_message", {})
            if welcome_config.get("enabled", True):
                welcome_text = welcome_config.get("text", "مرحباً بك في المجموعة! 👋")
                # Replace placeholders
                welcome_text = welcome_text.replace("{user}", new_member.first_name)
                welcome_text = welcome_text.replace("{mention}", f"@{new_member.username}" if new_member.username else new_member.first_name)
                
                try:
                    await message.answer(welcome_text)
                except Exception as e:
                    logger.error(f"Failed to send welcome message: {e}")

# -----------------------------------------------------------------------------
# 👋 EXIT MESSAGE
# -----------------------------------------------------------------------------
@router.message(F.left_chat_member)
async def exit_handler(message: Message):
    """
    Handle Left Chat Members - optional exit message.
    """
    chat_id = message.chat.id
    settings = await db.get_group_settings(chat_id)
    
    if not settings or not settings.get("is_active", False):
        return
    
    media_settings = settings.get("media", {})
    if media_settings.get("exit_msg", True):
        left_member = message.left_chat_member
        try:
            await message.answer(f"👋 وداعاً {left_member.first_name}!")
        except Exception as e:
            logger.error(f"Failed to send exit message: {e}")
