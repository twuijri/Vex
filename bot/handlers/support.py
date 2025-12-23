from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InaccessibleMessage
from aiogram.filters import Command
from bot.services.db import db
from bot.config_loader import load_config
import logging


# ==============================================================================
# 📄 File: bot/handlers/support.py
# 📝 Description: Handles Support Ticket System (Forwarding User <-> Admin).
# 📝 الوصف: نظام الدعم الفني (تحويل الرسائل بين المستخدم والمشرفين).
# ==============================================================================

router = Router()
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Filter: Check if message is from Support Group
# ------------------------------------------------------------------------------
def is_support_group(message: Message) -> bool:
    config = load_config()
    is_match = message.chat.id == config.support_group_id
    if not is_match and message.text and "حذف" in message.text:
       logger.warning(f"⚠️ Filter Mismatch: Msg Chat ID {message.chat.id} != Config Group ID {config.support_group_id}")
    return is_match

# ------------------------------------------------------------------------------
# Block Command (/block or /حظر)
# ------------------------------------------------------------------------------
@router.message(Command(commands=["block", "حظر"]), is_support_group)
async def block_command(message: Message, bot: Bot):
    """
    Block a user.
    🔹 حظر مستخدم.
    """
    if not message.reply_to_message:
        await message.reply("⚠️ يجب الرد على رسالة المستخدم لحظره.")
        return

    replied_id = message.reply_to_message.message_id
    target_user_id = await db.get_ticket_user(replied_id)

    if target_user_id:
        await db.block_user(target_user_id)
        await message.reply(f"⛔ <b>تم حظر العضو {target_user_id} بنجاح.</b>\nلن تصل رسائله للمجموعة بعد الآن.")
        
        # Optional: Notify user immediately? 
        # Plan says: "Notify User: You have been blocked". 
        try:
             await bot.send_message(target_user_id, "⛔ <b>تم حظرك من مراسلة الدعم الفني.</b>\n\nإذا كنت تعتقد أن هذا خطأ، يمكنك طلب التماس عند محاولة الإرسال مرة أخرى.")
        except:
            pass # User might have blocked bot
    else:
        await message.reply("⚠️ لم أتمكن من العثور على صاحب هذه الرسالة.")

# ------------------------------------------------------------------------------
# Debug: Check Group ID
# ------------------------------------------------------------------------------
@router.message(Command("check_id"))
async def check_group_id(message: Message, bot: Bot):
    config = load_config()
    match_status = "نعم ✅" if message.chat.id == config.support_group_id else "لا ❌"
    
    await message.reply(
        f"🆔 <b>فحص إعدادات المجموعة:</b>\n"
        f"📍 آيدي المجموعة الحالية: `{message.chat.id}`\n"
        f"⚙️ آيدي الدعم في الإعدادات: `{config.support_group_id}`\n"
        f"✅ هل هما متطابقان؟ {match_status}"
    )


# ------------------------------------------------------------------------------
# 3. Delete Command (/delete or /حذف) (Priority High)
# ------------------------------------------------------------------------------
# Using Regex to handle "/ حذف" (with space) or typos
@router.message(F.text.regexp(r"^/ ?(delete|حذف|del).*"), is_support_group)
async def delete_command(message: Message, bot: Bot):
    """
    Handle deletion of replies.
    🔹 معالجة حذف الردود.
    """
    logger.info(f"🗑️ Delete Command Triggered by {message.from_user.id} in chat {message.chat.id}")


    # 1. If Replying to a message: Delete THAT specific message.
    if message.reply_to_message:
        replied_id = message.reply_to_message.message_id
        
        # Check if we have a log for this admin message
        reply_info = await db.get_reply_info(replied_id)
        
        if reply_info:
            try:
                # Delete from User
                await bot.delete_message(chat_id=reply_info["user_id"], message_id=reply_info["user_msg_id"])
                await message.reply("✅ تم حذف الرسالة من المستخدم بنجاح.")
                logger.info(f"🗑️ Admin deleted message {reply_info['user_msg_id']} for user {reply_info['user_id']}")
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
                await message.reply(f"❌ فشل الحذف (ربما حذفت بالفعل أو مر وقت طويل).\nError: {e}")
        else:
            await message.reply("⚠️ لم أتمكن من العثور على سجل لهذه الرسالة (ربما لم أرسلها أنا أو قديمة).")
            
    # 2. If NOT Replying: Show List of recent messages
    else:
        recent_replies = await db.get_recent_replies(limit=5)
        
        if not recent_replies:
            await message.reply("📭 لا توجد رسائل حديثة للحذف.")
            return
            
        # Build Keyboard
        buttons = []
        for r in recent_replies:
            # Show preview text if available, else ID
            preview = r.get("reply_text") or f"Message #{r['admin_msg_id']}"
            btn_text = f"🗑️ {preview}"
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"del_msg_{r['admin_msg_id']}")]) 
 
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.reply("🗑️ <b>اختر رسالة لحذفها من عند المستخدم:</b>", reply_markup=keyboard)


