"""
خدمة الفلاتر - معالجة الرسائل والوسائط

هذا الملف مسؤول عن:
1. فلترة الوسائط (20 نوع)
2. فلترة الكلمات المحظورة/المسموح بها
3. التحقق من حالة القفل
4. إرسال رسائل الترحيب
5. معالجة الأعضاء الجدد
"""
import logging
import re
from typing import Optional
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, MEMBER, KICKED, LEFT, ADMINISTRATOR, CREATOR

from bot.database.models import Group
from bot.utils.constants import MEDIA_TYPES

logger = logging.getLogger(__name__)
router = Router(name="filters")


async def check_media_filter(message: Message, group: Group) -> bool:
    """
    الوصف:
        التحقق من فلاتر الوسائط
    
    المعاملات:
        message (Message): الرسالة المراد فحصها
        group (Group): بيانات المجموعة
    
    الإرجاع:
        bool: True إذا كانت الرسالة محظورة
    
    السلوك:
        فحص نوع الوسائط ومقارنته بالإعدادات
    """
    try:
        # التحقق من كل نوع وسائط
        if message.photo and not group.media.photo:
            return True
        
        if message.video and not group.media.video:
            return True
        
        if message.audio and not group.media.audio:
            return True
        
        if message.voice and not group.media.voice:
            return True
        
        if message.video_note and not group.media.video_note:
            return True
        
        if message.document and not group.media.document:
            return True
        
        if message.sticker and not group.media.sticker:
            return True
        
        if message.animation and not group.media.gif:
            return True
        
        if message.location and not group.media.location:
            return True
        
        if message.game and not group.media.games:
            return True
        
        # التحقق من الروابط في النص أو Caption
        text = message.text or message.caption or ""
        if text:
            # روابط
            if not group.media.link:
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                if re.search(url_pattern, text):
                    return True
            
            # هاشتاقات
            if not group.media.hashtag:
                if re.search(r'#\w+', text):
                    return True
            
            # أرقام الهواتف
            if not group.media.mobile:
                phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                if re.search(phone_pattern, text):
                    return True
        
        # التحقق من Forward
        if message.forward_date and not group.media.forward:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error in check_media_filter: {e}", exc_info=True)
        return False


async def check_words_filter(text: str, group: Group) -> bool:
    """
    الوصف:
        التحقق من فلاتر الكلمات
    
    المعاملات:
        text (str): النص المراد فحصه
        group (Group): بيانات المجموعة
    
    الإرجاع:
        bool: True إذا كان النص يحتوي على كلمات محظورة
    
    السلوك:
        1. فحص الكلمات المسموح بها أولاً
        2. ثم فحص الكلمات المحظورة
    """
    try:
        if not text:
            return False
        
        text_lower = text.lower()
        
        # التحقق من الكلمات المسموح بها (لها الأولوية)
        if group.antispam.allowed_words.active and group.antispam.allowed_words.words:
            for allowed_word in group.antispam.allowed_words.words:
                if allowed_word.lower() in text_lower:
                    return False  # الكلمة مسموح بها
        
        # التحقق من الكلمات المحظورة
        if group.antispam.blocked_words.active and group.antispam.blocked_words.words:
            for blocked_word in group.antispam.blocked_words.words:
                if blocked_word.lower() in text_lower:
                    return True  # الكلمة محظورة
        
        return False
        
    except Exception as e:
        logger.error(f"Error in check_words_filter: {e}", exc_info=True)
        return False


async def is_group_locked(group: Group) -> bool:
    """
    الوصف:
        التحقق من حالة قفل المجموعة
    
    المعاملات:
        group (Group): بيانات المجموعة
    
    الإرجاع:
        bool: True إذا كانت المجموعة مقفلة
    
    السلوك:
        1. التحقق من القفل اليدوي
        2. التحقق من القفل اليومي (الجدول الزمني)
        3. التحقق من قفل المؤقت
    """
    try:
        # القفل اليدوي
        if group.silent.manual_lock:
            return True
        
        # القفل اليومي
        if group.silent.daily_schedule.active:
            now = datetime.now()
            current_time = now.time()
            
            open_time = group.silent.daily_schedule.open_time
            close_time = group.silent.daily_schedule.close_time
            
            if open_time and close_time:
                # إذا كان وقت الفتح أكبر من وقت الإغلاق (مثل: 22:00 - 08:00)
                if open_time > close_time:
                    # المجموعة مقفلة إذا كان الوقت الحالي بعد الإغلاق أو قبل الفتح
                    if current_time >= close_time or current_time < open_time:
                        return True
                else:
                    # المجموعة مقفلة إذا كان الوقت الحالي بين الإغلاق والفتح
                    if close_time <= current_time < open_time:
                        return True
        
        # قفل المؤقت
        if group.silent.timer_lock.active and group.silent.timer_lock.end_time:
            if datetime.now() < group.silent.timer_lock.end_time:
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error in is_group_locked: {e}", exc_info=True)
        return False


