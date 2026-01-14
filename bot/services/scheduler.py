"""
خدمة الجدولة - إدارة المهام المجدولة

هذا الملف مسؤول عن:
1. القفل/الفتح التلقائي اليومي
2. إدارة قفل المؤقت
3. إرسال إشعارات القفل/الفتح
"""
import logging
from datetime import datetime, time, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from bot.database.models import Group

logger = logging.getLogger(__name__)

# الـ Scheduler العام
scheduler = AsyncIOScheduler()


async def lock_group(chat_id: int, bot):
    """
    الوصف:
        قفل المجموعة تلقائياً
    
    المعاملات:
        chat_id (int): معرف المجموعة
        bot: كائن البوت
    
    السلوك:
        1. تفعيل القفل اليدوي
        2. إرسال رسالة القفل
        3. تطبيق الصلاحيات المحفوظة
    """
    try:
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group or not group.active:
            logger.warning(f"Group {chat_id} not found or inactive")
            return
        
        # تفعيل القفل
        group.silent.manual_lock = True
        await group.save()
        
        # إرسال رسالة القفل
        lock_message = group.silent.lock_message or "🔕 تم قفل المجموعة"
        
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=lock_message
            )
        except Exception as e:
            logger.error(f"Failed to send lock message to {chat_id}: {e}")
        
        logger.info(f"Group {chat_id} locked automatically")
        
    except Exception as e:
        logger.error(f"Error in lock_group for {chat_id}: {e}", exc_info=True)


async def unlock_group(chat_id: int, bot):
    """
    الوصف:
        فتح المجموعة تلقائياً
    
    المعاملات:
        chat_id (int): معرف المجموعة
        bot: كائن البوت
    
    السلوك:
        1. إلغاء القفل اليدوي
        2. إرسال رسالة الفتح
    """
    try:
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group or not group.active:
            logger.warning(f"Group {chat_id} not found or inactive")
            return
        
        # إلغاء القفل
        group.silent.manual_lock = False
        await group.save()
        
        # إرسال رسالة الفتح
        unlock_message = group.silent.unlock_message or "🔔 تم فتح المجموعة"
        
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=unlock_message
            )
        except Exception as e:
            logger.error(f"Failed to send unlock message to {chat_id}: {e}")
        
        logger.info(f"Group {chat_id} unlocked automatically")
        
    except Exception as e:
        logger.error(f"Error in unlock_group for {chat_id}: {e}", exc_info=True)


async def schedule_daily_lock(chat_id: int, open_time: time, close_time: time, bot):
    """
    الوصف:
        جدولة القفل/الفتح اليومي
    
    المعاملات:
        chat_id (int): معرف المجموعة
        open_time (time): وقت الفتح
        close_time (time): وقت الإغلاق
        bot: كائن البوت
    
    السلوك:
        إنشاء مهام مجدولة يومية للقفل والفتح
    """
    try:
        # حذف المهام القديمة إن وجدت
        job_id_lock = f"lock_{chat_id}"
        job_id_unlock = f"unlock_{chat_id}"
        
        if scheduler.get_job(job_id_lock):
            scheduler.remove_job(job_id_lock)
        
        if scheduler.get_job(job_id_unlock):
            scheduler.remove_job(job_id_unlock)
        
        # جدولة القفل
        scheduler.add_job(
            lock_group,
            trigger=CronTrigger(
                hour=close_time.hour,
                minute=close_time.minute
            ),
            args=[chat_id, bot],
            id=job_id_lock,
            replace_existing=True
        )
        
        # جدولة الفتح
        scheduler.add_job(
            unlock_group,
            trigger=CronTrigger(
                hour=open_time.hour,
                minute=open_time.minute
            ),
            args=[chat_id, bot],
            id=job_id_unlock,
            replace_existing=True
        )
        
        logger.info(
            f"Scheduled daily lock/unlock for group {chat_id}: "
            f"Lock at {close_time}, Unlock at {open_time}"
        )
        
    except Exception as e:
        logger.error(f"Error in schedule_daily_lock for {chat_id}: {e}", exc_info=True)


async def cancel_daily_lock(chat_id: int):
    """
    الوصف:
        إلغاء جدولة القفل/الفتح اليومي
    
    المعاملات:
        chat_id (int): معرف المجموعة
    
    السلوك:
        حذف المهام المجدولة
    """
    try:
        job_id_lock = f"lock_{chat_id}"
        job_id_unlock = f"unlock_{chat_id}"
        
        if scheduler.get_job(job_id_lock):
            scheduler.remove_job(job_id_lock)
        
        if scheduler.get_job(job_id_unlock):
            scheduler.remove_job(job_id_unlock)
        
        logger.info(f"Cancelled daily lock/unlock for group {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in cancel_daily_lock for {chat_id}: {e}", exc_info=True)