# ------------------------------------------------------------------------------
# 4. Callback: Handle Deletion from List
# ------------------------------------------------------------------------------
@router.callback_query(F.data.startswith("del_msg_"))
async def delete_callback(callback: CallbackQuery, bot: Bot):
    # Parse ID
    try:
        admin_msg_id = int(callback.data.split("_")[-1])
    except:
        await callback.answer("Error parsing ID")
        return

    # Check info
    reply_info = await db.get_reply_info(admin_msg_id)
    
    if reply_info:
        try:
            # Delete from User
            await bot.delete_message(chat_id=reply_info["user_id"], message_id=reply_info["user_msg_id"])
            
            await callback.message.edit_text(f"✅ تم حذف الرسالة #{admin_msg_id} بنجاح.")
            await callback.answer("تم الحذف ✅")
            logger.info(f"🗑️ Admin log-deleted message {reply_info['user_msg_id']} for user {reply_info['user_id']}")
        except Exception as e:
            logger.error(f"Callback Delete Failed: {e}")
            await callback.answer("فشل الحذف ❌", show_alert=True)
            await callback.message.edit_text(f"❌ فشل حذف الرسالة #{admin_msg_id}.\nError: {e}")
    else:
        await callback.answer("لم يتم العثور على الرسالة", show_alert=True)


# ------------------------------------------------------------------------------
# 5. Appeal System Callbacks
# ------------------------------------------------------------------------------

# A. User Requests Appeal
@router.callback_query(F.data == "appeal_request")
async def appeal_request_handler(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    
    # Update Status
    await db.set_appeal_status(user_id, "pending")
    
    # Notify User
    await callback.message.edit_text("✅ <b>تم إرسال طلب الالتماس.</b>\nسيقوم المشرفون بمراجعته قريباً.")
    
    # Notify Support Group
    config = load_config()
    if config.support_group_id:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ قبول (Unblock)", callback_data=f"appeal_approve_{user_id}"),
                InlineKeyboardButton(text="❌ رفض (Reject)", callback_data=f"appeal_reject_{user_id}")
            ]
        ])
        
        user_info = f"{callback.from_user.first_name} (@{callback.from_user.username})" if callback.from_user.username else callback.from_user.first_name
        
        await bot.send_message(
            config.support_group_id,
            f"📨 <b>طلب التماس جديد (Appeal Request)</b>\n\n"
            f"👤 المستخدم: {user_info}\n"
            f"🆔 الآيدي: `{user_id}`\n\n"
            f"يطالب برفع الحظر عنه. ماذا تريد أن تفعل؟",
            reply_markup=keyboard
        )

# B. Admin Approves Appeal
@router.callback_query(F.data.startswith("appeal_approve_"))
async def appeal_approve_handler(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[-1])
    
    await db.unblock_user(user_id)
    
    await callback.message.edit_text(f"✅ <b>تم قبول الالتماس ورفع الحظر عن {user_id}.</b>\nتم بواسطة: {callback.from_user.first_name}")
    
    try:
        await bot.send_message(user_id, "🎉 <b>مبروك! تمت الموافقة على طلب الالتماس.</b>\nيمكنك الآن مراسلة الدعم الفني مرة أخرى.")
    except:
        pass

