from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from bot.services.db import db
from bot.config_loader import load_config
from bot.keyboards.groups import (
    get_main_settings_keyboard,
    get_media_settings_keyboard,
    get_silent_mode_keyboard,
    get_welcome_settings_keyboard,
    get_banned_words_keyboard,
    get_whitelist_keyboard
)
from aiogram.fsm.context import FSMContext
from bot.states.groups import GroupSettingsStates
import logging

router = Router()
logger = logging.getLogger(__name__)

async def is_admin(message: Message) -> bool:
    """Check if user is admin."""
    if message.chat.type == "private":
        return False
    member = await message.chat.get_member(message.from_user.id)
    return member.status in ["administrator", "creator"]

async def is_super_admin(user_id: int) -> bool:
    config = load_config()
    return user_id in config.telegram_admin_ids

@router.message(Command(commands=["activate", "تفعيل"]))
async def activate_command(message: Message):
    """
    Activate bot (Super Admin only).
    🔹 تفعيل البوت (للمشرف العام فقط).
    """
    if not await is_super_admin(message.from_user.id):
        logger.warning(f"⚠️ Unauthorized activate attempt by {message.from_user.id}")
        return
    logger.info(f"✅ Activate command received from {message.from_user.id}")
    
    settings = await db.get_group_settings(message.chat.id)
    
    # Check if already active
    if settings.get("is_active"):
        await message.reply("⚠️ <b>هذه المجموعة مفعلة مسبقاً!</b> ✅\n(تم تحديث بيانات المجموعة وتنسيق الرسائل)")
    else:
        await message.reply("✅ <b>تم تفعيل البوت في هذه المجموعة بنجاح!</b> 🚀\nيمكن للمشرفين التحكم بها من مجموعة الدعم.")

    # Data Fix / Update
    updates = {
        "is_active": True,
        "title": message.chat.title
    }
    
    # Fix Bold Formatting in DB (Migration from ** to <b>)
    silent_msgs = settings.get("silent", {}).get("messages", {})
    fixed_msgs = {}
    needs_fix = False
    
    for key, text in silent_msgs.items():
        if "**" in text:
            fixed_msgs[key] = text.replace("**", "<b>").replace("**", "</b>") # Naive replace, assumes pairs. 
            # Better: a simple replace is risky if not paired, but for **text** it works as replace first by <b> then second by </b>? No.
            # Python replace is global.
            # Regex is safer? Or just simple replace string.
            # Only user provided text might break, but defaults are controlled.
            # Let's use a regex replace for safety.
            import re
            fixed_msgs[key] = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            needs_fix = True
    
    if needs_fix:
        for k, v in fixed_msgs.items():
            updates[f"silent.messages.{k}"] = v
            
    await db.update_group_settings(message.chat.id, updates)

@router.message(Command(commands=["deactivate", "تعطيل"]))
async def deactivate_command(message: Message):
    """
    Deactivate bot.
    🔹 تعطيل البوت.
    """
    if not await is_super_admin(message.from_user.id):
        return
        
    await db.update_group_settings(message.chat.id, {"is_active": False})
    await message.reply("⛔ <b>تم تعطيل البوت في هذه المجموعة.</b>")

@router.message(Command(commands=["settings", "اعدادات", "الاعدادات"]))
@router.message(F.text.in_({"/اعدادات", "/settings", "/الاعدادات"})) # Fallback explicit check
async def settings_command(message: Message):
    """
    Open Group Settings Dashboard.
    🔹 فتح لوحة إعدادات المجموعة.
    """
    if message.chat.type == "private":
        await message.reply("⚠️ <b>هذا الأمر يعمل فقط في المجموعات.</b>")
        return

    config = load_config()
    is_support = message.chat.id == config.support_group_id
    
    # DEBUG LOG
    logger.info(f"⚙️ Settings cmd: Chat={message.chat.id}, ConfigSupport={config.support_group_id}, Match={is_support}")

    # 1. If in Support Group -> Show list of active groups
    if is_support:
        if not await is_admin(message):
             return # Ignore non-admins in support group (if any)
             
        active_groups = await db.get_active_groups()
        if not active_groups:
            await message.reply("🚫 <b>لا توجد مجموعات مفعلة حالياً.</b>")
            return
            
        from bot.keyboards.groups import get_groups_list_keyboard
        await message.reply(
            "📂 <b>إدارة المجموعات</b>\n\nاختر مجموعة للتحكم بها:",
            reply_markup=get_groups_list_keyboard(active_groups)
        )
        return

    # 2. If in Public Group -> Silent Delete (Security/Noise reduction)
    # Only allow if it's super admin debugging? No, user said "prevent settings command in public".
    try:
        await message.delete()
    except:
        pass
    
    # Notify admin privately? Maybe too much noise.
    return