async def schedule_timer_lock(chat_id: int, duration_minutes: int, bot):
    """
    الوصف:
        جدولة قفل مؤقت
    
    المعاملات:
        chat_id (int): معرف المجموعة
        duration_minutes (int): مدة القفل بالدقائق
        bot: كائن البوت
    
    السلوك:
        1. قفل المجموعة فوراً
        2. جدولة الفتح التلقائي بعد المدة المحددة
    """
    try:
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group or not group.active:
            logger.warning(f"Group {chat_id} not found or inactive")
            return
        
        # حساب وقت الفتح
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        # تفعيل قفل المؤقت
        group.silent.timer_lock.active = True
        group.silent.timer_lock.end_time = end_time
        await group.save()
        
        # قفل المجموعة فوراً
        await lock_group(chat_id, bot)
        
        # جدولة الفتح التلقائي
        job_id = f"timer_unlock_{chat_id}"
        
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        scheduler.add_job(
            unlock_timer_lock,
            trigger=DateTrigger(run_date=end_time),
            args=[chat_id, bot],
            id=job_id,
            replace_existing=True
        )
        
        logger.info(
            f"Scheduled timer lock for group {chat_id}: "
            f"Duration {duration_minutes} minutes, End at {end_time}"
        )
        
    except Exception as e:
        logger.error(f"Error in schedule_timer_lock for {chat_id}: {e}", exc_info=True)


async def unlock_timer_lock(chat_id: int, bot):
    """
    الوصص:
        فتح قفل المؤقت تلقائياً
    
    المعاملات:
        chat_id (int): معرف المجموعة
        bot: كائن البوت
    
    السلوك:
        1. إلغاء قفل المؤقت
        2. فتح المجموعة
    """
    try:
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group or not group.active:
            logger.warning(f"Group {chat_id} not found or inactive")
            return
        
        # إلغاء قفل المؤقت
        group.silent.timer_lock.active = False
        group.silent.timer_lock.end_time = None
        await group.save()
        
        # فتح المجموعة
        await unlock_group(chat_id, bot)
        
        logger.info(f"Timer lock ended for group {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in unlock_timer_lock for {chat_id}: {e}", exc_info=True)


async def cancel_timer_lock(chat_id: int):
    """
    الوصف:
        إلغاء قفل المؤقت يدوياً
    
    المعاملات:
        chat_id (int): معرف المجموعة
    
    السلوك:
        1. حذف المهمة المجدولة
        2. تحديث قاعدة البيانات
    """
    try:
        # حذف المهمة المجدولة
        job_id = f"timer_unlock_{chat_id}"
        
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        # تحديث قاعدة البيانات
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if group:
            group.silent.timer_lock.active = False
            group.silent.timer_lock.end_time = None
            await group.save()
        
        logger.info(f"Cancelled timer lock for group {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in cancel_timer_lock for {chat_id}: {e}", exc_info=True)


async def load_scheduled_tasks(bot):
    """
    الوصف:
        تحميل المهام المجدولة من قاعدة البيانات عند بدء البوت
    
    المعاملات:
        bot: كائن البوت
    
    السلوك:
        1. جلب جميع المجموعات النشطة
        2. إعادة جدولة القفل اليومي
        3. إعادة جدولة قفل المؤقت النشط
    """
    try:
        # جلب جميع المجموعات النشطة
        groups = await Group.find(Group.active == True).to_list()
        
        for group in groups:
            # إعادة جدولة القفل اليومي
            if group.silent.daily_schedule.active:
                open_time = group.silent.daily_schedule.open_time
                close_time = group.silent.daily_schedule.close_time
                
                if open_time and close_time:
                    await schedule_daily_lock(group.chat_id, open_time, close_time, bot)
            
            # إعادة جدولة قفل المؤقت النشط
            if group.silent.timer_lock.active and group.silent.timer_lock.end_time:
                end_time = group.silent.timer_lock.end_time
                
                # التحقق من أن الوقت لم ينتهي بعد
                if end_time > datetime.now():
                    job_id = f"timer_unlock_{group.chat_id}"
                    
                    scheduler.add_job(
                        unlock_timer_lock,
                        trigger=DateTrigger(run_date=end_time),
                        args=[group.chat_id, bot],
                        id=job_id,
                        replace_existing=True
                    )
                    
                    logger.info(f"Restored timer lock for group {group.chat_id}")
                else:
                    # الوقت انتهى، إلغاء القفل
                    await unlock_timer_lock(group.chat_id, bot)
        
        logger.info(f"Loaded scheduled tasks for {len(groups)} groups")
        
    except Exception as e:
        logger.error(f"Error in load_scheduled_tasks: {e}", exc_info=True)


def start_scheduler():
    """
    الوصف:
        بدء الـ Scheduler
    
    السلوك:
        تشغيل الـ Scheduler إذا لم يكن يعمل
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler():
    """
    الوصف:
        إيقاف الـ Scheduler
    
    السلوك:
        إيقاف الـ Scheduler بشكل آمن
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