# C. Admin Rejects Appeal
@router.callback_query(F.data.startswith("appeal_reject_"))
async def appeal_reject_handler(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[-1])
    
    await db.set_appeal_status(user_id, "rejected")
    
    await callback.message.edit_text(f"❌ <b>تم رفض الالتماس للمستخدم {user_id}.</b>\nالحظر أصبح دائماً.")
    
    try:
        await bot.send_message(user_id, "⛔ <b>عذراً، تم رفض طلب الالتماس الخاص بك.</b>\nقرار الحظر نهائي.")
    except:
        pass



# ------------------------------------------------------------------------------
# 1. User -> Admin (Forward to Support Group)
# ------------------------------------------------------------------------------
@router.message(F.chat.type == "private")
async def forward_to_support(message: Message, bot: Bot):
    """
    Forward any private message (not command) to the Support Group.
    🔹 تحويل أي رسالة خاصة (ليست أمراً) إلى مجموعة الدعم.
    """
    if message.text and message.text.startswith("/"):
        return # Ignore commands here (handled in private.py)
        
    config = load_config()
    if not config.support_group_id or config.support_group_id == 0:
        return

    # 🛑 CHECK BLOCK STATUS
    status = await db.get_user_status(message.from_user.id)
    if status["is_blocked"]:
        appeal_status = status["appeal_status"]
        
        if appeal_status == "none":
            # First time / Fresh block -> Show Appeal Button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📨 تقديم طلب التماس (Appeal)", callback_data="appeal_request")]
            ])
            await message.reply("⛔ <b>عذراً، لقد تم حظرك من مراسلة الدعم الفني.</b>\n\nيمكنك تقديم طلب التماس لرفع الحظر لمرة واحدة فقط.", reply_markup=keyboard)
        
        elif appeal_status == "pending":
            # Pending -> Wait
            await message.reply("⏳ <b>طلب الالتماس الخاص بك قيد المراجعة.</b>\nيرجى انتظار قرار المشرفين.")
            
        elif appeal_status == "rejected":
            # Rejected -> Final
            await message.reply("⛔ <b>عذراً، تم رفض طلب الالتماس.</b>\nلا يمكنك مراسلة الدعم بعد الآن.")
            
        return # ⛔ STOP EXECUTION

    try:
        # Forward or Copy? 

        # Creating a "New" message by copying is better to avoid privacy restrictions on forwarding.
        # But for Admins to know WHO sent it, we usually prepend info or rely on Forward.
        # Let's use `copy_message` + Caption or separate info message?
        # Simpler approach: Forward. If user blocks forward, it fails?
        # User requested: "The bot turns my message... saves data in DB". 
        # Let's try COPY method so we control the content and avoid "Forwarded from Hidden".
        
        # 1. Send Info Header (Optional, or just Rely on Reply)
        # Actually, standard practice: Forward the message. If admin replies to it, we catch it.
        # If user has "Forwarding Privacy" on, the bot sees it as "Forwarded from User" but Admins in group see "Forwarded from Hidden".
        # But we (Bot) know the user_id.
        
        # Sent Copy to Group
        # نرسل نسخة للمجموعة
        sent_msg = await message.forward(chat_id=config.support_group_id)
        
        # 2. Log it
        # نحفظ العلاقة: (ID الرسالة في المجموعة) -> (ID المستخدم الأصلي)
        await db.log_support_message(
            ticket_id=sent_msg.message_id,
            user_id=message.from_user.id,
            original_msg_id=message.message_id
        )
        
        # Feedback to user (Optional, maybe once per session?)
        # await message.answer("✅ تم استلام رسالتك وسيتم الرد عليك قريباً.") 
        # (Avoiding spamming user on every msg)
        
    except Exception as e:
        logger.error(f"Support Forward Error: {e}")
        # await message.answer("❌ حدث خطأ في إرسال رسالتك.")