# -----------------------------------------------------------------------------
# 🧭 NAVIGATION CALLBACKS
# -----------------------------------------------------------------------------

@router.callback_query(F.data == "close_settings")
async def close_settings_handler(callback: CallbackQuery):
    """Close the settings menu."""
    logger.info(f"🔘 Close Settings Clicked by {callback.from_user.id}")
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"❌ Failed to delete settings message: {e}")
        try:
             # Fallback: Just edit text if delete fails
             await callback.message.edit_text("✅ <b>تم إغلاق القائمة.</b>")
        except:
             await callback.answer("تم الإغلاق")

@router.callback_query(F.data.startswith("back_to_main:"))
async def back_to_main_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "⚙️ <b>لوحة تحكم إعدادات المجموعة</b>\n\nاختر خياراً للتعديل:",
        reply_markup=get_main_settings_keyboard(chat_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("manage_group:"))
async def manage_group_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    
    settings = await db.get_group_settings(chat_id)
    if not settings:
         await callback.answer("⚠️ المجموعة غير موجودة أو لم يتم تفعيلها.", show_alert=True)
         return

    title = settings.get("title", f"Group {chat_id}")
    await callback.message.edit_text(
        f"⚙️ <b>إعدادات: {title}</b>\n\nاختر خياراً للتعديل:",
        reply_markup=get_main_settings_keyboard(chat_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("settings_media:"))
async def settings_media_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    settings = await db.get_group_settings(chat_id)
    await callback.message.edit_text(
        "📷 <b>إعدادات الوسائط (Media Settings)</b>\n\nاضغط للتبديل (✅ مسموح / ❌ ممنوع):",
        reply_markup=get_media_settings_keyboard(chat_id, settings)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_media:"))
async def toggle_media_handler(callback: CallbackQuery):
    _, chat_id, key = callback.data.split(":")
    chat_id = int(chat_id)
    
    settings = await db.get_group_settings(chat_id)
    current_state = settings.get("media", {}).get(key, True)
    new_state = not current_state
    
    # Update DB
    await db.update_group_settings(chat_id, {f"media.{key}": new_state})
    
    # Refresh UI
    updated_settings = await db.get_group_settings(chat_id)
    await callback.message.edit_reply_markup(
        reply_markup=get_media_settings_keyboard(chat_id, updated_settings)
    )
    # Optional: Answer with status
    status_text = "مسموح ✅" if new_state else "ممنوع ❌"
    await callback.answer(f"{key}: {status_text}")

@router.callback_query(F.data.startswith("settings_lock:"))
async def settings_lock_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    settings = await db.get_group_settings(chat_id)
    await callback.message.edit_text(
        "🔇 <b>الوضع الصامت (Silent Mode)</b>\n\nالتحكم في قفل المجموعة والجدولة:",
        reply_markup=get_silent_mode_keyboard(chat_id, settings)
    )
    await callback.answer()

# --- SILENT MODE ACTIONS ---

@router.callback_query(F.data.startswith("silent_toggle:"))
async def silent_toggle_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    settings = await db.get_group_settings(chat_id)
    
    current_lock = settings.get("silent", {}).get("is_locked", False)
    new_lock = not current_lock
    
    # 1. Update DB
    await db.update_group_settings(chat_id, {"silent.is_locked": new_lock})
    
    # 2. Apply Permissions (API Call)
    from bot.utils.permissions import set_group_silent_mode
    success = await set_group_silent_mode(callback.bot, chat_id, new_lock)
    
    # 3. Refresh UI
    updated_settings = await db.get_group_settings(chat_id)
    await callback.message.edit_text(
        "🔇 <b>الوضع الصامت (Silent Mode)</b>\n\nالتحكم في قفل المجموعة والجدولة:",
        reply_markup=get_silent_mode_keyboard(chat_id, updated_settings)
    )
    
    if success:
        # Send Notification to Group
        msgs = settings.get("silent", {}).get("messages", {})
        msg_text = msgs.get("manual_lock", "🔒 <b>تم قفل المجموعة.</b>") if new_lock else msgs.get("manual_unlock", "🔓 <b>تم فتح المجموعة.</b>")
        # await callback.bot.send_message(chat_id, msg_text) # Optional: User didn't explicitly ask for manual toggle msg, but implied "4 types". The 4th is "manual lock".
        # Yes, "رسالة القفل اليدوي العادي عند الضغط على حالة القفل" -> So we MUST send it.
        try:
             await callback.bot.send_message(chat_id, msg_text)
        except:
             pass
             
        await callback.answer("تم تغيير حالة القفل ✅")
    else:
        await callback.answer("🚫 فشل تغيير الصلاحيات!", show_alert=True)

@router.callback_query(F.data.startswith("silent_timer:"))
async def silent_timer_handler(callback: CallbackQuery):
    _, chat_id, duration_str = callback.data.split(":")
    chat_id = int(chat_id)
    
    # Calculate End Time
    import datetime
    seconds = 0
    if duration_str == "1h": seconds = 3600
    elif duration_str == "4h": seconds = 14400
    elif duration_str == "12h": seconds = 43200
    
    end_time = datetime.datetime.now().timestamp() + seconds
    
    # Lock NOW + Set Timer
    await db.update_group_settings(chat_id, {
        "silent.is_locked": True,
        "silent.timer.active": True,
        "silent.timer.end_time": end_time
    })
    
    from bot.utils.permissions import set_group_silent_mode
    await set_group_silent_mode(callback.bot, chat_id, lock=True)
    
    # Send Timer Message
    settings = await db.get_group_settings(chat_id)
    msgs = settings.get("silent", {}).get("messages", {})
    msg_text = msgs.get("timer_lock", "⏱️ <b>تم قفل المجموعة مؤقتاً.</b>")
    try:
         await callback.bot.send_message(chat_id, f"{msg_text} ({duration_str})")
    except:
         pass

    updated_settings = await db.get_group_settings(chat_id)
    await callback.message.edit_text(
        "🔇 <b>الوضع الصامت (Silent Mode)</b>\n\nالتحكم في قفل المجموعة والجدولة:",
        reply_markup=get_silent_mode_keyboard(chat_id, updated_settings)
    )
    await callback.answer(f"✅ تم القفل لمدة {duration_str}")

@router.callback_query(F.data.startswith("silent_schedule_toggle:"))
async def silent_schedule_toggle_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    settings = await db.get_group_settings(chat_id)
    
    current = settings.get("silent", {}).get("schedule", {}).get("active", False)
    new_state = not current
    
    await db.update_group_settings(chat_id, {"silent.schedule.active": new_state})
    
    updated_settings = await db.get_group_settings(chat_id)
    await callback.message.edit_text(
        "🔇 <b>الوضع الصامت (Silent Mode)</b>\n\nالتحكم في قفل المجموعة والجدولة:",
        reply_markup=get_silent_mode_keyboard(chat_id, updated_settings)
    )
    await callback.answer("تم تحديث الجدولة ✅")

@router.callback_query(F.data.startswith("silent_msg_menu:"))
async def silent_msg_menu_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    
    from bot.keyboards.groups import get_silent_messages_keyboard
    await callback.message.edit_text(
        "💬 <b>تعديل رسائل الوضع الصامت</b>\n\nاختر الرسالة التي تريد تغيير نصها:",
        reply_markup=get_silent_messages_keyboard(chat_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("silent_msg_edit:"))
async def silent_msg_edit_start_handler(callback: CallbackQuery, state: FSMContext):
    _, chat_id, msg_type = callback.data.split(":")
    chat_id = int(chat_id)
    
    # Map type to readable name
    type_name = {
        "daily_open": "🔓 رسالة الفتح اليومي",
        "daily_close": "🔒 رسالة القفل اليومي",
        "timer_lock": "⏱️ رسالة المؤقت",
        "manual_lock": "👮 رسالة القفل اليدوي"
    }.get(msg_type, msg_type)
    
    await state.set_state(GroupSettingsStates.waiting_for_silent_message_text)
    await state.update_data(chat_id=chat_id, msg_type=msg_type)
    
    # Fetch current message
    settings = await db.get_group_settings(chat_id)
    current_msg = settings.get("silent", {}).get("messages", {}).get(msg_type, "—")
    
    await callback.message.edit_text(
        f"✏️ <b>تعديل: {type_name}</b>\n\n"
        f"📜 <b>الرسالة الحالية:</b>\n"
        f"<code>{current_msg}</code>\n\n"
        f"⬇️ <b>أرسل النص الجديد الآن:</b>\n(أرسل 'الغاء' للتراجع)",
        reply_markup=None
    )
    await callback.answer()

@router.message(GroupSettingsStates.waiting_for_silent_message_text)
async def silent_msg_text_handler(message: Message, state: FSMContext):
    if message.text.lower() == "الغاء":
        await state.clear()
        await message.answer("❌ تم الإلغاء.")
        return

    data = await state.get_data()
    chat_id = data.get("chat_id")
    msg_type = data.get("msg_type")
    
    # Update DB
    key = f"silent.messages.{msg_type}"
    await db.update_group_settings(chat_id, {key: message.text})
    
    await state.clear()
    
    from bot.keyboards.groups import get_silent_messages_keyboard
    await message.answer(
        f"✅ <b>تم تحديث الرسالة بنجاح!</b>",
        reply_markup=get_silent_messages_keyboard(chat_id)
    )

@router.callback_query(F.data.startswith("silent_schedule_edit:"))
async def silent_schedule_edit_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    
    # Show Time Picker for CLOSE time first (Requested by User)
    from bot.keyboards.groups import get_time_selection_keyboard
    await callback.message.edit_text(
        "⏰ <b>ختر وقت إغلاق المجموعة (Close Time):</b>",
        reply_markup=get_time_selection_keyboard(chat_id, mode="close")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("time_pick:"))
async def time_pick_handler(callback: CallbackQuery):
    _, chat_id, mode, time_str = callback.data.split(":", 3)
    chat_id = int(chat_id)
    
    from bot.keyboards.groups import get_time_selection_keyboard
    
    if mode == "close":
        # Saved Close Time -> Ask for Open Time
        await db.update_group_settings(chat_id, {"silent.schedule.close_time": time_str})
        await callback.message.edit_text(
            f"✅ تم تحديد الإغلاق: `{time_str}`\n\n⏰ <b>الآن إختر وقت فتح المجموعة (Open Time):</b>",
            reply_markup=get_time_selection_keyboard(chat_id, mode="open")
        )
    elif mode == "open":
        # Saved Open Time -> Finish
        await db.update_group_settings(chat_id, {
            "silent.schedule.open_time": time_str,
            "silent.schedule.active": True  # Auto-activate when fully set
        })
        
        settings = await db.get_group_settings(chat_id)
        close_t = settings.get("silent", {}).get("schedule", {}).get("close_time")
        
        await callback.message.edit_text(
            f"✅ <b>تم تحديث الجدول بنجاح!</b>\n\n🔒 الإغلاق: `{close_t}`\n🔓 الفتح: `{time_str}`",
            reply_markup=get_silent_mode_keyboard(chat_id, settings)
        )
    
    await callback.answer()

from aiogram.fsm.context import FSMContext
from bot.states.groups import GroupSettingsStates
from bot.keyboards.groups import (
    get_main_settings_keyboard,
    get_media_settings_keyboard,
    get_silent_mode_keyboard,
    get_welcome_settings_keyboard,
    get_banned_words_keyboard,
    get_whitelist_keyboard
)

# ... (Previous toggle handlers) ...

@router.callback_query(F.data.startswith("toggle_welcome:"))
async def toggle_welcome_handler(callback: CallbackQuery):
    _, chat_id, param = callback.data.split(":") # param is 'enabled'
    chat_id = int(chat_id)
    
    settings = await db.get_group_settings(chat_id)
    current_state = settings["welcome_message"].get(param, True)
    new_state = not current_state
    
    await db.update_group_settings(chat_id, {f"welcome_message.{param}": new_state})
    
    updated_settings = await db.get_group_settings(chat_id)
    await callback.message.edit_text(
        "👋 <b>إعدادات الترحيب (Welcome Settings)</b>\n\nتفعيل أو تعطيل الترحيب وتعديل النص:",
        reply_markup=get_welcome_settings_keyboard(chat_id, updated_settings)
    )
    await callback.answer("تم التحديث ✅")

# -----------------------------------------------------------------------------
# 🚫 BANNED WORDS MANAGEMENT
# -----------------------------------------------------------------------------

@router.callback_query(F.data.startswith("settings_banned:"))
async def settings_banned_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    settings = await db.get_group_settings(chat_id)
    await callback.message.edit_text(
        "🚫 <b>الكلمات المحظورة (Banned Words)</b>\n\nاضغط على الكلمة لحذفها، أو أضف كلمة جديدة:",
        reply_markup=get_banned_words_keyboard(chat_id, settings)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("add_word:"))
async def add_word_prompt(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    await state.set_state(GroupSettingsStates.waiting_for_banned_word)
    await state.update_data(chat_id=chat_id, msg_id=callback.message.message_id) # Store msg to edit back
    
    await callback.message.edit_text(
        "📝 <b>أرسل الكلمة التي تريد حظرها الآن:</b>\n(أرسل 'الغاء' للإلغاء)",
        reply_markup=None
    )
    await callback.answer()

@router.message(GroupSettingsStates.waiting_for_banned_word)
async def add_word_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    
    if message.text.lower() == "الغاء":
        await state.clear()
        settings = await db.get_group_settings(chat_id)
        # Try to restore menu (sends new msg since old one is gone or hard to find if user chatted)
        await message.answer(
            "🚫 <b>تم الإلغاء.</b>\nالعودة للقائمة:",
            reply_markup=get_banned_words_keyboard(chat_id, settings)
        )
        return

    # Add word to DB
    word = message.text.strip()
    await db.db.groups.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"banned_words": word}}
    )
    
    await state.clear()
    settings = await db.get_group_settings(chat_id)
    await message.answer(
        f"✅ <b>تم إضافة الكلمة:</b> {word}\nالعودة للقائمة:",
        reply_markup=get_banned_words_keyboard(chat_id, settings)
    )

@router.callback_query(F.data.startswith("del_word:"))
async def delete_word_handler(callback: CallbackQuery):
    _, chat_id, word = callback.data.split(":")
    chat_id = int(chat_id)
    
    await db.db.groups.update_one(
        {"chat_id": chat_id},
        {"$pull": {"banned_words": word}}
    )
    
    settings = await db.get_group_settings(chat_id)
    await callback.message.edit_text(
        "🚫 <b>الكلمات المحظورة (Banned Words)</b>\n\nاضغط على الكلمة لحذفها، أو أضف كلمة جديدة:",
        reply_markup=get_banned_words_keyboard(chat_id, settings)
    )
    await callback.answer("تم الحذف 🗑️")

# -----------------------------------------------------------------------------
# 🏳️ WHITELIST MANAGEMENT
# -----------------------------------------------------------------------------

@router.callback_query(F.data.startswith("settings_whitelist:"))
async def settings_whitelist_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    settings = await db.get_group_settings(chat_id)
    await callback.message.edit_text(
        "🏳️ <b>القائمة البيضاء (Whitelist)</b>\n\nالأعضاء أو الروابط المستثناة:",
        reply_markup=get_whitelist_keyboard(chat_id, settings)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("add_whitelist:"))
async def add_whitelist_prompt(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    await state.set_state(GroupSettingsStates.waiting_for_whitelist_item)
    await state.update_data(chat_id=chat_id)
    
    await callback.message.edit_text(
        "📝 <b>أرسل المعرف (ID) أو الرابط للإضافة:</b>\n(أرسل 'الغاء' للإلغاء)",
        reply_markup=None
    )
    await callback.answer()

@router.message(GroupSettingsStates.waiting_for_whitelist_item)
async def add_whitelist_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    
    if message.text.lower() == "الغاء":
        await state.clear()
        settings = await db.get_group_settings(chat_id)
        await message.answer("🏳️ <b>تم الإلغاء.</b>", reply_markup=get_whitelist_keyboard(chat_id, settings))
        return

    item = message.text.strip()
    await db.db.groups.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"whitelist": item}}
    )
    
    await state.clear()
    settings = await db.get_group_settings(chat_id)
    await message.answer(
        f"✅ <b>تمت الإضافة:</b> {item}",
        reply_markup=get_whitelist_keyboard(chat_id, settings)
    )

