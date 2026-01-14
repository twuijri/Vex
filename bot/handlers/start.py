"""
معالج أمر /start

هذا الملف مسؤول عن معالجة أمر /start في الخاص والمجموعات
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.enums import ChatType

from bot.database.models import User, Group
from bot.utils.helpers import get_or_create_user, is_user_admin
from bot.utils.constants import MSG_WELCOME_USER, MSG_WELCOME_ADMIN
from bot.keyboards.builders import build_main_settings_keyboard

logger = logging.getLogger(__name__)

# إنشاء Router للمعالجات
router = Router(name="start")


@router.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def start_command_private(message: Message):
    """
    الوصف:
        معالج أمر /start في الخاص
        يقوم بحفظ بيانات المستخدم وإرسال رسالة ترحيب
        إذا كان المستخدم مشرف، يعرض له لوحة التحكم
    
    المعاملات:
        message (Message): رسالة المستخدم التي تحتوي على /start
    
    الإرجاع:
        None
    
    السلوك:
        1. حفظ/تحديث بيانات المستخدم في قاعدة البيانات
        2. التحقق إذا كان المستخدم مشرف
        3. إرسال رسالة ترحيب مناسبة
        4. إذا كان مشرف، إضافة زر لوحة التحكم
    
    الملفات المرتبطة:
        - bot/database/models.py: User model
        - bot/utils/helpers.py: get_or_create_user, is_user_admin
        - bot/keyboards/builders.py: build_main_settings_keyboard
    
    أمثلة الاستخدام:
        المستخدم يرسل: /start
        البوت يرد: "مرحباً بك في البوت! 👋"
        
        المشرف يرسل: /start
        البوت يرد: "مرحباً بك في لوحة التحكم! 👨‍💼" + أزرار الإعدادات
    """
    try:
        # حفظ بيانات المستخدم
        user = await get_or_create_user(message.from_user)
        logger.info(f"User {user.user_id} started the bot")
        
        # التحقق من صلاحيات المستخدم
        is_admin = await is_user_admin(message.from_user.id)
        
        if is_admin:
            # رسالة ترحيب للمشرف مع لوحة التحكم
            await message.answer(
                MSG_WELCOME_ADMIN,
                reply_markup=build_main_settings_keyboard()
            )
        else:
            # رسالة ترحيب عادية للمستخدم
            await message.answer(MSG_WELCOME_USER)
            
    except Exception as e:
        logger.error(f"Error in start_command_private: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ، يرجى المحاولة لاحقاً")


@router.message(CommandStart(), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def start_command_group(message: Message):
    """
    الوصف:
        معالج أمر /start في المجموعات
        يستخدم لتفعيل البوت في المجموعة
        يجب أن يكون المستخدم مشرف في البوت لتفعيل المجموعة
    
    المعاملات:
        message (Message): رسالة المستخدم التي تحتوي على /start
    
    الإرجاع:
        None
    
    السلوك:
        1. التحقق من أن المستخدم مشرف في البوت
        2. التحقق من أن المجموعة غير مفعلة مسبقاً
        3. حفظ بيانات المجموعة في قاعدة البيانات
        4. إرسال رسالة تأكيد التفعيل
    
    الملفات المرتبطة:
        - bot/database/models.py: Group model
        - bot/utils/helpers.py: is_user_admin
        - bot/utils/constants.py: MSG_GROUP_ACTIVATED, MSG_GROUP_ALREADY_ACTIVE
    
    أمثلة الاستخدام:
        المشرف يرسل في المجموعة: /start
        البوت يرد: "✅ تم تفعيل المجموعة بنجاح"
        
        مستخدم عادي يرسل: /start
        البوت يرد: "⚠️ هذا الأمر للمشرفين فقط"
    """
    try:
        # التحقق من صلاحيات المستخدم
        is_admin = await is_user_admin(message.from_user.id)
        
        if not is_admin:
            await message.reply("⚠️ هذا الأمر للمشرفين فقط")
            return
        
        # التحقق من أن المجموعة غير مفعلة مسبقاً
        existing_group = await Group.find_one(Group.chat_id == message.chat.id)
        
        if existing_group and existing_group.active:
            await message.reply("⚠️ المجموعة مفعلة مسبقاً")
            return
        
        # إنشاء أو تحديث المجموعة
        if existing_group:
            # إعادة تفعيل مجموعة معطلة
            existing_group.active = True
            existing_group.activated_by = message.from_user.id
            await existing_group.save()
        else:
            # إنشاء مجموعة جديدة
            new_group = Group(
                chat_id=message.chat.id,
                chat_title=message.chat.title,
                chat_type=message.chat.type,
                activated_by=message.from_user.id
            )
            await new_group.insert()
        
        logger.info(f"Group {message.chat.id} activated by user {message.from_user.id}")
        
        await message.reply(
            "✅ تم تفعيل المجموعة بنجاح!\n\n"
            "يمكنك الآن إدارة المجموعة من خلال الأمر /admin في الخاص"
        )
        
    except Exception as e:
        logger.error(f"Error in start_command_group: {e}", exc_info=True)
        await message.reply("❌ حدث خطأ أثناء تفعيل المجموعة")


def register_handlers(dp):
    """
    الوصف:
        تسجيل معالجات أمر /start في الـ Dispatcher
        يتم استدعاء هذه الدالة من bot/handlers/__init__.py
    
    المعاملات:
        dp (Dispatcher): الـ Dispatcher الخاص بـ aiogram
    
    الإرجاع:
        None
    
    الملفات المرتبطة:
        - bot/handlers/__init__.py: يستدعي هذه الدالة
    """
    dp.include_router(router)
