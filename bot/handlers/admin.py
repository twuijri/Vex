"""
معالج أمر /admin

هذا الملف مسؤول عن معالجة أمر /admin الذي يعرض لوحة التحكم الرئيسية
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

from bot.utils.helpers import is_user_admin
from bot.utils.constants import MSG_NOT_ADMIN
from bot.keyboards.builders import build_main_settings_keyboard

logger = logging.getLogger(__name__)

# إنشاء Router للمعالجات
router = Router(name="admin")


@router.message(Command("admin"), F.chat.type == ChatType.PRIVATE)
async def admin_command(message: Message):
    """
    الوصف:
        معالج أمر /admin في الخاص
        يعرض لوحة التحكم الرئيسية للمشرفين فقط
        يحتوي على أزرار للوصول إلى جميع إعدادات البوت
    
    المعاملات:
        message (Message): رسالة المستخدم التي تحتوي على /admin
    
    الإرجاع:
        None
    
    السلوك:
        1. التحقق من أن المستخدم مشرف في البوت
        2. إذا كان مشرف: عرض لوحة التحكم الرئيسية
        3. إذا لم يكن مشرف: إرسال رسالة رفض الصلاحية
    
    الملفات المرتبطة:
        - bot/utils/helpers.py: is_user_admin
        - bot/keyboards/builders.py: build_main_settings_keyboard
        - bot/keyboards/callbacks/main.py: معالجات أزرار القائمة الرئيسية
    
    لوحة التحكم تحتوي على:
        - ⚙️ إعدادات المجموعات: إدارة المجموعات المفعلة
        - 👨‍💼 إعدادات البوت: إدارة المشرفين والمحظورين
    
    أمثلة الاستخدام:
        المشرف يرسل: /admin
        البوت يرد: "⚙️ لوحة التحكم الرئيسية" + أزرار الإعدادات
        
        مستخدم عادي يرسل: /admin
        البوت يرد: "⚠️ هذا الأمر للمشرفين فقط"
    """
    try:
        # التحقق من صلاحيات المستخدم
        is_admin = await is_user_admin(message.from_user.id)
        
        if not is_admin:
            await message.answer(MSG_NOT_ADMIN)
            logger.warning(f"User {message.from_user.id} tried to access admin panel")
            return
        
        # عرض لوحة التحكم الرئيسية
        await message.answer(
            "⚙️ **لوحة التحكم الرئيسية**\n\n"
            "اختر القسم الذي تريد إدارته:",
            reply_markup=build_main_settings_keyboard()
        )
        
        logger.info(f"Admin {message.from_user.id} opened admin panel")
        
    except Exception as e:
        logger.error(f"Error in admin_command: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ، يرجى المحاولة لاحقاً")


@router.message(Command("admin"), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def admin_command_group(message: Message):
    """
    الوصف:
        معالج أمر /admin في المجموعات
        يوجه المستخدم لاستخدام الأمر في الخاص
        لأن لوحة التحكم يجب أن تكون في الخاص فقط
    
    المعاملات:
        message (Message): رسالة المستخدم التي تحتوي على /admin
    
    الإرجاع:
        None
    
    السلوك:
        1. حذف رسالة الأمر من المجموعة (لتجنب الفوضى)
        2. إرسال رسالة توجيهية للمستخدم
    
    أمثلة الاستخدام:
        المستخدم يرسل في المجموعة: /admin
        البوت يرد: "⚠️ يرجى استخدام هذا الأمر في الخاص"
    """
    try:
        # حذف رسالة الأمر من المجموعة
        await message.delete()
        
        # إرسال رسالة توجيهية
        bot_info = await message.bot.get_me()
        sent_message = await message.answer(
            f"⚠️ يرجى استخدام الأمر /admin في الخاص مع البوت\n\n"
            f"👉 @{bot_info.username}"
        )
        
        # حذف الرسالة التوجيهية بعد 10 ثواني
        import asyncio
        await asyncio.sleep(10)
        await sent_message.delete()
        
    except Exception as e:
        logger.error(f"Error in admin_command_group: {e}", exc_info=True)


def register_handlers(dp):
    """
    الوصف:
        تسجيل معالجات أمر /admin في الـ Dispatcher
        يتم استدعاء هذه الدالة من bot/handlers/__init__.py
    
    المعاملات:
        dp (Dispatcher): الـ Dispatcher الخاص بـ aiogram
    
    الإرجاع:
        None
    
    الملفات المرتبطة:
        - bot/handlers/__init__.py: يستدعي هذه الدالة
    """
    dp.include_router(router)