@router.callback_query(F.data.startswith("del_whitelist:"))
async def delete_whitelist_handler(callback: CallbackQuery):
    _, chat_id, item = callback.data.split(":")
    chat_id = int(chat_id)
    
    await db.db.groups.update_one(
        {"chat_id": chat_id},
        {"$pull": {"whitelist": item}}
    )
    
    settings = await db.get_group_settings(chat_id)
    await callback.message.edit_text(
        "🏳️ <b>القائمة البيضاء (Whitelist)</b>\n\nالأعضاء أو الروابط المستثناة:",
        reply_markup=get_whitelist_keyboard(chat_id, settings)
    )
    await callback.message.edit_text(
        "🏳️ <b>القائمة البيضاء (Whitelist)</b>\n\nالأعضاء أو الروابط المستثناة:",
        reply_markup=get_whitelist_keyboard(chat_id, settings)
    )
    await callback.answer("تم الحذف 🗑️")

# -----------------------------------------------------------------------------
# 👋 WELCOME MESSAGE
# -----------------------------------------------------------------------------

@router.callback_query(F.data.startswith("settings_welcome:"))
async def settings_welcome_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    settings = await db.get_group_settings(chat_id)
    
    await callback.message.edit_text(
        "👋 <b>إعدادات الترحيب (Welcome Settings)</b>\n\nتفعيل أو تعطيل الترحيب وتعديل النص:",
        reply_markup=get_welcome_settings_keyboard(chat_id, settings)
    )
    await callback.answer()

