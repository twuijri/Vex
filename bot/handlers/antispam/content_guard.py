import logging
import re
import unicodedata

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberAdministrator, ChatMemberOwner
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from bot.services.admin_service import is_admin, get_admin_group_id
from bot.services.group_service import is_managed_group, list_blocked_words
from bot.services.ai_service import analyze_text as ai_analyze_text
from bot.core.config import get_ai_debug_channel_id, get_ai_thresholds

logger = logging.getLogger("vex.handlers.antispam.content_guard")

# ─── Global Fallback Blacklist ────────────────────────────────────────────────
# ⚠️ تعمداً فارغة — إدارة الكلمات المحظورة تتم من لوحة التحكم لكل مجموعة على حدة.
# لا تضيف كلمات هنا، فكلمة مثل "كلب" قد تكون طبيعية في مجموعة حيوانات أليفة.
GLOBAL_BLACKLIST: list[str] = []



# ─── Layer 1: Text Normalization ─────────────────────────────────────────────

def normalize_arabic(text: str) -> str:
    """
    Deep-clean Arabic text to defeat obfuscation attempts.
    Steps:
      1. Unicode normalization (NFKC) - fixes special look-alike chars
      2. Remove diacritics (tashkeel) using PyArabic
      3. Normalize Alef/Hamza/Yaa/Taa variations
      4. Remove non-Arabic, non-space characters (symbols, emoji, punctuation)
      5. Collapse repeated characters (e.g. "غببيييي" → "غبي")
      6. Strip extra whitespace
    """
    try:
        import pyarabic.araby as araby
        # 1. Unicode normalization
        text = unicodedata.normalize("NFKC", text)
        # 2. Remove tashkeel (diacritics)
        text = araby.strip_tashkeel(text)
        text = araby.strip_tatweel(text)
    except ImportError:
        # Fallback if pyarabic not installed - basic unicode normalize only
        text = unicodedata.normalize("NFKC", text)

    # 3. Normalize common Arabic letter variants
    alef_variants = "أإآٱ"
    for ch in alef_variants:
        text = text.replace(ch, "ا")
    text = text.replace("ة", "ه")
    text = text.replace("ى", "ي")

    # 4. Remove everything that is NOT Arabic letter or space
    text = re.sub(r"[^\u0600-\u06FF\s]", "", text)

    # 5. Collapse repeated characters: "غبيييي" → "غبي" (max 1 repeat)
    text = re.sub(r"(.)\1{2,}", r"\1", text)

    # 6. Strip & collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ─── Layer 2: Blacklist Exact Match ──────────────────────────────────────────

async def check_against_blacklists(normalized_text: str, chat_id: int) -> bool:
    """
    Check normalized text against:
    - Global hardcoded blacklist
    - Per-group blocked words from database

    Returns True if a blocked word is found (message should be deleted).
    """
    lower_text = normalized_text.lower()

    # Check global blacklist first (fast, no DB)
    for word in GLOBAL_BLACKLIST:
        if normalize_arabic(word.lower()) in lower_text:
            return True

    # Check per-group words from database
    group_words = await list_blocked_words(chat_id)
    for word in group_words:
        if normalize_arabic(word.lower()) in lower_text:
            return True

    return False


AI_THRESHOLD = 0.65  # legacy constant (no longer used directly — thresholds come from DB)