# ------------------------------------------------------------------------------
# 2. Admin -> User (Reply in Support Group)
# ------------------------------------------------------------------------------
@router.message(F.chat.type.in_({"group", "supergroup"}), F.reply_to_message, is_support_group)
async def reply_to_user(message: Message, bot: Bot):
    """
    Handle replies in Support Group -> Send back to User.
    🔹 معالجة الردود في مجموعة الدعم -> إرسالها للمستخدم.
    """

    config = load_config()
    logger.info(f"📩 Reply Handler Triggered. Chat ID: {message.chat.id} | Config Group ID: {config.support_group_id}")
    
    # Check if replying to a forwarded message we know of

    replied_msg_id = message.reply_to_message.message_id
    logger.info(f"🔄 Checking ticket for Message ID: {replied_msg_id}")

    
    # Get original user owner of that message
    target_user_id = await db.get_ticket_user(replied_msg_id)
    logger.info(f"🔎 Ticket Owner Lookup Result: {target_user_id}")
    
    if target_user_id:
        try:
            # Copy the admin's reply to the user
            # نسخ رد المشرف وإرساله للمستخدم
            sent_copy = await message.copy_to(chat_id=target_user_id)
            
            # Extract Text/Caption for Preview
            # استخراج النص أو الشرح للعرض
            preview_text = message.text or message.caption or "[Media/ملف]"
            preview_text = preview_text[:30] + "..." if len(preview_text) > 30 else preview_text
            
            # Log for potential deletion
            # حفظ بيانات الرسالة للحذف لاحقاً
            await db.log_admin_reply(
                admin_msg_id=message.message_id,
                user_id=target_user_id,
                user_msg_id=sent_copy.message_id,
                reply_text=preview_text
            )

            
            # Confirm to Admin (User requested to remove this)
            # await message.reply("✅ تم إرسال الرد للمستخدم.")
            logger.info(f"✅ Reply sent to user {target_user_id}")

            
        except Exception as e:
            logger.error(f"Failed to send reply to user {target_user_id}: {e}")
            await message.reply(f"❌ فشل إرسال الرد (قد يكون المستخدم حظر البوت).\nError: {e}")
        # Not a tracked message, ignore.
        logger.info("❌ No ticket found for this message.")
        pass

# ------------------------------------------------------------------------------
# 6. Test Log Command (/log)
# ------------------------------------------------------------------------------
@router.message(Command(commands=["log"]))
async def test_log_command(message: Message):
    """
    Test Log Channel (Admin only).
    """
    from bot.handlers.groups import is_admin # Reuse helper or redefine
    # Ideally should be consistent. Local check:
    
    # Check Admin
    config = load_config()
    is_super = message.from_user.id in config.telegram_admin_ids
    
    # Also Check Group Admin
    is_group_admin = False
    if message.chat.type in ["group", "supergroup"]:
        member = await message.chat.get_member(message.from_user.id)
        is_group_admin = member.status in ["administrator", "creator"]
        
    if not (is_super or is_group_admin):
        return

    channel_id = config.log_channel_id
    
    if not channel_id:
        await message.reply("⚠️ <b>لم يتم تعيين قناة السجلات (Log Channel) في الإعدادات.</b>")
        return

    try:
        # Send Test Message
        await message.bot.send_message(
            chat_id=channel_id,
            text=f"🧪 <b>Test Log Message</b>\n\nUser: {message.from_user.full_name}\nID: {message.from_user.id}\nTime: {message.date}"
        )
        await message.reply("✅ <b>تم إرسال سجل تجريبي إلى قناة السجلات.</b>")
    except Exception as e:
        await message.reply(f"❌ <b>فشل الإرسال:</b>\n<code>{e}</code>")

@router.message(Command(commands=["force_error"]))
async def force_crash_handler(message: Message):
    """
    Force a crash to test Error Logging.
    """
    config = load_config()
    if message.from_user.id not in config.telegram_admin_ids:
        return
        
    await message.reply("💣 <b>Simulating Crash...</b>")
    raise Exception("This is a simulate fatal error triggered by /force_error")
