"""
معالجات أزرار الكلمات المحظورة والمسموح بها

هذا الملف مسؤول عن معالجة الأزرار الخاصة بإدارة الكلمات المحظورة والمسموح بها
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.database.models import Group
from bot.keyboards.builders import (
    build_words_settings_keyboard,
    build_cancel_keyboard,
    build_confirmation_keyboard
)
from bot.core.states import BlockedWordsStates, AllowedWordsStates
from bot.utils.constants import EMOJI_SUCCESS, EMOJI_ERROR

logger = logging.getLogger(__name__)

# إنشاء Router للمعالجات
router = Router(name="words_callbacks")


@router.callback_query(F.data.startswith("group_settings:blocked_words:"))
async def show_blocked_words_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "الكلمات المحظورة"
        يعرض قائمة إعدادات الكلمات المحظورة
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "group_settings:blocked_words:{chat_id}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id من callback.data
        2. جلب إعدادات الكلمات المحظورة من قاعدة البيانات
        3. عرض قائمة الإعدادات:
           - حالة النظام (مفعل/معطل)
           - عرض الكلمات المحظورة
           - إضافة كلمة جديدة
           - حذف كلمة
           - حذف جميع الكلمات
    
    الملفات المرتبطة:
        - bot/database/models.py: Group.blocked_words
        - bot/keyboards/builders.py: build_words_settings_keyboard
        - bot/handlers/groups/filters.py: تطبيق فلتر الكلمات
    
    مثال:
        المشرف يضغط على: "🚫 الكلمات المحظورة"
        البوت يعرض: قائمة إعدادات الكلمات المحظورة
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # الحصول على حالة النظام
        is_active = group.blocked_words.active
        words_count = len(group.blocked_words.words)
        
        # عرض إعدادات الكلمات المحظورة
        await callback.message.edit_text(
            f"🚫 **الكلمات المحظورة**\n\n"
            f"📌 المجموعة: {group.chat_title}\n"
            f"📊 عدد الكلمات: {words_count}\n"
            f"♻️ الحالة: {'مفعل ✅' if is_active else 'معطل ❌'}\n\n"
            f"اختر الإجراء المطلوب:",
            reply_markup=build_words_settings_keyboard(chat_id, "blocked", is_active)
        )
        
        await callback.answer("🚫 الكلمات المحظورة")
        
        logger.info(f"User {callback.from_user.id} opened blocked words for group {chat_id}")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_blocked_words_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("group_settings:allowed_words:"))
async def show_allowed_words_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "الكلمات المسموح بها"
        يعرض قائمة إعدادات الكلمات المسموح بها
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "group_settings:allowed_words:{chat_id}"
    
    الإرجاع:
        None
    
    السلوك:
        مشابه لـ show_blocked_words_settings لكن للكلمات المسموح بها
        الكلمات المسموح بها تستثنى من الفلترة حتى لو كانت محظورة
    
    الملفات المرتبطة:
        - bot/database/models.py: Group.allowed_words
        - bot/keyboards/builders.py: build_words_settings_keyboard
    
    مثال:
        المشرف يضغط على: "✅ الكلمات المسموح بها"
        البوت يعرض: قائمة إعدادات الكلمات المسموح بها
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # الحصول على حالة النظام
        is_active = group.allowed_words.active
        words_count = len(group.allowed_words.words)
        
        # عرض إعدادات الكلمات المسموح بها
        await callback.message.edit_text(
            f"✅ **الكلمات المسموح بها**\n\n"
            f"📌 المجموعة: {group.chat_title}\n"
            f"📊 عدد الكلمات: {words_count}\n"
            f"♻️ الحالة: {'مفعل ✅' if is_active else 'معطل ❌'}\n\n"
            f"ℹ️ الكلمات المسموح بها تستثنى من الفلترة\n"
            f"حتى لو كانت في قائمة الكلمات المحظورة\n\n"
            f"اختر الإجراء المطلوب:",
            reply_markup=build_words_settings_keyboard(chat_id, "allowed", is_active)
        )
        
        await callback.answer("✅ الكلمات المسموح بها")
        
        logger.info(f"User {callback.from_user.id} opened allowed words for group {chat_id}")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_allowed_words_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("words:toggle_status:"))
async def toggle_words_status(callback: CallbackQuery):
    """
    الوصف:
        معالج تبديل حالة نظام الكلمات (مفعل/معطل)
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "words:toggle_status:{chat_id}:{words_type}"
            - words_type: "blocked" أو "allowed"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id و words_type من callback.data
        2. تبديل حالة النظام (active = True/False)
        3. حفظ التغيير في قاعدة البيانات
        4. تحديث الأزرار
    
    مثال:
        المشرف يضغط على: "♻️ حالة النظام: ✅"
        البوت ينفذ: تغيير الحالة إلى "❌"
        البوت يعرض: Toast "❌ تم تعطيل النظام"
    """
    try:
        # استخراج البيانات
        parts = callback.data.split(":", 3)
        chat_id = int(parts[2])
        words_type = parts[3]  # "blocked" or "allowed"
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # تبديل الحالة
        if words_type == "blocked":
            current_status = group.blocked_words.active
            group.blocked_words.active = not current_status
            new_status = group.blocked_words.active
        else:  # allowed
            current_status = group.allowed_words.active
            group.allowed_words.active = not current_status
            new_status = group.allowed_words.active
        
        # حفظ التغيير
        await group.save()
        
        # تحديد نص الإشعار
        status_text = "تم تفعيل" if new_status else "تم تعطيل"
        status_emoji = EMOJI_SUCCESS if new_status else EMOJI_ERROR
        words_name = "الكلمات المحظورة" if words_type == "blocked" else "الكلمات المسموح بها"
        
        logger.info(
            f"User {callback.from_user.id} toggled {words_type} words status "
            f"to {new_status} for group {chat_id}"
        )
        
        # تحديث الأزرار
        await callback.message.edit_reply_markup(
            reply_markup=build_words_settings_keyboard(chat_id, words_type, new_status)
        )
        
        # إرسال إشعار
        await callback.answer(f"{status_emoji} {status_text} {words_name}")
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in toggle_words_status: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("words:list:"))
async def list_words(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "عرض الكلمات"
        يعرض قائمة بجميع الكلمات المحظورة أو المسموح بها
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "words:list:{chat_id}:{words_type}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id و words_type من callback.data
        2. جلب قائمة الكلمات من قاعدة البيانات
        3. عرض الكلمات في رسالة منسقة
        4. إذا لا توجد كلمات: عرض رسالة مناسبة
    
    مثال:
        المشرف يضغط على: "📃 عرض الكلمات"
        البوت يعرض: قائمة الكلمات أو "لا توجد كلمات"
    """
    try:
        # استخراج البيانات
        parts = callback.data.split(":", 3)
        chat_id = int(parts[2])
        words_type = parts[3]
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # الحصول على قائمة الكلمات
        if words_type == "blocked":
            words = group.blocked_words.words
            title = "🚫 الكلمات المحظورة"
        else:
            words = group.allowed_words.words
            title = "✅ الكلمات المسموح بها"
        
        if not words:
            await callback.answer(
                f"ℹ️ لا توجد كلمات في القائمة",
                show_alert=True
            )
            return
        
        # بناء قائمة الكلمات
        words_list = "\n".join([f"• {word}" for word in words])
        
        # عرض القائمة
        await callback.answer(
            f"{title}\n\n{words_list}\n\nالعدد: {len(words)}",
            show_alert=True
        )
        
        logger.info(f"User {callback.from_user.id} viewed {words_type} words for group {chat_id}")
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in list_words: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("words:add:"))
async def start_add_word(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "إضافة كلمة"
        يبدأ عملية إضافة كلمة جديدة باستخدام FSM
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "words:add:{chat_id}:{words_type}"
        state (FSMContext): حالة FSM لحفظ البيانات
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id و words_type من callback.data
        2. حفظ البيانات في FSM state
        3. تغيير حالة FSM إلى WordsStates.waiting_for_word
        4. طلب من المستخدم إرسال الكلمة
    
    الملفات المرتبطة:
        - bot/core/states.py: WordsStates
        - process_add_word: الدالة التي تستقبل الكلمة
    
    مثال:
        المشرف يضغط على: "➕ إضافة كلمة"
        البوت يعرض: "أرسل الكلمة التي تريد إضافتها"
    """
    try:
        # استخراج البيانات
        parts = callback.data.split(":", 3)
        chat_id = int(parts[2])
        words_type = parts[3]
        
        # حفظ البيانات في state
        await state.update_data(
            chat_id=chat_id,
            words_type=words_type
        )
        
        # تغيير حالة FSM
        if words_type == "blocked":
            await state.set_state(BlockedWordsStates.waiting_for_word_to_add)
        else:
            await state.set_state(AllowedWordsStates.waiting_for_word_to_add)
        
        # طلب الكلمة من المستخدم
        words_name = "المحظورة" if words_type == "blocked" else "المسموح بها"
        await callback.message.edit_text(
            f"➕ **إضافة كلمة {words_name}**\n\n"
            f"أرسل الكلمة التي تريد إضافتها:\n\n"
            f"ℹ️ يمكنك إرسال عدة كلمات مفصولة بفواصل\n"
            f"مثال: كلمة1, كلمة2, كلمة3",
            reply_markup=build_cancel_keyboard()
        )
        
        await callback.answer("✍️ أرسل الكلمة")
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_add_word: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.message(BlockedWordsStates.waiting_for_word_to_add)
@router.message(AllowedWordsStates.waiting_for_word_to_add)
async def process_add_word(message: Message, state: FSMContext):
    """
    الوصف:
        معالج استقبال الكلمة من المستخدم وإضافتها
    
    المعاملات:
        message (Message): رسالة المستخدم التي تحتوي على الكلمة
        state (FSMContext): حالة FSM للحصول على البيانات المحفوظة
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج البيانات من FSM state
        2. استخراج الكلمات من الرسالة (مفصولة بفواصل)
        3. إضافة الكلمات إلى قاعدة البيانات
        4. تجنب التكرار (لا تضيف كلمة موجودة مسبقاً)
        5. عرض رسالة نجاح مع عدد الكلمات المضافة
        6. إنهاء حالة FSM
        7. العودة لقائمة إعدادات الكلمات
    
    مثال:
        المستخدم يرسل: "كلمة1, كلمة2, كلمة3"
        البوت يضيف: الكلمات الثلاث
        البوت يعرض: "✅ تم إضافة 3 كلمات"
    """
    try:
        # الحصول على البيانات من state
        data = await state.get_data()
        chat_id = data.get("chat_id")
        words_type = data.get("words_type")
        
        if not chat_id or not words_type:
            await message.answer("❌ حدث خطأ، يرجى المحاولة مرة أخرى")
            await state.clear()
            return
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await message.answer("❌ المجموعة غير موجودة")
            await state.clear()
            return
        
        # استخراج الكلمات من الرسالة
        text = message.text.strip()
        new_words = [word.strip() for word in text.split(",")]
        new_words = [word for word in new_words if word]  # إزالة الفراغات
        
        if not new_words:
            await message.answer("❌ لم يتم إرسال أي كلمات صحيحة")
            return
        
        # إضافة الكلمات
        added_count = 0
        if words_type == "blocked":
            for word in new_words:
                if word not in group.blocked_words.words:
                    group.blocked_words.words.append(word)
                    added_count += 1
        else:  # allowed
            for word in new_words:
                if word not in group.allowed_words.words:
                    group.allowed_words.words.append(word)
                    added_count += 1
        
        # حفظ التغييرات
        await group.save()
        
        logger.info(
            f"User {message.from_user.id} added {added_count} {words_type} words "
            f"to group {chat_id}"
        )
        
        # عرض رسالة نجاح
        words_name = "محظورة" if words_type == "blocked" else "مسموح بها"
        await message.answer(
            f"{EMOJI_SUCCESS} **تم إضافة {added_count} كلمة {words_name}**\n\n"
            f"إجمالي الكلمات: {len(group.blocked_words.words if words_type == 'blocked' else group.allowed_words.words)}"
        )
        
        # إنهاء حالة FSM
        await state.clear()
        
        # العودة لقائمة الإعدادات
        is_active = group.blocked_words.active if words_type == "blocked" else group.allowed_words.active
        await message.answer(
            f"{'🚫' if words_type == 'blocked' else '✅'} **الكلمات ال{words_name}**\n\n"
            f"اختر الإجراء المطلوب:",
            reply_markup=build_words_settings_keyboard(chat_id, words_type, is_active)
        )
        
    except Exception as e:
        logger.error(f"Error in process_add_word: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ أثناء إضافة الكلمات")
        await state.clear()


@router.callback_query(F.data.startswith("words:remove:"))
async def start_remove_word(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "حذف كلمة"
        يبدأ عملية حذف كلمة باستخدام FSM
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        مشابه لـ start_add_word لكن للحذف
    """
    try:
        # استخراج البيانات
        parts = callback.data.split(":", 3)
        chat_id = int(parts[2])
        words_type = parts[3]
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # التحقق من وجود كلمات
        words = group.blocked_words.words if words_type == "blocked" else group.allowed_words.words
        
        if not words:
            await callback.answer("ℹ️ لا توجد كلمات للحذف", show_alert=True)
            return
        
        # حفظ البيانات في state
        await state.update_data(
            chat_id=chat_id,
            words_type=words_type
        )
        
        # تغيير حالة FSM
        if words_type == "blocked":
            await state.set_state(BlockedWordsStates.waiting_for_word_to_remove)
        else:
            await state.set_state(AllowedWordsStates.waiting_for_word_to_remove)
        
        # طلب الكلمة من المستخدم
        words_name = "المحظورة" if words_type == "blocked" else "المسموح بها"
        words_list = "\n".join([f"• {word}" for word in words[:10]])  # أول 10 كلمات
        more_text = f"\n... و {len(words) - 10} كلمة أخرى" if len(words) > 10 else ""
        
        await callback.message.edit_text(
            f"➖ **حذف كلمة {words_name}**\n\n"
            f"الكلمات الحالية:\n{words_list}{more_text}\n\n"
            f"أرسل الكلمة التي تريد حذفها:",
            reply_markup=build_cancel_keyboard()
        )
        
        await callback.answer("✍️ أرسل الكلمة")
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_remove_word: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.message(BlockedWordsStates.waiting_for_word_to_remove)
@router.message(AllowedWordsStates.waiting_for_word_to_remove)
async def process_remove_word(message: Message, state: FSMContext):
    """
    الوصف:
        معالج استقبال الكلمة وحذفها
    
    المعاملات:
        message (Message): رسالة المستخدم
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج البيانات من state
        2. البحث عن الكلمة في القائمة
        3. حذف الكلمة إذا وجدت
        4. عرض رسالة نجاح أو فشل
    """
    try:
        # الحصول على البيانات
        data = await state.get_data()
        chat_id = data.get("chat_id")
        words_type = data.get("words_type")
        
        if not chat_id or not words_type:
            await message.answer("❌ حدث خطأ")
            await state.clear()
            return
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await message.answer("❌ المجموعة غير موجودة")
            await state.clear()
            return
        
        # استخراج الكلمة
        word = message.text.strip()
        
        # حذف الكلمة
        removed = False
        if words_type == "blocked":
            if word in group.blocked_words.words:
                group.blocked_words.words.remove(word)
                removed = True
        else:
            if word in group.allowed_words.words:
                group.allowed_words.words.remove(word)
                removed = True
        
        if removed:
            await group.save()
            
            logger.info(
                f"User {message.from_user.id} removed word '{word}' "
                f"from {words_type} words in group {chat_id}"
            )
            
            await message.answer(f"{EMOJI_SUCCESS} تم حذف الكلمة: {word}")
        else:
            await message.answer(f"{EMOJI_ERROR} الكلمة غير موجودة في القائمة")
        
        # إنهاء FSM
        await state.clear()
        
        # العودة للإعدادات
        is_active = group.blocked_words.active if words_type == "blocked" else group.allowed_words.active
        words_name = "المحظورة" if words_type == "blocked" else "المسموح بها"
        await message.answer(
            f"{'🚫' if words_type == 'blocked' else '✅'} **الكلمات ال{words_name}**\n\n"
            f"اختر الإجراء المطلوب:",
            reply_markup=build_words_settings_keyboard(chat_id, words_type, is_active)
        )
        
    except Exception as e:
        logger.error(f"Error in process_remove_word: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.callback_query(F.data.startswith("words:remove_all:"))
async def confirm_remove_all_words(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "حذف جميع الكلمات"
        يطلب تأكيد قبل الحذف
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
    
    الإرجاع:
        None
    
    السلوك:
        1. عرض رسالة تأكيد
        2. إضافة أزرار (نعم/إلغاء)
    """
    try:
        # استخراج البيانات
        parts = callback.data.split(":", 3)
        chat_id = parts[2]
        words_type = parts[3]
        
        # عرض رسالة التأكيد
        words_name = "المحظورة" if words_type == "blocked" else "المسموح بها"
        await callback.message.edit_text(
            f"⚠️ **تأكيد حذف جميع الكلمات ال{words_name}**\n\n"
            f"هل أنت متأكد من حذف جميع الكلمات؟\n"
            f"هذا الإجراء لا يمكن التراجع عنه!",
            reply_markup=build_confirmation_keyboard("remove_all_words", f"{chat_id}:{words_type}")
        )
        
        await callback.answer("⚠️ تأكيد الحذف")
        
    except Exception as e:
        logger.error(f"Error in confirm_remove_all_words: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("confirm:remove_all_words:"))
async def remove_all_words(callback: CallbackQuery):
    """
    الوصف:
        معالج تأكيد حذف جميع الكلمات
        ينفذ عملية الحذف الفعلية
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "confirm:remove_all_words:{chat_id}:{words_type}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج البيانات
        2. حذف جميع الكلمات من القائمة
        3. حفظ التغيير
        4. عرض رسالة نجاح
    """
    try:
        # استخراج البيانات
        parts = callback.data.split(":", 3)
        data_parts = parts[2].split(":")
        chat_id = int(data_parts[0])
        words_type = data_parts[1]
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # حذف جميع الكلمات
        if words_type == "blocked":
            words_count = len(group.blocked_words.words)
            group.blocked_words.words = []
        else:
            words_count = len(group.allowed_words.words)
            group.allowed_words.words = []
        
        # حفظ التغيير
        await group.save()
        
        logger.info(
            f"User {callback.from_user.id} removed all {words_type} words "
            f"({words_count} words) from group {chat_id}"
        )
        
        # عرض رسالة نجاح
        words_name = "المحظورة" if words_type == "blocked" else "المسموح بها"
        await callback.message.edit_text(
            f"{EMOJI_SUCCESS} **تم حذف جميع الكلمات ال{words_name}**\n\n"
            f"تم حذف {words_count} كلمة"
        )
        
        await callback.answer(f"{EMOJI_SUCCESS} تم الحذف")
        
        # العودة للإعدادات بعد 2 ثانية
        import asyncio
        await asyncio.sleep(2)
        
        is_active = group.blocked_words.active if words_type == "blocked" else group.allowed_words.active
        await callback.message.edit_text(
            f"{'🚫' if words_type == 'blocked' else '✅'} **الكلمات ال{words_name}**\n\n"
            f"اختر الإجراء المطلوب:",
            reply_markup=build_words_settings_keyboard(chat_id, words_type, is_active)
        )
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in remove_all_words: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("cancel:remove_all_words"))
async def cancel_remove_all_words(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "إلغاء" في تأكيد حذف جميع الكلمات
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
    
    الإرجاع:
        None
    
    السلوك:
        إلغاء عملية الحذف والعودة للإعدادات
    """
    try:
        await callback.answer("❌ تم الإلغاء")
        
        # يمكن إضافة كود للعودة للإعدادات هنا
        
    except Exception as e:
        logger.error(f"Error in cancel_remove_all_words: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data == "cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "إلغاء" العام
        يلغي أي عملية جارية ويمسح FSM state
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        1. مسح FSM state
        2. عرض رسالة إلغاء
    """
    try:
        # مسح FSM state
        await state.clear()
        
        await callback.message.edit_text("❌ تم إلغاء العملية")
        await callback.answer("❌ تم الإلغاء")
        
    except Exception as e:
        logger.error(f"Error in cancel_operation: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


def register_callbacks(dp):
    """
    الوصف:
        تسجيل معالجات أزرار الكلمات في الـ Dispatcher
        يتم استدعاء هذه الدالة من bot/keyboards/callbacks/__init__.py
    
    المعاملات:
        dp (Dispatcher): الـ Dispatcher الخاص بـ aiogram
    
    الإرجاع:
        None
    
    الملفات المرتبطة:
        - bot/keyboards/callbacks/__init__.py: يستدعي هذه الدالة
    """
    dp.include_router(router)
