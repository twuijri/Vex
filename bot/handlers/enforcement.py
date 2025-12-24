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
    2. Check 'entry_msg' permission (Delete join message)
    3. Send Welcome Message (if enabled)
    """
    settings = await db.get_group_settings(message.chat.id)
    media_settings = settings.get("media", {})
    
    # 1. Bot Invite Check
    # If adding bots is disabled, kick them immediately.
    # Note: Only admins can add bots usually? Or anyone?
    # If setting is False, NO ONE (except admin) should add bots.
    # But this handler checks newly joined members.
    if not media_settings.get("bot_invite", False):
        # Check if user who ADDED the bot is admin
        # message.from_user is the one who added? Yes.
        is_admin_user = await is_admin(message)
        if not is_admin_user:
            for member in message.new_chat_members:
                if member.is_bot and member.id != message.bot.id:
                    try:
                        await message.chat.ban(member.id) # Kick
                        # Optional: Ban the user who added it? Too harsh maybe.
                    except:
                        pass
    
    # 2. Entry Notification (Service Message) Check
    # If entry_msg is False, DELETE the service message (User joined group)
    if not media_settings.get("entry_msg", True):
        try:
            await message.delete()
            return # If deleted, maybe don't send welcome? Or send welcome anyway?
            # Usually if "Silent Join" is desired, we delete service msg AND don't welcome?
            # User request: "Entry Notifications" ❌. Probably means HIDE the system message.
            # Welcome message is separate setting.
        except:
            pass

    # 3. Welcome Message
    # Only if NOT deleted (or maybe we show welcome even if system msg is deleted?)
    # Let's show welcome if distinct setting is enabled.
    welcome_cfg = settings.get("welcome_message", {})
    if welcome_cfg.get("enabled", True):
        text = welcome_cfg.get("text", "مرحباً بك في المجموعة! 👋")
        for member in message.new_chat_members:
            if member.is_bot:
                continue
            final_text = text.replace("{name}", member.first_name).replace("{user}", member.full_name).replace("{chat}", message.chat.title)
            try:
                await message.answer(final_text)
            except:
                pass

@router.message(F.left_chat_member)
async def left_member_handler(message: Message):
    """
    Handle Left Members:
    1. Check 'exit_msg' permission (Delete left message)
    """
    settings = await db.get_group_settings(message.chat.id)
    media_settings = settings.get("media", {})
    
    if not media_settings.get("exit_msg", True):
        try:
            await message.delete()
        except:
            pass

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
    
    # 🕵️‍♂️ Bypass for Admins
    user_is_admin = await is_admin(message)
    if user_is_admin:
        return # Admins can do anything

    # -------------------------------------------------------------------------
    # 🤖 0. ANTI-BOT ENFORCEMENT (Active Purge)
    # -------------------------------------------------------------------------
    media_settings = settings.get("media", {})
    
    # If "Bot Invite" is DISABLED (False), it means NO BOTS allowed.
    # We enforce this on ACTIVE messages too (Kick on Sight).
    if message.from_user.is_bot and not media_settings.get("bot_invite", False):
        try:
            # Kick the bot immediately
            await message.chat.ban(message.from_user.id)
            await message.delete()
            # Optional: Send "Bot removed" message?
            return
        except Exception as e:
            logger.error(f"Failed to kick active bot {message.from_user.id} in {chat_id}: {e}")
            # Continue to other checks if kick failed (e.g. maybe just delete msg)


    # -------------------------------------------------------------------------
    # 🔒 1. GROUP LOCK CHECK
    # -------------------------------------------------------------------------
    lock_settings = settings.get("lock_settings", {})
    if lock_settings.get("is_locked", False):
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Failed to delete msg in locked group {chat_id}: {e}")
        return # Stop processing

    # -------------------------------------------------------------------------
    # 📷 2. MEDIA & CONTENT CHECK (The Guard)
    # -------------------------------------------------------------------------
    media_settings = settings.get("media", {})
    
    # A. Content Type Check
    # Map dictionary: content_type -> settings_key
    media_map = {
        "photo": "photo",
        "video": "video",
        "sticker": "sticker",
        "document": "document",
        "voice": "voice",
        "audio": "audio",
        "animation": "animation",
        "video_note": "video_note",
        # New Types
        "game": "game",
        "venue": "venue",
        "location": "location",
        "contact": "contact",
        "poll": "poll"
    }
    
    msg_type = message.content_type
    
    if msg_type in media_map:
        perm_key = media_map[msg_type]
        if not media_settings.get(perm_key, True):
            try:
                await message.delete()
            except:
                pass
            return
            
    # B. Text Check
    # Only if purely text? Or any message with text?
    # Usually "Text" permission controls "Text Messages".
    # If media is sent (Photo with Caption), it's Media.
    # So if content_type is 'text', check 'text' permission.
    if msg_type == "text":
        if not media_settings.get("text", True):
            # Ignore commands?
            if not message.text.startswith("/"):
                try:
                    await message.delete()
                    return
                except:
                    pass

    # C. Entity Checks (Links, Mentions, Hashtags)
    text_entities = message.entities or []
    caption_entities = message.caption_entities or []
    all_entities = text_entities + caption_entities
    
    if all_entities:
        has_mention = any(e.type in ["mention", "text_mention"] for e in all_entities)
        has_hashtag = any(e.type == "hashtag" for e in all_entities)
        
        # Link Logic
        urls = [e for e in all_entities if e.type in ["url", "text_link"]]
        import re
        tg_regex = re.compile(r"(t\.me|telegram\.me|telegram\.dog)")
        
        has_tg_link = False
        has_general_link = False
        
        for u in urls:
            # Get URL content?
            # For 'url' (plain), the text is the URL.
            # For 'text_link', the URL is in e.url.
            link_url = u.url if u.type == "text_link" else (message.text or message.caption)[u.offset:u.offset+u.length]
            
            if tg_regex.search(link_url):
                has_tg_link = True
            else:
                has_general_link = True
                
        # Enforce Permissions
        violations = []
        if has_mention and not media_settings.get("mention", True): violations.append("mention")
        
        # Fallback: Regex Check for @ if mention is disabled, to catch edge cases
        if not media_settings.get("mention", True) and "@" in content_text and "mention" not in violations:
             violations.append("mention")

        if has_hashtag and not media_settings.get("hashtag", True): violations.append("hashtag")
        if has_tg_link and not media_settings.get("telegram_link", False): violations.append("telegram_link")
        if has_general_link and not media_settings.get("link", False): violations.append("link")
        
        if violations:
            try:
                await message.delete()
            except:
                pass
            return
            
    # D. Phone Number Check (Regex)
    # Checks for phone numbers in text (English & Arabic digits) if 'contact' is disabled.
    if not media_settings.get("contact", True):
        # Regex to find 10+ digits. Simple check.
        # Supports Arabic (٠-٩) and English (0-9)
        # Matches: 0555555210, ٠٥٥٥٥٥٥٢١٠, +966..., 00966...
        import re
        content_text = message.text or message.caption or ""
        # Remove spaces and dashes for checking
        clean_text = re.sub(r'[\s\-]', '', content_text)
        
        # Pattern: (Start with + or 00 or 0 or ٠) followed by 8+ digits
        # Arabic Zero: ٠ | English Zero: 0
        phone_pattern = r'(\+|00|0|٠٠|٠)[\d٠-٩]{8,}'
        
        if re.search(phone_pattern, clean_text):
            try:
                await message.delete()
            except:
                pass
            return

    # D. Forward Check
    is_forward = message.forward_origin is not None
    if is_forward and not media_settings.get("forward", False):
        try:
            await message.delete()
        except:
            pass
        return

    # -------------------------------------------------------------------------
    # 🧹 PRE-PROCESS TEXT (Anti-Spam / Anti-Obfuscation)
    # -------------------------------------------------------------------------
    # Remove "strikethrough", "tashkeel", and other "decorations" used by spammers.
    # Ex: "أط̶لع" -> "أطلع"
    import unicodedata
    raw_text = message.text or message.caption or ""
    
    # Normalize: Decompose characters (NFD), filter out non-spacing marks (Mn), then Recompose (NFC)
    # This removes accents, strikethroughs, and Arabic tashkeel.
    clean_content = ''.join(c for c in unicodedata.normalize('NFD', raw_text)
                   if unicodedata.category(c) != 'Mn')
    
    # Explicitly remove Tatweel (Kashida) 'ـ' which is not a proper mark but used for spam
    clean_content = clean_content.replace("ـ", "")
                   
    # Normalize similar chars (like Persian Kaf/Yeh to Arabic) if needed, but 'Mn' removal is powerful enough for strikethrough.
    
    # Update content_text variable for subsequent checks
    content_text = clean_content

    # -------------------------------------------------------------------------
    # 🚫 3. BANNED WORDS CHECK
    # -------------------------------------------------------------------------
    banned_words = settings.get("banned_words", [])
    
    if content_text and banned_words:
        for word in banned_words:
            if word in content_text: # Check against CLEANED text
                try:
                    await message.delete()
                    action = settings.get("banned_words_action", "delete")
                    if action == "mute":
                        await message.answer(f"⚠️ **تم حذف رسالتك لاحتوائها على كلمة محظورة.**\n@{message.from_user.username}", delete_after=5)
                except Exception as e:
                    logger.error(f"Failed to enforce banned word {chat_id}: {e}")
                return

    # D. Phone Number Check (Regex)
    # Checks for phone numbers in text (English & Arabic digits) if 'contact' is disabled.
    if not media_settings.get("contact", True):
        # Clean specific chars for phone check (spaces, dashes) + use the ALREADY CLEANED content from above
        import re
        # Remove spaces and dashes
        phone_clean_text = re.sub(r'[\s\-]', '', content_text)
        
        # Pattern: (Start with + or 00 or 0 or ٠) followed by 8+ digits
        # Arabic Zero: ٠ | English Zero: 0
        phone_pattern = r'(\+|00|0|٠٠|٠)[\d٠-٩]{8,}'
        
        if re.search(phone_pattern, phone_clean_text):
            try:
                await message.delete()
            except:
                pass
            return