@router.message(F.new_chat_members)
async def welcome_handler(message: Message):
    # Check if bot itself joined?
    for member in message.new_chat_members:
        if member.id == message.bot.id:
            # Bot joined -> Activate default? or just say hi.
            await message.reply("🤖 <b>أهلاً! أنا بوت إدارة المجموعات.</b>\nلتفعيل البوت، يجب أن أكون مشرفاً أولاً، ثم استخدم أمر /activate.")
            return

    # User joined
    settings = await db.get_group_settings(message.chat.id)
    if not settings.get("is_active"):
        return

    welcome = settings.get("welcome_message", {})
    if welcome.get("enabled", True):
        text = welcome.get("text", "مرحباً بك في المجموعة! 👋")
        
        for member in message.new_chat_members:
             user_text = text.replace("{user}", member.full_name).replace("{chat}", message.chat.title)
             try:
                 await message.answer(user_text)
             except:
                 pass

# -----------------------------------------------------------------------------
# 📜 RULES MANAGEMENT
# -----------------------------------------------------------------------------

@router.callback_query(F.data.startswith("settings_rules:"))
async def settings_rules_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    settings = await db.get_group_settings(chat_id)
    rules = settings.get("rules", "") or "— لا توجد قوانين مسجلة —"
    is_enabled = settings.get("rules_enabled", True)
    
    # Show current rules snippet
    snippet = rules[:100] + "..." if len(rules) > 100 else rules
    
    status_icon = "✅" if is_enabled else "❌"
    status_text = "مفعل (On)" if is_enabled else "معطل (Off)"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"الحالة: {status_icon} {status_text}", callback_data=f"toggle_rules:{chat_id}")],
        [InlineKeyboardButton(text="📝 تعديل القوانين (Edit)", callback_data=f"edit_rules:{chat_id}")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"back_to_main:{chat_id}")]
    ])
    
    await callback.message.edit_text(
        f"📜 <b>قوانين المجموعة (Rules)</b>\n\n📄 <b>النص الحالي:</b>\n<code>{snippet}</code>",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_rules:"))
async def toggle_rules_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    settings = await db.get_group_settings(chat_id)
    
    current = settings.get("rules_enabled", True)
    new_state = not current
    
    await db.update_group_settings(chat_id, {"rules_enabled": new_state})
    
    # Refresh
    # Reuse settings_rules_handler logic but we need to pass callback/message correctly.
    # Easiest: Call it or copy logic. calling handler with modified callback is tricky.
    # Just copy logic.
    
    updated_settings = await db.get_group_settings(chat_id)
    rules = updated_settings.get("rules", "") or "— لا توجد قوانين مسجلة —"
    is_enabled = updated_settings.get("rules_enabled", True)
    snippet = rules[:100] + "..." if len(rules) > 100 else rules
    
    status_icon = "✅" if is_enabled else "❌"
    status_text = "مفعل (On)" if is_enabled else "معطل (Off)"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"الحالة: {status_icon} {status_text}", callback_data=f"toggle_rules:{chat_id}")],
        [InlineKeyboardButton(text="📝 تعديل القوانين (Edit)", callback_data=f"edit_rules:{chat_id}")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"back_to_main:{chat_id}")]
    ])
    
    await callback.message.edit_text(
        f"📜 <b>قوانين المجموعة (Rules)</b>\n\n📄 <b>النص الحالي:</b>\n<code>{snippet}</code>",
        reply_markup=keyboard
    )
    await callback.answer(f"تم {status_text} القوانين")


