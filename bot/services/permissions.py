"""
خدمة الصلاحيات - إدارة صلاحيات المجموعة

هذا الملف مسؤول عن:
1. تطبيق الصلاحيات عند القفل
2. استعادة الصلاحيات عند الفتح
3. التحقق من صلاحيات المستخدمين
"""
import logging
from typing import Optional

from aiogram import Bot
from aiogram.types import ChatPermissions

logger = logging.getLogger(__name__)


async def apply_lock_permissions(bot: Bot, chat_id: int, permissions: dict):
    """
    الوصف:
        تطبيق صلاحيات القفل على المجموعة
    
    المعاملات:
        bot (Bot): كائن البوت
        chat_id (int): معرف المجموعة
        permissions (dict): الصلاحيات المراد تطبيقها
    
    السلوك:
        تحديث صلاحيات المجموعة باستخدام set_chat_permissions
    """
    try:
        # إنشاء كائن ChatPermissions
        chat_permissions = ChatPermissions(
            can_send_messages=permissions.get("can_send_messages", False),
            can_send_media_messages=permissions.get("can_send_media", False),
            can_send_polls=permissions.get("can_send_polls", False),
            can_send_other_messages=permissions.get("can_send_stickers", False),
            can_add_web_page_previews=permissions.get("can_add_web_page_previews", False),
            can_change_info=permissions.get("can_change_info", False),
            can_invite_users=permissions.get("can_invite_users", False),
            can_pin_messages=permissions.get("can_pin_messages", False)
        )
        
        # تطبيق الصلاحيات
        await bot.set_chat_permissions(
            chat_id=chat_id,
            permissions=chat_permissions
        )
        
        logger.info(f"Applied lock permissions to group {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in apply_lock_permissions for {chat_id}: {e}", exc_info=True)


async def restore_full_permissions(bot: Bot, chat_id: int):
    """
    الوصف:
        استعادة الصلاحيات الكاملة للمجموعة
    
    المعاملات:
        bot (Bot): كائن البوت
        chat_id (int): معرف المجموعة
    
    السلوك:
        إعادة جميع الصلاحيات للأعضاء
    """
    try:
        # إنشاء كائن ChatPermissions بصلاحيات كاملة
        chat_permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,  # عادة محظور للأعضاء العاديين
            can_invite_users=True,
            can_pin_messages=False  # عادة محظور للأعضاء العاديين
        )
        
        # تطبيق الصلاحيات
        await bot.set_chat_permissions(
            chat_id=chat_id,
            permissions=chat_permissions
        )
        
        logger.info(f"Restored full permissions to group {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in restore_full_permissions for {chat_id}: {e}", exc_info=True)


async def check_bot_permissions(bot: Bot, chat_id: int) -> bool:
    """
    الوصف:
        التحقق من صلاحيات البوت في المجموعة
    
    المعاملات:
        bot (Bot): كائن البوت
        chat_id (int): معرف المجموعة
    
    الإرجاع:
        bool: True إذا كان البوت لديه الصلاحيات المطلوبة
    
    السلوك:
        التحقق من أن البوت مشرف ولديه صلاحية تقييد الأعضاء
    """
    try:
        # جلب معلومات البوت في المجموعة
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        
        # التحقق من أن البوت مشرف
        if bot_member.status not in ["administrator", "creator"]:
            logger.warning(f"Bot is not admin in group {chat_id}")
            return False
        
        # التحقق من صلاحية تقييد الأعضاء
        if not bot_member.can_restrict_members:
            logger.warning(f"Bot doesn't have restrict_members permission in group {chat_id}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error in check_bot_permissions for {chat_id}: {e}", exc_info=True)
        return False


async def mute_user(bot: Bot, chat_id: int, user_id: int, duration_seconds: Optional[int] = None):
    """
    الوصف:
        كتم عضو في المجموعة
    
    المعاملات:
        bot (Bot): كائن البوت
        chat_id (int): معرف المجموعة
        user_id (int): معرف العضو
        duration_seconds (int, optional): مدة الكتم بالثواني (None = دائم)
    
    السلوك:
        تقييد صلاحيات العضو
    """
    try:
        from datetime import datetime, timedelta
        
        # حساب وقت انتهاء الكتم
        until_date = None
        if duration_seconds:
            until_date = datetime.now() + timedelta(seconds=duration_seconds)
        
        # كتم العضو
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        
        logger.info(f"Muted user {user_id} in group {chat_id} for {duration_seconds}s")
        
    except Exception as e:
        logger.error(f"Error in mute_user for {user_id} in {chat_id}: {e}", exc_info=True)


async def unmute_user(bot: Bot, chat_id: int, user_id: int):
    """
    الوصف:
        إلغاء كتم عضو في المجموعة
    
    المعاملات:
        bot (Bot): كائن البوت
        chat_id (int): معرف المجموعة
        user_id (int): معرف العضو
    
    السلوك:
        استعادة صلاحيات العضو
    """
    try:
        # إلغاء الكتم
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True
            )
        )
        
        logger.info(f"Unmuted user {user_id} in group {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in unmute_user for {user_id} in {chat_id}: {e}", exc_info=True)


async def ban_user(bot: Bot, chat_id: int, user_id: int, delete_messages: bool = True):
    """
    الوصف:
        حظر عضو من المجموعة
    
    المعاملات:
        bot (Bot): كائن البوت
        chat_id (int): معرف المجموعة
        user_id (int): معرف العضو
        delete_messages (bool): حذف رسائل العضو
    
    السلوك:
        طرد العضو من المجموعة
    """
    try:
        # حظر العضو
        await bot.ban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            revoke_messages=delete_messages
        )
        
        logger.info(f"Banned user {user_id} from group {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in ban_user for {user_id} in {chat_id}: {e}", exc_info=True)


async def unban_user(bot: Bot, chat_id: int, user_id: int):
    """
    الوصف:
        إلغاء حظر عضو من المجموعة
    
    المعاملات:
        bot (Bot): كائن البوت
        chat_id (int): معرف المجموعة
        user_id (int): معرف العضو
    
    السلوك:
        السماح للعضو بالانضمام مجدداً
    """
    try:
        # إلغاء الحظر
        await bot.unban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            only_if_banned=True
        )
        
        logger.info(f"Unbanned user {user_id} from group {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in unban_user for {user_id} in {chat_id}: {e}", exc_info=True)


async def kick_user(bot: Bot, chat_id: int, user_id: int):
    """
    الوصف:
        طرد عضو من المجموعة (بدون حظر)
    
    المعاملات:
        bot (Bot): كائن البوت
        chat_id (int): معرف المجموعة
        user_id (int): معرف العضو
    
    السلوك:
        طرد العضو ثم إلغاء الحظر فوراً
    """
    try:
        # طرد العضو
        await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        
        # إلغاء الحظر فوراً
        await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        
        logger.info(f"Kicked user {user_id} from group {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in kick_user for {user_id} in {chat_id}: {e}", exc_info=True)