async def send_admin_alert(
    context: ContextTypes.DEFAULT_TYPE,
    admin_group_id: int,
    user_name: str,
    user_id: int,
    original_text: str,
    abuse_score: float,
    chat_id: int,
    message_id: int,
    auto_deleted: bool = False,
) -> None:
    """Send an alert to the admin group with action buttons (or auto-delete notice)."""
    score_pct = int(abuse_score * 100)

    if auto_deleted:
        alert_text = (
            f"🗑️ **تم الحذف التلقائي — نسبة الإساءة {score_pct}%**\n\n"
            f"👤 المستخدم: [{user_name}](tg://user?id={user_id})\n"
            f"💬 الرسالة المحذوفة:\n`{original_text[:300]}`"
        )
        keyboard = None
    else:
        alert_text = (
            f"⚠️ **اشتباه برسالة مسيئة بنسبة {score_pct}%**\n\n"
            f"👤 المستخدم: [{user_name}](tg://user?id={user_id})\n"
            f"💬 الرسالة الأصلية:\n`{original_text[:300]}`"
        )
        chat_id_clean = str(chat_id).lstrip("-").removeprefix("100")
        msg_link = f"https://t.me/c/{chat_id_clean}/{message_id}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 اذهب للرسالة", url=msg_link)],
            [
                InlineKeyboardButton("🗑️ احذف الرسالة", callback_data=f"guard_delete:{chat_id}:{message_id}"),
                InlineKeyboardButton("✅ لا تحذف", callback_data=f"guard_keep:{chat_id}:{message_id}"),
            ]
        ])

    await context.bot.send_message(
        chat_id=admin_group_id,
        text=alert_text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


# ─── Main Handler ─────────────────────────────────────────────────────────────

async def content_guard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main entry point for the content guard.
    Runs all 3 layers sequentially on every group message.
    """
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not chat or not user:
        return

    # Only process managed groups
    if not await is_managed_group(chat.id):
        return

    # Skip bot admins
    if await is_admin(user.id):
        return

    # Skip Telegram group admins/owners
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if isinstance(member, (ChatMemberAdministrator, ChatMemberOwner)):
            return
    except Exception:
        pass

    original_text = message.text or message.caption
    if not original_text:
        return

    # ── Layer 1: Normalize ────────────────────────────────────────────────────
    normalized = normalize_arabic(original_text)
    if not normalized:
        return

    # ── Layer 2: Blacklist Check → delete immediately ─────────────────────────
    if await check_against_blacklists(normalized, chat.id):
        logger.info(f"[GUARD-L2] Blocked word detected. Deleting message from {user.id} in {chat.id}")
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"[GUARD-L2] Could not delete message: {e}")
        return  # Stop here, do not proceed to AI layer

    # ── Layer 3: AI Analysis ──────────────────────────────────────────────────
    admin_group_id = await get_admin_group_id()
    if not admin_group_id:
        return  # No admin group configured, skip AI layer silently

    score = await ai_analyze_text(normalized)
    alert_threshold, auto_delete_threshold = await get_ai_thresholds()
    logger.info(
        f"[GUARD-L3] AI score={score:.2f} alert>={alert_threshold} auto_del>={auto_delete_threshold} "
        f"user={user.id} chat={chat.id}"
    )

    user_name = user.full_name or user.username or str(user.id)
    action_taken = False

    if score >= auto_delete_threshold:
        # Auto-delete and notify admins
        action_taken = True
        try:
            await message.delete()
            logger.info(f"[GUARD-L3] Auto-deleted message from {user.id} in {chat.id} (score={score:.2f})")
        except Exception as e:
            logger.warning(f"[GUARD-L3] Could not auto-delete message: {e}")
        try:
            await send_admin_alert(
                context=context,
                admin_group_id=admin_group_id,
                user_name=user_name,
                user_id=user.id,
                original_text=original_text,
                abuse_score=score,
                chat_id=chat.id,
                message_id=message.message_id,
                auto_deleted=True,
            )
        except Exception as e:
            logger.error(f"[GUARD-L3] Failed to send auto-delete notice: {e}")

    elif score >= alert_threshold:
        # Alert admins, let them decide
        action_taken = True
        logger.info(f"[GUARD-L3] Alerting admins for message from {user.id} in {chat.id} (score={score:.2f})")
        try:
            await send_admin_alert(
                context=context,
                admin_group_id=admin_group_id,
                user_name=user_name,
                user_id=user.id,
                original_text=original_text,
                abuse_score=score,
                chat_id=chat.id,
                message_id=message.message_id,
                auto_deleted=False,
            )
        except Exception as e:
            logger.error(f"[GUARD-L3] Failed to send admin alert: {e}")

    # ── Debug Channel ──────────────────────────────────────────────────────────
    debug_ch = await get_ai_debug_channel_id()
    if debug_ch:
        try:
            bar = int(score * 10)
            bar_filled = '█' * bar + '░' * (10 - bar)
            if score >= auto_delete_threshold:
                action_label = "🗑️ حذف تلقائي"
            elif score >= alert_threshold:
                action_label = "🚨 تنبيه أرسل للمشرفين"
            else:
                action_label = "✅ لم يتخذ إجراء"
            debug_text = (
                f"🔬 *AI Debug Log*\n"
                f"────────────────────\n"
                f"💬 *الرسالة:* `{original_text[:300]}`\n"
                f"📊 *النتيجة:* `{score:.2f}` / 1.0\n"
                f"[{bar_filled}] {score*100:.0f}%\n"
                f"⚡ *تنبيه من:* `{alert_threshold:.0%}` | *حذف من:* `{auto_delete_threshold:.0%}`\n"
                f"📍 *المجموعة:* `{chat.id}`\n"
                f"🛡 *الإجراء:* {action_label}"
            )
            await context.bot.send_message(
                chat_id=debug_ch,
                text=debug_text,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(f"[GUARD-DEBUG] Failed to send debug message: {e}")


# ─── Handler Registration ─────────────────────────────────────────────────────

def register_content_guard_handlers(app: Application):
    """Register the content guard handler."""
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
            content_guard_handler,
        ),
        group=12,  # Runs after word_filter (group=11)
    )
