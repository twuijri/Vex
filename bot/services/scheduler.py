import asyncio
import logging
from datetime import datetime
import pytz
from bot.services.db import db
from bot.utils.permissions import set_group_silent_mode
from aiogram import Bot

logger = logging.getLogger(__name__)

# Riyadh Timezone for consistency
TZ = pytz.timezone('Asia/Riyadh')

async def scheduler_task(bot: Bot):
    """
    Background Task that runs every 60 seconds.
    Checks for: 1. Timer Expiry 2. Schedule Open/Close
    """
    logger.info("⏳ Scheduler started...")
    while True:
        try:
            now = datetime.now(TZ)
            current_time_str = now.strftime("%H:%M")
            
            # 1. Get ALL active groups
            active_groups = await db.get_active_groups()
            
            for group in active_groups:
                chat_id = group["chat_id"]
                silent_s = group.get("silent", {})
                
                # Messages Config
                messages = silent_s.get("messages", {})
                msg_open = messages.get("daily_open", "🔓 <b>تم فتح المجموعة حسب الجدول اليومي.</b>")
                msg_close = messages.get("daily_close", "🔒 <b>تم قفل المجموعة حسب الجدول اليومي.</b>")
                msg_timer = messages.get("timer_lock", "⏱️ <b>انتهى وقت المؤقت.</b>")
                
                # --- A. TIMER LOGIC ---
                timer = silent_s.get("timer", {})
                if timer.get("active"):
                    end_time = timer.get("end_time")
                    if end_time and datetime.now().timestamp() >= end_time:
                        # Timer Expired -> Unlock
                        await set_group_silent_mode(bot, chat_id, lock=False)
                        
                        await db.update_group_settings(chat_id, {
                            "silent.is_locked": False,
                            "silent.timer.active": False,
                            "silent.timer.end_time": None
                        })
                        await bot.send_message(chat_id, "🔓 <b>انتهى القفل المؤقت.</b>")

                # --- B. SCHEDULE LOGIC ---
                # --- B. SCHEDULE LOGIC (Strict State Enforcement) ---
                schedule = silent_s.get("schedule", {})
                if schedule.get("active"):
                    open_str = schedule.get("open_time", "08:00")
                    close_str = schedule.get("close_time", "23:00")
                    
                    # Parse Hours/Minutes
                    def parse_time(t_str):
                        h, m = map(int, t_str.split(":"))
                        return h * 60 + m
                    
                    current_mins = now.hour * 60 + now.minute
                    open_mins = parse_time(open_str)
                    close_mins = parse_time(close_str)
                    
                    # specific minute checks for NOTIFICATION
                    is_transition_minute = (current_time_str == open_str) or (current_time_str == close_str)
                    
                    # Logic: When should it be LOCKED (Silent)?
                    # It is locked between CloseTime (Start of Silence) and OpenTime (End of Silence).
                    
                    should_be_locked = False
                    
                    if close_mins < open_mins:
                         # e.g. Close 01:00, Open 08:00 (Night Lock)
                         # Locked if now >= 01:00 AND now < 08:00
                         if close_mins <= current_mins < open_mins:
                             should_be_locked = True
                    else:
                         # e.g. Close 23:00, Open 08:00 (Overnight Lock)
                         # Locked if now >= 23:00 OR now < 08:00
                         if current_mins >= close_mins or current_mins < open_mins:
                             should_be_locked = True
                    
                    current_locked = silent_s.get("is_locked", False)
                    timer_active = timer.get("active", False)
                    
                    # DEBUG LOGGING (Expanded)
                    log_emoji = "🔒" if should_be_locked else "🔓"
                    logger.info(f"🔍 Sched Check [{chat_id}]: {now.strftime('%H:%M:%S')} | "
                                f"Win={open_str}-{close_str} | Target={log_emoji} (Lock={should_be_locked}) | "
                                f"State={current_locked} | Timer={timer_active}")
                    
                    if should_be_locked and not current_locked:
                        # ENFORCE LOCK
                        await set_group_silent_mode(bot, chat_id, lock=True)
                        await db.update_group_settings(chat_id, {"silent.is_locked": True})
                        
                        # Notify on State Change (Always)
                        try:
                             await bot.send_message(chat_id, msg_close)
                        except:
                             pass
                             
                    elif not should_be_locked and current_locked:
                        # ENFORCE OPEN
                        # Check Timer: If Timer is Active, DO NOT UNLOCK via Schedule.
                        if not timer_active:
                            # DOUBLE CHECK: Are we ABSOLUTELY sure we should unlock?
                            # If should_be_locked is False, then we are in Open Window.
                            await set_group_silent_mode(bot, chat_id, lock=False)
                            await db.update_group_settings(chat_id, {"silent.is_locked": False})
                            
                            try:
                                 await bot.send_message(chat_id, msg_open)
                            except:
                                 pass
                        else:
                            logger.info(f"⏳ Timer active for {chat_id}, skipping schedule unlock.")

        except Exception as e:
            logger.error(f"❌ Scheduler Error: {e}")
        
        # Wait until next minute starts (Sync)
        # Sleep seconds = 60 - current_seconds
        now = datetime.now(TZ)
        sleep_seconds = 60 - now.second + 1 # Add 1s buffer to ensure we land in the next minute
        if sleep_seconds > 60: sleep_seconds = 1 
        # If now.second=59, sleep=2. Wakes at 01.
        
        logger.debug(f"💤 Sleeping for {sleep_seconds}s...")
        await asyncio.sleep(sleep_seconds)