@router.callback_query(F.data.startswith("edit_rules:"))
async def edit_rules_prompt(callback: CallbackQuery, state: FSMContext):
    logger.info(f"🔘 Edit Rules Clicked by {callback.from_user.id}") # DEBUG
    chat_id = int(callback.data.split(":")[1])
    await state.set_state(GroupSettingsStates.waiting_for_rules)
    await state.update_data(chat_id=chat_id)
    
    await callback.message.edit_text(
        "📝 <b>أرسل نص القوانين الجديد الآن:</b>\n(أرسل 'الغاء' للتراجع)",
        reply_markup=None
    )
    await callback.answer()

@router.message(GroupSettingsStates.waiting_for_rules)
async def save_rules_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    
    if message.text.lower() == "الغاء":
        await state.clear()
        await message.answer("❌ تم الإلغاء.")
        return

    # Update DB
    await db.update_group_settings(chat_id, {"rules": message.text})
    await state.clear()
    
    await message.answer("✅ <b>تم حفظ القوانين بنجاح!</b>")

# Public Command
@router.message(Command(commands=["rules", "قوانين"]))
async def rules_command(message: Message):
    settings = await db.get_group_settings(message.chat.id)
    
    # Check if enabled
    if not settings.get("rules_enabled", True):
        # Optional: Reply saying it's disabled? or ignore?
        # Usually ignore or small msg.
        await message.reply("🚫 <b>عرض القوانين معطل حالياً من قبل المشرفين.</b>")
        return

    rules = settings.get("rules")
    
    if rules:
        await message.reply(f"📜 <b>قوانين المجموعة:</b>\n\n{rules}")
    else:
        await message.reply("📜 <b>لا توجد قوانين مسجلة لهذه المجموعة حالياً.</b>")
    
    # Check Welcome settings edit
@router.callback_query(F.data.startswith("edit_welcome_text:"))
async def edit_welcome_prompt(callback: CallbackQuery, state: FSMContext):
    logger.info(f"🔘 Edit Welcome Clicked by {callback.from_user.id}") # DEBUG
    chat_id = int(callback.data.split(":")[1])
    await state.set_state(GroupSettingsStates.waiting_for_welcome_text)
    await state.update_data(chat_id=chat_id)
    
    await callback.message.edit_text(
        "📝 <b>أرسل نص الترحيب الجديد:</b>\nاستخدم <code>{user}</code> لاسم العضو و <code>{chat}</code> لاسم المجموعة.\n(أرسل 'الغاء' للتراجع)",
        reply_markup=None
    )
    await callback.answer()

@router.message(GroupSettingsStates.waiting_for_welcome_text)
async def save_welcome_text_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    
    if message.text.lower() == "الغاء":
        await state.clear()
        await message.answer("❌ تم الإلغاء.")
        return

    # Update DB
    await db.update_group_settings(chat_id, {"welcome_message.text": message.text})
    await state.clear()
    
    await message.answer("✅ <b>تم حفظ نص الترحيب بنجاح!</b>")
