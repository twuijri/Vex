"""
معالجات أزرار الترحيب

هذا الملف مسؤول عن معالجة الأزرار الخاصة بإدارة رسائل الترحيب
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.database.models import Group
from bot.keyboards.builders import build_welcome_settings_keyboard, build_cancel_keyboard
from bot.core.states import WelcomeStates
from bot.utils.constants import EMOJI_SUCCESS, EMOJI_ERROR

logger = logging.getLogger(__name__)
router = Router(name="welcome_callbacks")


@router.callback_query(F.data.startswith("group_settings:welcome:"))
async def show_welcome_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "الترحيب"
        يعرض قائمة إعدادات رسائل الترحيب
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
    
    السلوك:
        عرض إعدادات الترحيب مع الأزرار التفاعلية
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        is_active = group.welcome.active
        has_message = bool(group.welcome.message)
        buttons_count = len(group.welcome.buttons) if group.welcome.buttons else 0
        
        await callback.message.edit_text(
            f"🎊 **إعدادات الترحيب**\n\n"
            f"📌 المجموعة: {group.chat_title}\n"
            f"♻️ الحالة: {'مفعل ✅' if is_active else 'معطل ❌'}\n"
            f"📝 الرسالة: {'محفوظة ✅' if has_message else 'غير محفوظة ❌'}\n"
            f"🔘 الأزرار: {buttons_count}\n\n"
            f"اختر الإعداد المطلوب:",
            reply_markup=build_welcome_settings_keyboard(chat_id, is_active)
        )
        
        await callback.answer("🎊 إعدادات الترحيب")
        logger.info(f"User {callback.from_user.id} opened welcome settings for group {chat_id}")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_welcome_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("welcome:toggle:"))
async def toggle_welcome_status(callback: CallbackQuery):
    """
    الوصف:
        معالج تبديل حالة الترحيب (مفعل/معطل)
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        group.welcome.active = not group.welcome.active
        await group.save()
        
        status_text = "تم تفعيل" if group.welcome.active else "تم تعطيل"
        status_emoji = EMOJI_SUCCESS if group.welcome.active else EMOJI_ERROR
        
        logger.info(f"User {callback.from_user.id} toggled welcome to {group.welcome.active} for group {chat_id}")
        
        await callback.message.edit_reply_markup(
            reply_markup=build_welcome_settings_keyboard(chat_id, group.welcome.active)
        )
        await callback.answer(f"{status_emoji} {status_text} الترحيب")
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in toggle_welcome_status: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("welcome:show:"))
async def show_welcome_message(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "عرض الترحيب"
        يعرض رسالة الترحيب الحالية
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        if not group.welcome.message:
            await callback.answer("ℹ️ لم يتم تعيين رسالة ترحيب بعد", show_alert=True)
            return
        
        # عرض الرسالة مع الأزرار إن وجدت
        from aiogram.types import InlineKeyboardMarkup
        keyboard = None
        
        if group.welcome.buttons:
            buttons = []
            for btn in group.welcome.buttons:
                buttons.append([InlineKeyboardButton(text=btn['text'], url=btn['url'])])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.answer("📃 رسالة الترحيب")
        await callback.message.answer(
            f"📃 **رسالة الترحيب الحالية:**\n\n{group.welcome.message}",
            reply_markup=keyboard
        )
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_welcome_message: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("welcome:edit:"))
async def start_edit_welcome(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "تعديل الترحيب"
        يبدأ عملية تعديل رسالة الترحيب
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        
        await state.update_data(chat_id=chat_id)
        await state.set_state(WelcomeStates.waiting_for_message)
        
        await callback.message.edit_text(
            f"📝 **تعديل رسالة الترحيب**\n\n"
            f"أرسل الرسالة الجديدة:\n\n"
            f"ℹ️ يمكنك استخدام:\n"
            f"• {{name}} - اسم العضو\n"
            f"• {{username}} - معرف العضو\n"
            f"• {{mention}} - منشن العضو\n"
            f"• {{group}} - اسم المجموعة\n"
            f"• Markdown للتنسيق",
            reply_markup=build_cancel_keyboard()
        )
        
        await callback.answer("✍️ أرسل الرسالة")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_edit_welcome: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.message(WelcomeStates.waiting_for_message)
async def process_welcome_message(message: Message, state: FSMContext):
    """
    الوصف:
        معالج استقبال رسالة الترحيب من المستخدم
    """
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")
        
        if not chat_id:
            await message.answer("❌ حدث خطأ")
            await state.clear()
            return
        
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await message.answer("❌ المجموعة غير موجودة")
            await state.clear()
            return
        
        new_message = message.text.strip()
        group.welcome.message = new_message
        await group.save()
        
        logger.info(f"User {message.from_user.id} updated welcome message for group {chat_id}")
        
        await message.answer(
            f"{EMOJI_SUCCESS} **تم تحديث رسالة الترحيب**\n\n"
            f"الرسالة الجديدة:\n{new_message}"
        )
        
        await state.clear()
        
        await message.answer(
            "🎊 **إعدادات الترحيب**\n\nاختر الإعداد المطلوب:",
            reply_markup=build_welcome_settings_keyboard(chat_id, group.welcome.active)
        )
        
    except Exception as e:
        logger.error(f"Error in process_welcome_message: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.callback_query(F.data.startswith("welcome:add_button:"))
async def start_add_welcome_button(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "إضافة زر"
        يبدأ عملية إضافة زر مخصص لرسالة الترحيب
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        
        await state.update_data(chat_id=chat_id)
        await state.set_state(WelcomeStates.waiting_for_button_text)
        
        await callback.message.edit_text(
            f"➕ **إضافة زر للترحيب**\n\n"
            f"أرسل نص الزر:\n"
            f"مثال: قوانين المجموعة",
            reply_markup=build_cancel_keyboard()
        )
        
        await callback.answer("✍️ أرسل نص الزر")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_add_welcome_button: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.message(WelcomeStates.waiting_for_button_text)
async def process_button_text(message: Message, state: FSMContext):
    """
    الوصف:
        معالج استقبال نص الزر
    """
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")
        
        if not chat_id:
            await message.answer("❌ حدث خطأ")
            await state.clear()
            return
        
        button_text = message.text.strip()
        
        await state.update_data(button_text=button_text)
        await state.set_state(WelcomeStates.waiting_for_button_url)
        
        await message.answer(
            f"✅ نص الزر: {button_text}\n\n"
            f"الآن أرسل رابط الزر:\n"
            f"مثال: https://t.me/channel"
        )
        
    except Exception as e:
        logger.error(f"Error in process_button_text: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.message(WelcomeStates.waiting_for_button_url)
async def process_button_url(message: Message, state: FSMContext):
    """
    الوصف:
        معالج استقبال رابط الزر وحفظه
    """
    try:
        data = await state.get_data()
        chat_id = data.get("chat_id")
        button_text = data.get("button_text")
        
        if not chat_id or not button_text:
            await message.answer("❌ حدث خطأ")
            await state.clear()
            return
        
        button_url = message.text.strip()
        
        # التحقق من صحة الرابط
        if not button_url.startswith(("http://", "https://", "tg://")):
            await message.answer("❌ الرابط غير صحيح. يجب أن يبدأ بـ http:// أو https://")
            return
        
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await message.answer("❌ المجموعة غير موجودة")
            await state.clear()
            return
        
        # إضافة الزر
        if not group.welcome.buttons:
            group.welcome.buttons = []
        
        group.welcome.buttons.append({
            "text": button_text,
            "url": button_url
        })
        
        await group.save()
        
        logger.info(f"User {message.from_user.id} added welcome button for group {chat_id}")
        
        await message.answer(
            f"{EMOJI_SUCCESS} **تم إضافة الزر بنجاح!**\n\n"
            f"📝 النص: {button_text}\n"
            f"🔗 الرابط: {button_url}"
        )
        
        await state.clear()
        
        await message.answer(
            "🎊 **إعدادات الترحيب**\n\nاختر الإعداد المطلوب:",
            reply_markup=build_welcome_settings_keyboard(chat_id, group.welcome.active)
        )
        
    except Exception as e:
        logger.error(f"Error in process_button_url: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.callback_query(F.data.startswith("welcome:clear_buttons:"))
async def clear_welcome_buttons(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "حذف الأزرار"
        يحذف جميع الأزرار المخصصة من رسالة الترحيب
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        if not group.welcome.buttons:
            await callback.answer("ℹ️ لا توجد أزرار لحذفها", show_alert=True)
            return
        
        buttons_count = len(group.welcome.buttons)
        group.welcome.buttons = []
        await group.save()
        
        logger.info(f"User {callback.from_user.id} cleared welcome buttons for group {chat_id}")
        
        await callback.answer(f"{EMOJI_SUCCESS} تم حذف {buttons_count} زر")
        
        await callback.message.edit_reply_markup(
            reply_markup=build_welcome_settings_keyboard(chat_id, group.welcome.active)
        )
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in clear_welcome_buttons: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


def register_callbacks(dp):
    """
    الوصف:
        تسجيل معالجات أزرار الترحيب في الـ Dispatcher
    """
    dp.include_router(router)
