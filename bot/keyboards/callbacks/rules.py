"""
معالجات أزرار القوانين

هذا الملف مسؤول عن معالجة الأزرار الخاصة بإدارة قوانين المجموعة
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from bot.database.models import Group
from bot.keyboards.builders import build_rules_settings_keyboard, build_cancel_keyboard
from bot.core.states import RulesStates
from bot.utils.constants import EMOJI_SUCCESS, EMOJI_ERROR

logger = logging.getLogger(__name__)
router = Router(name="rules_callbacks")


@router.callback_query(F.data.startswith("group_settings:rules:"))
async def show_rules_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "القوانين"
        يعرض قائمة إعدادات قوانين المجموعة
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        is_active = group.rules.active
        has_rules = bool(group.rules.text)
        buttons_count = len(group.rules.buttons) if group.rules.buttons else 0
        
        # معلومات الصلاحيات
        send_in_group = "المجموعة" if group.rules.send_in_group else "الخاص"
        admin_only = "المشرفين فقط" if group.rules.admin_only else "الجميع"
        
        await callback.message.edit_text(
            f"🚩 **إعدادات القوانين**\n\n"
            f"📌 المجموعة: {group.chat_title}\n"
            f"♻️ الحالة: {'مفعل ✅' if is_active else 'معطل ❌'}\n"
            f"📝 القوانين: {'محفوظة ✅' if has_rules else 'غير محفوظة ❌'}\n"
            f"🔘 الأزرار: {buttons_count}\n"
            f"📍 مكان الإرسال: {send_in_group}\n"
            f"🔐 الصلاحيات: {admin_only}\n\n"
            f"اختر الإعداد المطلوب:",
            reply_markup=build_rules_settings_keyboard(chat_id, is_active)
        )
        
        await callback.answer("🚩 إعدادات القوانين")
        logger.info(f"User {callback.from_user.id} opened rules settings for group {chat_id}")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_rules_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("rules:toggle:"))
async def toggle_rules_status(callback: CallbackQuery):
    """
    الوصف:
        معالج تبديل حالة القوانين (مفعل/معطل)
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        group.rules.active = not group.rules.active
        await group.save()
        
        status_text = "تم تفعيل" if group.rules.active else "تم تعطيل"
        status_emoji = EMOJI_SUCCESS if group.rules.active else EMOJI_ERROR
        
        logger.info(f"User {callback.from_user.id} toggled rules to {group.rules.active} for group {chat_id}")
        
        await callback.message.edit_reply_markup(
            reply_markup=build_rules_settings_keyboard(chat_id, group.rules.active)
        )
        await callback.answer(f"{status_emoji} {status_text} القوانين")
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in toggle_rules_status: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("rules:show:"))
async def show_rules_text(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "عرض القوانين"
        يعرض نص القوانين الحالي
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        if not group.rules.text:
            await callback.answer("ℹ️ لم يتم تعيين قوانين بعد", show_alert=True)
            return
        
        # عرض القوانين مع الأزرار إن وجدت
        keyboard = None
        
        if group.rules.buttons:
            buttons = []
            for btn in group.rules.buttons:
                buttons.append([InlineKeyboardButton(text=btn['text'], url=btn['url'])])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.answer("📃 قوانين المجموعة")
        await callback.message.answer(
            f"📃 **قوانين المجموعة:**\n\n{group.rules.text}",
            reply_markup=keyboard
        )
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_rules_text: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("rules:edit:"))
async def start_edit_rules(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "تعديل القوانين"
        يبدأ عملية تعديل نص القوانين
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        
        await state.update_data(chat_id=chat_id)
        await state.set_state(RulesStates.waiting_for_message)
        
        await callback.message.edit_text(
            f"📝 **تعديل القوانين**\n\n"
            f"أرسل نص القوانين الجديد:\n\n"
            f"ℹ️ يمكنك استخدام:\n"
            f"• {{group}} - اسم المجموعة\n"
            f"• Markdown للتنسيق\n"
            f"• أرقام للترتيب",
            reply_markup=build_cancel_keyboard()
        )
        
        await callback.answer("✍️ أرسل القوانين")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_edit_rules: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.message(RulesStates.waiting_for_message)
async def process_rules_text(message: Message, state: FSMContext):
    """
    الوصف:
        معالج استقبال نص القوانين من المستخدم
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
        
        new_rules = message.text.strip()
        group.rules.text = new_rules
        await group.save()
        
        logger.info(f"User {message.from_user.id} updated rules for group {chat_id}")
        
        await message.answer(
            f"{EMOJI_SUCCESS} **تم تحديث القوانين**\n\n"
            f"النص الجديد:\n{new_rules[:200]}{'...' if len(new_rules) > 200 else ''}"
        )
        
        await state.clear()
        
        await message.answer(
            "🚩 **إعدادات القوانين**\n\nاختر الإعداد المطلوب:",
            reply_markup=build_rules_settings_keyboard(chat_id, group.rules.active)
        )
        
    except Exception as e:
        logger.error(f"Error in process_rules_text: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.callback_query(F.data.startswith("rules:permissions:"))
async def show_rules_permissions(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "الصلاحيات"
        يعرض إعدادات صلاحيات عرض القوانين
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        admin_only_status = "✅" if group.rules.admin_only else "❌"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{admin_only_status} المشرفين فقط",
                callback_data=f"rules:toggle_admin_only:{chat_id}"
            )],
            [InlineKeyboardButton(text="🔙 الرجوع", callback_data=f"group_settings:rules:{chat_id}")]
        ])
        
        await callback.message.edit_text(
            f"🔐 **صلاحيات القوانين**\n\n"
            f"📌 المجموعة: {group.chat_title}\n\n"
            f"{'✅' if group.rules.admin_only else '❌'} المشرفين فقط: "
            f"{'مفعل' if group.rules.admin_only else 'معطل'}\n\n"
            f"ℹ️ إذا كان مفعل، فقط المشرفين يمكنهم استخدام أمر /rules",
            reply_markup=keyboard
        )
        
        await callback.answer("🔐 صلاحيات القوانين")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_rules_permissions: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("rules:toggle_admin_only:"))
async def toggle_admin_only(callback: CallbackQuery):
    """
    الوصف:
        معالج تبديل صلاحية "المشرفين فقط"
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        group.rules.admin_only = not group.rules.admin_only
        await group.save()
        
        status_text = "مفعل" if group.rules.admin_only else "معطل"
        status_emoji = EMOJI_SUCCESS if group.rules.admin_only else EMOJI_ERROR
        
        logger.info(f"User {callback.from_user.id} toggled admin_only to {group.rules.admin_only} for group {chat_id}")
        
        # تحديث الأزرار
        admin_only_status = "✅" if group.rules.admin_only else "❌"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{admin_only_status} المشرفين فقط",
                callback_data=f"rules:toggle_admin_only:{chat_id}"
            )],
            [InlineKeyboardButton(text="🔙 الرجوع", callback_data=f"group_settings:rules:{chat_id}")]
        ])
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer(f"{status_emoji} المشرفين فقط: {status_text}")
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in toggle_admin_only: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("rules:place:"))
async def show_rules_place(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "مكان الإرسال"
        يعرض إعدادات مكان إرسال القوانين
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        send_in_group_status = "✅" if group.rules.send_in_group else "❌"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{send_in_group_status} إرسال في المجموعة",
                callback_data=f"rules:toggle_place:{chat_id}"
            )],
            [InlineKeyboardButton(text="🔙 الرجوع", callback_data=f"group_settings:rules:{chat_id}")]
        ])
        
        await callback.message.edit_text(
            f"📍 **مكان إرسال القوانين**\n\n"
            f"📌 المجموعة: {group.chat_title}\n\n"
            f"{'✅' if group.rules.send_in_group else '❌'} إرسال في المجموعة: "
            f"{'مفعل' if group.rules.send_in_group else 'معطل'}\n\n"
            f"ℹ️ إذا كان مفعل، سيتم إرسال القوانين في المجموعة\n"
            f"إذا كان معطل، سيتم إرسالها في الخاص",
            reply_markup=keyboard
        )
        
        await callback.answer("📍 مكان الإرسال")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_rules_place: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("rules:toggle_place:"))
