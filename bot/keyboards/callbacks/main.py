"""
معالجات أزرار القائمة الرئيسية

هذا الملف مسؤول عن معالجة الأزرار في القائمة الرئيسية للإعدادات
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.database.models import Group, BlockedUser
from bot.keyboards.builders import (
    build_main_settings_keyboard,
    build_bot_settings_keyboard,
    build_groups_list_keyboard
)
from bot.utils.constants import MSG_SETTINGS_CLOSED

logger = logging.getLogger(__name__)

# إنشاء Router للمعالجات
router = Router(name="main_callbacks")


@router.callback_query(F.data == "settings:groups_list")
async def show_groups_list(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "إعدادات المجموعات"
        يعرض قائمة بجميع المجموعات المفعلة في البوت
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
    
    الإرجاع:
        None
    
    السلوك:
        1. جلب جميع المجموعات المفعلة من قاعدة البيانات
        2. إذا لا توجد مجموعات: عرض رسالة + زر لإضافة مجموعة
        3. إذا توجد مجموعات: عرض قائمة بأسماء المجموعات
        4. كل مجموعة لها زر للدخول إلى إعداداتها
    
    الملفات المرتبطة:
        - bot/database/models.py: Group model
        - bot/keyboards/builders.py: build_groups_list_keyboard
        - bot/keyboards/callbacks/groups.py: معالج الضغط على مجموعة معينة
    
    مثال:
        المشرف يضغط على: "⚙️ إعدادات المجموعات"
        البوت يعرض: قائمة المجموعات أو رسالة "لا توجد مجموعات"
    """
    try:
        # جلب جميع المجموعات المفعلة
        groups = await Group.find(Group.active == True).to_list()
        
        # الحصول على معلومات البوت للرابط
        bot_info = await callback.bot.get_me()
        
        if not groups:
            # لا توجد مجموعات مفعلة
            await callback.message.edit_text(
                "❌ **لا توجد مجموعات مفعلة**\n\n"
                "لإضافة مجموعة جديدة:\n"
                "1. أضف البوت إلى المجموعة\n"
                "2. اجعله مشرف\n"
                "3. أرسل الأمر /start في المجموعة",
                reply_markup=build_groups_list_keyboard([], bot_info.username)
            )
        else:
            # تحويل المجموعات إلى قائمة قواميس
            groups_list = [
                {
                    'chat_id': group.chat_id,
                    'chat_title': group.chat_title
                }
                for group in groups
            ]
            
            await callback.message.edit_text(
                f"👥 **قائمة المجموعات المفعلة** ({len(groups_list)})\n\n"
                "اختر المجموعة التي تريد إدارتها:",
                reply_markup=build_groups_list_keyboard(groups_list, bot_info.username)
            )
        
        # إرسال إشعار للمستخدم
        await callback.answer("📋 قائمة المجموعات")
        
        logger.info(f"User {callback.from_user.id} viewed groups list")
        
    except Exception as e:
        logger.error(f"Error in show_groups_list: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data == "settings:bot")
async def show_bot_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "إعدادات البوت"
        يعرض قائمة إعدادات البوت العامة
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
    
    الإرجاع:
        None
    
    السلوك:
        1. عرض قائمة إعدادات البوت
        2. تحتوي على: حذف الرسائل، المحظورين
    
    الملفات المرتبطة:
        - bot/keyboards/builders.py: build_bot_settings_keyboard
        - bot/keyboards/callbacks/support.py: معالجات الدعم والحظر
    
    مثال:
        المشرف يضغط على: "👨‍💼 إعدادات البوت"
        البوت يعرض: قائمة إعدادات البوت
    """
    try:
        await callback.message.edit_text(
            "👨‍💼 **إعدادات البوت**\n\n"
            "اختر الإعداد الذي تريد إدارته:",
            reply_markup=build_bot_settings_keyboard()
        )
        
        await callback.answer("⚙️ إعدادات البوت")
        
        logger.info(f"User {callback.from_user.id} viewed bot settings")
        
    except Exception as e:
        logger.error(f"Error in show_bot_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data == "bot_settings:blocked_users")
async def show_blocked_users(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "المحظورين"
        يعرض قائمة المستخدمين المحظورين من نظام الدعم
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
    
    الإرجاع:
        None
    
    السلوك:
        1. جلب جميع المستخدمين المحظورين من قاعدة البيانات
        2. عرض قائمة بأسمائهم وأسباب الحظر
        3. إضافة أزرار لإلغاء الحظر
    
    الملفات المرتبطة:
        - bot/database/models.py: BlockedUser model
        - bot/keyboards/callbacks/support.py: معالج إلغاء الحظر
    
    مثال:
        المشرف يضغط على: "🚫 المحظورين"
        البوت يعرض: قائمة المحظورين أو "لا يوجد محظورين"
    """
    try:
        # جلب جميع المستخدمين المحظورين
        blocked_users = await BlockedUser.find_all().to_list()
        
        if not blocked_users:
            await callback.message.edit_text(
                "✅ **لا يوجد مستخدمين محظورين**\n\n"
                "جميع المستخدمين يمكنهم مراسلة البوت حالياً",
                reply_markup=build_bot_settings_keyboard()
            )
        else:
            # بناء قائمة المحظورين
            blocked_list = []
            for user in blocked_users:
                username = f"@{user.username}" if user.username else "لا يوجد"
                reason = user.reason if user.reason else "غير محدد"
                blocked_list.append(
                    f"👤 {user.first_name}\n"
                    f"   └ المعرف: {username}\n"
                    f"   └ السبب: {reason}\n"
                )
            
            text = (
                f"🚫 **المستخدمين المحظورين** ({len(blocked_users)})\n\n"
                + "\n".join(blocked_list)
            )
            
            await callback.message.edit_text(
                text,
                reply_markup=build_bot_settings_keyboard()
            )
        
        await callback.answer("🚫 قائمة المحظورين")
        
        logger.info(f"User {callback.from_user.id} viewed blocked users")
        
    except Exception as e:
        logger.error(f"Error in show_blocked_users: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("back:"))
async def handle_back_button(callback: CallbackQuery):
    """
    الوصف:
        معالج أزرار "الرجوع"
        يعيد المستخدم إلى القائمة السابقة
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "back:destination"
            - destinations: main, groups_list, group:{chat_id}, etc.
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج الوجهة من callback.data
        2. عرض القائمة المناسبة حسب الوجهة
    
    الملفات المرتبطة:
        - bot/keyboards/builders.py: جميع دوال بناء الأزرار
    
    مثال:
        المستخدم يضغط على: "🔙 الرجوع"
        البوت يعرض: القائمة السابقة
    """
    try:
        # استخراج الوجهة
        destination = callback.data.split(":", 1)[1]
        
        if destination == "main":
            # الرجوع للقائمة الرئيسية
            await callback.message.edit_text(
                "⚙️ **لوحة التحكم الرئيسية**\n\n"
                "اختر القسم الذي تريد إدارته:",
                reply_markup=build_main_settings_keyboard()
            )
            await callback.answer("🏠 القائمة الرئيسية")
            
        elif destination == "groups_list":
            # الرجوع لقائمة المجموعات
            await show_groups_list(callback)
            
        elif destination == "bot_settings":
            # الرجوع لإعدادات البوت
            await show_bot_settings(callback)
            
        else:
            await callback.answer("❌ وجهة غير معروفة")
        
    except Exception as e:
        logger.error(f"Error in handle_back_button: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data == "exit")
async def handle_exit_button(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "الخروج من الإعدادات"
        يغلق قائمة الإعدادات ويحذف الرسالة
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
    
    الإرجاع:
        None
    
    السلوك:
        1. تعديل الرسالة لإظهار رسالة إغلاق
        2. حذف الأزرار
    
    مثال:
        المستخدم يضغط على: "❌ الخروج من الإعدادات"
        البوت يعرض: "☑️ تم إغلاق الإعدادات"
    """
    try:
        await callback.message.edit_text(MSG_SETTINGS_CLOSED)
        await callback.answer("👋 تم الإغلاق")
        
        logger.info(f"User {callback.from_user.id} closed settings")
        
    except Exception as e:
        logger.error(f"Error in handle_exit_button: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


def register_callbacks(dp):
    """
    الوصف:
        تسجيل معالجات أزرار القائمة الرئيسية في الـ Dispatcher
        يتم استدعاء هذه الدالة من bot/keyboards/callbacks/__init__.py
    
    المعاملات:
        dp (Dispatcher): الـ Dispatcher الخاص بـ aiogram
    
    الإرجاع:
        None
    
    الملفات المرتبطة:
        - bot/keyboards/callbacks/__init__.py: يستدعي هذه الدالة
    """
    dp.include_router(router)
