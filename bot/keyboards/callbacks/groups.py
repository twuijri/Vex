"""
معالجات أزرار إدارة المجموعات

هذا الملف مسؤول عن معالجة الأزرار الخاصة بإعدادات المجموعات
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.database.models import Group
from bot.keyboards.builders import (
    build_group_settings_keyboard,
    build_confirmation_keyboard
)
from bot.utils.constants import EMOJI_SUCCESS, EMOJI_ERROR

logger = logging.getLogger(__name__)

# إنشاء Router للمعالجات
router = Router(name="groups_callbacks")


@router.callback_query(F.data.startswith("group:"))
async def show_group_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج الضغط على مجموعة معينة من قائمة المجموعات
        يعرض قائمة إعدادات المجموعة المختارة
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "group:{chat_id}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id من callback.data
        2. جلب بيانات المجموعة من قاعدة البيانات
        3. عرض قائمة إعدادات المجموعة
        4. القائمة تحتوي على:
           - إعدادات الوسائط
           - الكلمات المحظورة/المسموح بها
           - قفل المجموعة
           - الترحيب
           - القوانين
           - التحذيرات
           - منع التكرار
           - التحقق (Captcha)
           - اللغات
           - حذف إدارة المجموعة
    
    الملفات المرتبطة:
        - bot/database/models.py: Group model
        - bot/keyboards/builders.py: build_group_settings_keyboard
        - bot/keyboards/callbacks/media.py: معالجات فلاتر الوسائط
        - bot/keyboards/callbacks/words.py: معالجات الكلمات
        - bot/keyboards/callbacks/silent.py: معالجات القفل
        - bot/keyboards/callbacks/welcome.py: معالجات الترحيب
        - bot/keyboards/callbacks/rules.py: معالجات القوانين
    
    مثال:
        المشرف يضغط على: "مجموعة الأصدقاء"
        البوت يعرض: قائمة إعدادات المجموعة
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 1)[1])
        
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        if not group.active:
            await callback.answer("⚠️ المجموعة غير مفعلة", show_alert=True)
            return
        
        # عرض إعدادات المجموعة
        await callback.message.edit_text(
            f"⚙️ **إعدادات المجموعة**\n\n"
            f"📌 الاسم: {group.chat_title}\n"
            f"🆔 المعرف: `{group.chat_id}`\n"
            f"📅 تاريخ التفعيل: {group.created_at.strftime('%Y-%m-%d')}\n\n"
            f"اختر الإعداد الذي تريد تعديله:",
            reply_markup=build_group_settings_keyboard(chat_id)
        )
        
        await callback.answer(f"⚙️ {group.chat_title}")
        
        logger.info(f"User {callback.from_user.id} opened settings for group {chat_id}")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_group_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("group_settings:deactivate:"))
async def confirm_deactivate_group(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "حذف إدارة المجموعة"
        يطلب تأكيد من المستخدم قبل إلغاء تفعيل المجموعة
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "group_settings:deactivate:{chat_id}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id من callback.data
        2. عرض رسالة تأكيد مع أزرار (نعم/إلغاء)
        3. تحذير المستخدم من أن هذا الإجراء سيحذف جميع الإعدادات
    
    الملفات المرتبطة:
        - bot/keyboards/builders.py: build_confirmation_keyboard
        - deactivate_group: الدالة التي تنفذ الحذف الفعلي
    
    مثال:
        المشرف يضغط على: "⛔️ حذف إدارة المجموعة"
        البوت يعرض: "⚠️ هل أنت متأكد؟" + أزرار التأكيد
    """
    try:
        # استخراج chat_id
        chat_id = callback.data.split(":", 2)[2]
        
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == int(chat_id))
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # عرض رسالة التأكيد
        await callback.message.edit_text(
            f"⚠️ **تأكيد حذف إدارة المجموعة**\n\n"
            f"📌 المجموعة: {group.chat_title}\n"
            f"🆔 المعرف: `{group.chat_id}`\n\n"
            f"❗️ **تحذير:**\n"
            f"• سيتم إلغاء تفعيل المجموعة\n"
            f"• سيتم حذف جميع الإعدادات\n"
            f"• سيتوقف البوت عن العمل في المجموعة\n\n"
            f"هل أنت متأكد من المتابعة؟",
            reply_markup=build_confirmation_keyboard("deactivate_group", chat_id)
        )
        
        await callback.answer("⚠️ تأكيد الحذف")
        
    except Exception as e:
        logger.error(f"Error in confirm_deactivate_group: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("confirm:deactivate_group:"))
async def deactivate_group(callback: CallbackQuery):
    """
    الوصف:
        معالج تأكيد حذف إدارة المجموعة
        ينفذ عملية إلغاء التفعيل الفعلية
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "confirm:deactivate_group:{chat_id}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id من callback.data
        2. تحديث حالة المجموعة إلى غير مفعلة (active = False)
        3. الاحتفاظ بالبيانات في قاعدة البيانات (لا يتم حذفها)
        4. عرض رسالة نجاح
        5. العودة لقائمة المجموعات
    
    الملفات المرتبطة:
        - bot/database/models.py: Group model
        - bot/keyboards/callbacks/main.py: show_groups_list
    
    ملاحظة:
        البيانات لا يتم حذفها، فقط يتم تعطيل المجموعة
        يمكن إعادة تفعيلها لاحقاً بإرسال /start في المجموعة
    
    مثال:
        المشرف يضغط على: "✅ نعم، تأكيد"
        البوت ينفذ: إلغاء تفعيل المجموعة
        البوت يعرض: "✅ تم إلغاء تفعيل المجموعة بنجاح"
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # حفظ اسم المجموعة قبل التعطيل
        group_name = group.chat_title
        
        # تعطيل المجموعة (لا نحذف البيانات)
        group.active = False
        await group.save()
        
        logger.info(f"User {callback.from_user.id} deactivated group {chat_id}")
        
        # عرض رسالة نجاح
        await callback.message.edit_text(
            f"{EMOJI_SUCCESS} **تم إلغاء تفعيل المجموعة بنجاح**\n\n"
            f"📌 المجموعة: {group_name}\n"
            f"🆔 المعرف: `{chat_id}`\n\n"
            f"ℹ️ البيانات محفوظة ويمكن إعادة التفعيل لاحقاً\n"
            f"بإرسال الأمر /start في المجموعة"
        )
        
        await callback.answer(f"{EMOJI_SUCCESS} تم إلغاء التفعيل")
        
        # العودة لقائمة المجموعات بعد 3 ثواني
        import asyncio
        await asyncio.sleep(3)
        
        # استدعاء دالة عرض قائمة المجموعات
        from .main import show_groups_list
        await show_groups_list(callback)
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in deactivate_group: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ أثناء إلغاء التفعيل", show_alert=True)


@router.callback_query(F.data.startswith("cancel:deactivate_group"))
async def cancel_deactivate_group(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "إلغاء" في تأكيد حذف المجموعة
        يلغي عملية الحذف ويعود للإعدادات
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
    
    الإرجاع:
        None
    
    السلوك:
        1. إلغاء عملية الحذف
        2. العودة لقائمة المجموعات
    
    مثال:
        المشرف يضغط على: "❌ إلغاء"
        البوت يعرض: قائمة المجموعات
    """
    try:
        await callback.answer("❌ تم الإلغاء")
        
        # العودة لقائمة المجموعات
        from .main import show_groups_list
        await show_groups_list(callback)
        
    except Exception as e:
        logger.error(f"Error in cancel_deactivate_group: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("back:group:"))
async def back_to_group_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "الرجوع" من إعدادات فرعية إلى إعدادات المجموعة الرئيسية
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "back:group:{chat_id}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id من callback.data
        2. عرض قائمة إعدادات المجموعة الرئيسية
    
    الملفات المرتبطة:
        - show_group_settings: الدالة التي تعرض إعدادات المجموعة
    
    مثال:
        المستخدم يضغط على: "🔙 الرجوع"
        البوت يعرض: قائمة إعدادات المجموعة الرئيسية
    """
    try:
        # استخراج chat_id
        chat_id = callback.data.split(":", 2)[2]
        
        # إنشاء callback جديد بصيغة "group:{chat_id}"
        new_callback_data = f"group:{chat_id}"
        
        # تحديث callback.data
        callback.data = new_callback_data
        
        # استدعاء دالة عرض إعدادات المجموعة
        await show_group_settings(callback)
        
    except Exception as e:
        logger.error(f"Error in back_to_group_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


def register_callbacks(dp):
    """
    الوصف:
        تسجيل معالجات أزرار إدارة المجموعات في الـ Dispatcher
        يتم استدعاء هذه الدالة من bot/keyboards/callbacks/__init__.py
    
    المعاملات:
        dp (Dispatcher): الـ Dispatcher الخاص بـ aiogram
    
    الإرجاع:
        None
    
    الملفات المرتبطة:
        - bot/keyboards/callbacks/__init__.py: يستدعي هذه الدالة
    """
    dp.include_router(router)
