"""
Vex - Moderation Callbacks (Layer 4)
Handles admin decisions from content_guard alert buttons.
"""
import logging

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

logger = logging.getLogger("vex.handlers.antispam.moderation_callbacks")


async def handle_guard_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin pressed 'Delete message' button."""
    query = update.callback_query
    await query.answer()

    admin = update.effective_user
    admin_name = admin.full_name or admin.username or str(admin.id)

    # Parse callback data: guard_delete:{chat_id}:{message_id}
    try:
        _, chat_id_str, message_id_str = query.data.split(":")
        chat_id = int(chat_id_str)
        message_id = int(message_id_str)
    except (ValueError, AttributeError) as e:
        logger.error(f"[GUARD-CB] Failed to parse callback data '{query.data}': {e}")
        await query.edit_message_text("⚠️ خطأ في رقم الرسالة.")
        return

    # Attempt to delete the user's original message from the group
    deleted = False
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        deleted = True
        logger.info(f"[GUARD-CB] Message {message_id} in {chat_id} deleted by admin {admin.id}")
    except Exception as e:
        logger.warning(f"[GUARD-CB] Could not delete message {message_id} in {chat_id}: {e}")

    # Update the alert message in the admin group
    if deleted:
        new_text = (
            query.message.text_markdown_v2 or query.message.text or ""
        )
        result_line = f"\n\n✅ **تم حذف الرسالة** بواسطة [{admin_name}](tg://user?id={admin.id})"
        try:
            await query.edit_message_text(
                text=f"{query.message.text}{result_line}",
                parse_mode="Markdown",
            )
        except Exception:
            await query.edit_message_text(
                text=f"✅ تم حذف الرسالة بواسطة {admin_name}",
            )
    else:
        try:
            await query.edit_message_text(
                text=f"{query.message.text}\n\n⚠️ فشل الحذف (ربما حُذفت الرسالة مسبقاً). محاولة من [{admin_name}](tg://user?id={admin.id})",
                parse_mode="Markdown",
            )
        except Exception:
            pass


async def handle_guard_keep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin pressed 'Keep message' button."""
    query = update.callback_query
    await query.answer()

    admin = update.effective_user
    admin_name = admin.full_name or admin.username or str(admin.id)

    logger.info(f"[GUARD-CB] Message kept by admin {admin.id}")

    # Update the alert message to reflect the decision
    try:
        await query.edit_message_text(
            text=f"{query.message.text}\n\n✅ **تم السماح بالرسالة** بواسطة [{admin_name}](tg://user?id={admin.id})",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning(f"[GUARD-CB] Could not edit alert message: {e}")


def register_moderation_callback_handlers(app: Application):
    """Register Layer 4 callback handlers."""
    app.add_handler(CallbackQueryHandler(handle_guard_delete, pattern=r"^guard_delete:"))
    app.add_handler(CallbackQueryHandler(handle_guard_keep, pattern=r"^guard_keep:"))