async def toggle_send_place(callback: CallbackQuery):
    """
    الوصف:
        معالج تبديل مكان إرسال القوانين
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        group.rules.send_in_group = not group.rules.send_in_group
        await group.save()
        
        place_text = "المجموعة" if group.rules.send_in_group else "الخاص"
        
        logger.info(f"User {callback.from_user.id} toggled send_in_group to {group.rules.send_in_group} for group {chat_id}")
        
        # تحديث الأزرار
        send_in_group_status = "✅" if group.rules.send_in_group else "❌"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{send_in_group_status} إرسال في المجموعة",
                callback_data=f"rules:toggle_place:{chat_id}"
            )],
            [InlineKeyboardButton(text="🔙 الرجوع", callback_data=f"group_settings:rules:{chat_id}")]
        ])
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer(f"📍 مكان الإرسال: {place_text}")
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in toggle_send_place: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("rules:add_button:"))
async def start_add_rules_button(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "إضافة زر"
        يبدأ عملية إضافة زر مخصص للقوانين
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        
        await state.update_data(chat_id=chat_id)
        await state.set_state(RulesStates.waiting_for_button_text)
        
        await callback.message.edit_text(
            f"➕ **إضافة زر للقوانين**\n\n"
            f"أرسل نص الزر:\n"
            f"مثال: قناة المجموعة",
            reply_markup=build_cancel_keyboard()
        )
        
        await callback.answer("✍️ أرسل نص الزر")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_add_rules_button: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.message(RulesStates.waiting_for_button_text)
async def process_rules_button_text(message: Message, state: FSMContext):
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
        await state.set_state(RulesStates.waiting_for_button_url)
        
        await message.answer(
            f"✅ نص الزر: {button_text}\n\n"
            f"الآن أرسل رابط الزر:\n"
            f"مثال: https://t.me/channel"
        )
        
    except Exception as e:
        logger.error(f"Error in process_rules_button_text: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.message(RulesStates.waiting_for_button_url)
async def process_rules_button_url(message: Message, state: FSMContext):
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
        if not group.rules.buttons:
            group.rules.buttons = []
        
        group.rules.buttons.append({
            "text": button_text,
            "url": button_url
        })
        
        await group.save()
        
        logger.info(f"User {message.from_user.id} added rules button for group {chat_id}")
        
        await message.answer(
            f"{EMOJI_SUCCESS} **تم إضافة الزر بنجاح!**\n\n"
            f"📝 النص: {button_text}\n"
            f"🔗 الرابط: {button_url}"
        )
        
        await state.clear()
        
        await message.answer(
            "🚩 **إعدادات القوانين**\n\nاختر الإعداد المطلوب:",
            reply_markup=build_rules_settings_keyboard(chat_id, group.rules.active)
        )
        
    except Exception as e:
        logger.error(f"Error in process_rules_button_url: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.callback_query(F.data.startswith("rules:clear_buttons:"))
async def clear_rules_buttons(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "حذف الأزرار"
        يحذف جميع الأزرار المخصصة من القوانين
    """
    try:
        chat_id = int(callback.data.split(":", 2)[2])
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        if not group.rules.buttons:
            await callback.answer("ℹ️ لا توجد أزرار لحذفها", show_alert=True)
            return
        
        buttons_count = len(group.rules.buttons)
        group.rules.buttons = []
        await group.save()
        
        logger.info(f"User {callback.from_user.id} cleared rules buttons for group {chat_id}")
        
        await callback.answer(f"{EMOJI_SUCCESS} تم حذف {buttons_count} زر")
        
        await callback.message.edit_reply_markup(
            reply_markup=build_rules_settings_keyboard(chat_id, group.rules.active)
        )
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in clear_rules_buttons: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


def register_callbacks(dp):
    """
    الوصف:
        تسجيل معالجات أزرار القوانين في الـ Dispatcher
    """
    dp.include_router(router)