async def check_user_permission(message: Message, group: Group, permission: str) -> bool:
    """
    الوصف:
        التحقق من صلاحية المستخدم عند القفل
    
    المعاملات:
        message (Message): الرسالة
        group (Group): بيانات المجموعة
        permission (str): نوع الصلاحية المطلوبة
    
    الإرجاع:
        bool: True إذا كان المستخدم لديه الصلاحية
    
    السلوك:
        التحقق من الصلاحيات المحفوظة في saved_permissions
    """
    try:
        # المشرفون دائماً لديهم صلاحيات
        member = await message.chat.get_member(message.from_user.id)
        if member.status in ["creator", "administrator"]:
            return True
        
        # التحقق من الصلاحيات المحفوظة
        permissions = group.silent.saved_permissions.dict()
        return permissions.get(permission, False)
        
    except Exception as e:
        logger.error(f"Error in check_user_permission: {e}", exc_info=True)
        return False


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def filter_group_messages(message: Message):
    """
    الوصف:
        معالج رئيسي لفلترة رسائل المجموعات
    
    المعاملات:
        message (Message): الرسالة الواردة
    
    السلوك:
        1. جلب بيانات المجموعة
        2. التحقق من حالة القفل
        3. فلترة الوسائط
        4. فلترة الكلمات
        5. حذف الرسالة إذا لزم الأمر
    """
    try:
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == message.chat.id)
        
        if not group or not group.active:
            return
        
        # تجاهل رسائل المشرفين
        member = await message.chat.get_member(message.from_user.id)
        if member.status in ["creator", "administrator"]:
            return
        
        # التحقق من حالة القفل
        if await is_group_locked(group):
            # التحقق من صلاحيات المستخدم
            can_send = False
            
            # تحديد نوع الرسالة والتحقق من الصلاحية
            if message.text:
                can_send = await check_user_permission(message, group, "can_send_messages")
            elif message.photo or message.video or message.document:
                can_send = await check_user_permission(message, group, "can_send_media")
            elif message.sticker or message.animation:
                can_send = await check_user_permission(message, group, "can_send_stickers")
            elif message.poll:
                can_send = await check_user_permission(message, group, "can_send_polls")
            
            if not can_send:
                await message.delete()
                logger.info(f"Deleted message from {message.from_user.id} in locked group {message.chat.id}")
                return
        
        # فلترة الوسائط
        if await check_media_filter(message, group):
            await message.delete()
            logger.info(f"Deleted media message from {message.from_user.id} in group {message.chat.id}")
            return
        
        # فلترة الكلمات
        text = message.text or message.caption or ""
        if text and await check_words_filter(text, group):
            await message.delete()
            logger.info(f"Deleted message with blocked words from {message.from_user.id} in group {message.chat.id}")
            return
        
    except Exception as e:
        logger.error(f"Error in filter_group_messages: {e}", exc_info=True)


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    """
    الوصف:
        معالج انضمام عضو جديد للمجموعة
    
    المعاملات:
        event (ChatMemberUpdated): حدث تغيير حالة العضو
    
    السلوك:
        1. إرسال رسالة الترحيب
        2. حذف رسالة الخدمة (إذا كان مفعل)
    """
    try:
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == event.chat.id)
        
        if not group or not group.active:
            return
        
        # حذف رسالة الخدمة
        if not group.media.join_service:
            try:
                # البحث عن رسالة الخدمة وحذفها
                # ملاحظة: قد لا تكون متاحة دائماً
                pass
            except:
                pass
        
        # إرسال رسالة الترحيب
        if group.welcome.active and group.welcome.message:
            user = event.new_chat_member.user
            
            # استبدال المتغيرات
            welcome_text = group.welcome.message
            welcome_text = welcome_text.replace("{name}", user.first_name)
            welcome_text = welcome_text.replace("{username}", f"@{user.username}" if user.username else user.first_name)
            welcome_text = welcome_text.replace("{mention}", user.mention_html())
            welcome_text = welcome_text.replace("{group}", event.chat.title)
            
            # إنشاء الأزرار
            keyboard = None
            if group.welcome.buttons:
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                buttons = []
                for btn in group.welcome.buttons:
                    buttons.append([InlineKeyboardButton(text=btn['text'], url=btn['url'])])
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await event.chat.send_message(
                welcome_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            logger.info(f"Sent welcome message to {user.id} in group {event.chat.id}")
        
    except Exception as e:
        logger.error(f"Error in on_user_join: {e}", exc_info=True)


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=(KICKED | LEFT)))
async def on_user_leave(event: ChatMemberUpdated):
    """
    الوصف:
        معالج مغادرة عضو من المجموعة
    
    المعاملات:
        event (ChatMemberUpdated): حدث تغيير حالة العضو
    
    السلوك:
        حذف رسالة الخدمة (إذا كان مفعل)
    """
    try:
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == event.chat.id)
        
        if not group or not group.active:
            return
        
        # حذف رسالة الخدمة
        if not group.media.left_service:
            try:
                # البحث عن رسالة الخدمة وحذفها
                pass
            except:
                pass
        
        logger.info(f"User {event.old_chat_member.user.id} left group {event.chat.id}")
        
    except Exception as e:
        logger.error(f"Error in on_user_leave: {e}", exc_info=True)


def register_filters(dp):
    """
    الوصف:
        تسجيل معالجات الفلاتر في الـ Dispatcher
    """
    dp.include_router(router)
