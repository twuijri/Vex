"""
معالجات أزرار نظام القفل (Silent Mode)

هذا الملف مسؤول عن معالجة الأزرار الخاصة بنظام قفل المجموعة
يشمل: القفل اليدوي، القفل المجدول، القفل المؤقت، إدارة الصلاحيات
"""
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.database.models import Group
from bot.keyboards.builders import (
    build_silent_settings_keyboard,
    build_permissions_keyboard,
    build_cancel_keyboard
)
from bot.core.states import SilentStates
from bot.utils.constants import EMOJI_SUCCESS, EMOJI_ERROR, PERMISSION_NAMES

logger = logging.getLogger(__name__)

# إنشاء Router للمعالجات
router = Router(name="silent_callbacks")


@router.callback_query(F.data.startswith("group_settings:silent:"))
async def show_silent_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "قفل المجموعة"
        يعرض قائمة إعدادات نظام القفل
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "group_settings:silent:{chat_id}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id من callback.data
        2. التحقق من حالة المجموعة الحالية (مقفولة/مفتوحة)
        3. عرض قائمة الإعدادات:
           - حالة القفل الحالية
           - قفل يومي (من ساعة X إلى Y)
           - قفل مؤقت (لمدة محددة)
           - ضبط الصلاحيات
           - ضبط رسائل القفل
    
    الملفات المرتبطة:
        - bot/database/models.py: Group.silent
        - bot/keyboards/builders.py: build_silent_settings_keyboard
        - bot/services/scheduler.py: جدولة القفل اليومي
        - bot/services/permissions.py: تطبيق الصلاحيات
    
    مثال:
        المشرف يضغط على: "🔕 قفل المجموعة"
        البوت يعرض: قائمة إعدادات القفل
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # التحقق من حالة القفل الحالية
        try:
            chat = await callback.bot.get_chat(chat_id)
            is_locked = not chat.permissions.can_send_messages
        except Exception as e:
            logger.error(f"Error getting chat permissions: {e}")
            is_locked = False
        
        # معلومات القفل المجدول
        daily_info = ""
        if group.silent.from_time and group.silent.to_time:
            daily_info = f"\n📆 القفل اليومي: من {group.silent.from_time} إلى {group.silent.to_time}"
        
        # عرض إعدادات القفل
        await callback.message.edit_text(
            f"🔕 **إعدادات قفل المجموعة**\n\n"
            f"📌 المجموعة: {group.chat_title}\n"
            f"🔘 الحالة: {'مقفولة 🔕' if is_locked else 'مفتوحة 🔔'}"
            f"{daily_info}\n\n"
            f"اختر الإعداد المطلوب:",
            reply_markup=build_silent_settings_keyboard(chat_id, is_locked)
        )
        
        await callback.answer("🔕 إعدادات القفل")
        
        logger.info(f"User {callback.from_user.id} opened silent settings for group {chat_id}")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_silent_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("silent:toggle:"))
async def toggle_group_lock(callback: CallbackQuery):
    """
    الوصف:
        معالج تبديل حالة قفل المجموعة (يدوي)
        يقوم بقفل أو فتح المجموعة فوراً
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "silent:toggle:{chat_id}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id من callback.data
        2. التحقق من الحالة الحالية
        3. إذا مفتوحة: قفل المجموعة (منع الإرسال)
        4. إذا مقفولة: فتح المجموعة (استعادة الصلاحيات المحفوظة)
        5. إرسال رسالة في المجموعة (اختياري)
    
    الملفات المرتبطة:
        - bot/services/permissions.py: close_group, open_group
        - bot/database/models.py: Group.silent.lock_message, unlock_message
    
    مثال:
        المشرف يضغط على: "🔘 حالة المجموعة: مفتوحة 🔔"
        البوت ينفذ: قفل المجموعة
        البوت يعرض: "🔕 تم قفل المجموعة"
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # التحقق من الحالة الحالية
        chat = await callback.bot.get_chat(chat_id)
        is_locked = not chat.permissions.can_send_messages
        
        if is_locked:
            # فتح المجموعة
            from bot.services.permissions import open_group
            await open_group(callback.bot, chat_id)
            
            # إرسال رسالة الفتح إذا كانت مفعلة
            if group.silent.unlock_message:
                try:
                    await callback.bot.send_message(chat_id, group.silent.unlock_message)
                except:
                    pass
            
            await callback.answer(f"{EMOJI_SUCCESS} تم فتح المجموعة")
            logger.info(f"User {callback.from_user.id} unlocked group {chat_id}")
            
        else:
            # قفل المجموعة
            from bot.services.permissions import close_group
            await close_group(callback.bot, chat_id)
            
            # إرسال رسالة القفل إذا كانت مفعلة
            if group.silent.lock_message:
                try:
                    await callback.bot.send_message(chat_id, group.silent.lock_message)
                except:
                    pass
            
            await callback.answer(f"{EMOJI_SUCCESS} تم قفل المجموعة")
            logger.info(f"User {callback.from_user.id} locked group {chat_id}")
        
        # تحديث الأزرار
        new_is_locked = not is_locked
        await callback.message.edit_reply_markup(
            reply_markup=build_silent_settings_keyboard(chat_id, new_is_locked)
        )
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in toggle_group_lock: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ أثناء التبديل", show_alert=True)


@router.callback_query(F.data.startswith("silent:daily:"))
async def start_daily_lock_setup(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "قفل يومي"
        يبدأ عملية إعداد القفل اليومي المجدول
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        1. طلب وقت بداية القفل (HH:MM)
        2. طلب وقت نهاية القفل (HH:MM)
        3. حفظ الأوقات في قاعدة البيانات
        4. جدولة المهام باستخدام APScheduler
    
    الملفات المرتبطة:
        - bot/core/states.py: SilentStates.waiting_for_lock_time
        - bot/services/scheduler.py: schedule_daily_lock
    
    مثال:
        المشرف يضغط على: "📆 قفل يومي"
        البوت يطلب: "أرسل وقت بداية القفل (مثال: 23:00)"
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # حفظ البيانات في state
        await state.update_data(chat_id=chat_id, setup_step="from_time")
        
        # تغيير حالة FSM
        await state.set_state(SilentStates.waiting_for_from_time)
        
        # طلب وقت البداية
        await callback.message.edit_text(
            f"📆 **إعداد القفل اليومي**\n\n"
            f"أرسل وقت **بداية** القفل بالصيغة التالية:\n"
            f"مثال: `23:00` أو `11:30 PM`\n\n"
            f"ℹ️ سيتم قفل المجموعة تلقائياً في هذا الوقت يومياً",
            reply_markup=build_cancel_keyboard()
        )
        
        await callback.answer("✍️ أرسل وقت البداية")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_daily_lock_setup: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.message(SilentStates.waiting_for_from_time)
async def process_from_time(message: Message, state: FSMContext):
    """
    الوصف:
        معالج استقبال وقت القفل من المستخدم
    
    المعاملات:
        message (Message): رسالة المستخدم
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        1. استقبال الوقت وتحويله للصيغة الصحيحة (HH:MM)
        2. التحقق من صحة الصيغة
        3. إذا كان وقت البداية: طلب وقت النهاية
        4. إذا كان وقت النهاية: حفظ الإعدادات وجدولة المهام
    """
    try:
        # الحصول على البيانات من state
        data = await state.get_data()
        chat_id = data.get("chat_id")
        
        if not chat_id:
            await message.answer("❌ حدث خطأ")
            await state.clear()
            return
        
        # استخراج الوقت من الرسالة
        time_text = message.text.strip()
        
        # تحويل الوقت للصيغة الصحيحة (HH:MM)
        try:
            # محاولة تحليل الوقت
            if ":" in time_text:
                parts = time_text.split(":")
                hour = int(parts[0])
                minute = int(parts[1].split()[0])  # إزالة AM/PM إن وجد
                
                # التحقق من الصحة
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("Invalid time")
                
                formatted_time = f"{hour:02d}:{minute:02d}"
            else:
                raise ValueError("Invalid format")
                
        except:
            await message.answer(
                "❌ صيغة الوقت غير صحيحة\n\n"
                "يرجى إرسال الوقت بالصيغة: HH:MM\n"
                "مثال: 23:00 أو 14:30"
            )
            return
        
        # حفظ وقت البداية وطلب وقت النهاية
        await state.update_data(from_time=formatted_time)
        await state.set_state(SilentStates.waiting_for_to_time)
        
        await message.answer(
            f"✅ تم حفظ وقت البداية: {formatted_time}\n\n"
            f"الآن أرسل وقت **نهاية** القفل:\n"
            f"مثال: `08:00` أو `6:00 AM`\n\n"
            f"ℹ️ سيتم فتح المجموعة تلقائياً في هذا الوقت يومياً"
        )
        
    except Exception as e:
        logger.error(f"Error in process_from_time: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.message(SilentStates.waiting_for_to_time)
async def process_to_time(message: Message, state: FSMContext):
    """
    الوصف:
        معالج استقبال وقت نهاية القفل من المستخدم
    
    المعاملات:
        message (Message): رسالة المستخدم
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        1. استقبال الوقت وتحويله للصيغة الصحيحة (HH:MM)
        2. التحقق من صحة الصيغة
        3. حفظ الإعدادات وجدولة المهام
    """
    try:
        # الحصول على البيانات من state
        data = await state.get_data()
        chat_id = data.get("chat_id")
        from_time = data.get("from_time")
        
        if not chat_id or not from_time:
            await message.answer("❌ حدث خطأ")
            await state.clear()
            return
        
        # استخراج الوقت من الرسالة
        time_text = message.text.strip()
        
        # تحويل الوقت للصيغة الصحيحة (HH:MM)
        try:
            # محاولة تحليل الوقت
            if ":" in time_text:
                parts = time_text.split(":")
                hour = int(parts[0])
                minute = int(parts[1].split()[0])  # إزالة AM/PM إن وجد
                
                # التحقق من الصحة
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("Invalid time")
                
                formatted_time = f"{hour:02d}:{minute:02d}"
            else:
                raise ValueError("Invalid format")
                
        except:
            await message.answer(
                "❌ صيغة الوقت غير صحيحة\n\n"
                "يرجى إرسال الوقت بالصيغة: HH:MM\n"
                "مثال: 08:00 أو 06:30"
            )
            return
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await message.answer("❌ المجموعة غير موجودة")
            await state.clear()
            return
        
        # حفظ الأوقات
        group.silent.from_time = from_time
        group.silent.to_time = formatted_time
        await group.save()
        
        # جدولة المهام
        from bot.services.scheduler import schedule_daily_lock
        await schedule_daily_lock(message.bot, chat_id, from_time, formatted_time)
        
        logger.info(
            f"User {message.from_user.id} set daily lock for group {chat_id}: "
            f"{from_time} - {formatted_time}"
        )
        
        # عرض رسالة نجاح
        await message.answer(
            f"{EMOJI_SUCCESS} **تم إعداد القفل اليومي بنجاح!**\n\n"
            f"🔕 وقت القفل: {from_time}\n"
            f"🔔 وقت الفتح: {formatted_time}\n\n"
            f"ℹ️ سيتم تطبيق القفل تلقائياً كل يوم"
        )
        
        # إنهاء FSM
        await state.clear()
        
        # العودة للإعدادات
        is_locked = False  # سنحصل عليها من API
        await message.answer(
            "🔕 **إعدادات قفل المجموعة**\n\n"
            "اختر الإعداد المطلوب:",
            reply_markup=build_silent_settings_keyboard(chat_id, is_locked)
        )
        
    except Exception as e:
        logger.error(f"Error in process_to_time: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.callback_query(F.data.startswith("silent:timer:"))
async def start_timer_lock_setup(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "قفل مؤقت"
        يبدأ عملية إعداد قفل مؤقت لمدة محددة
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        1. طلب المدة بالدقائق
        2. قفل المجموعة فوراً
        3. جدولة فتح المجموعة بعد المدة المحددة
    
    مثال:
        المشرف يضغط على: "⏰ قفل مؤقت"
        البوت يطلب: "أرسل المدة بالدقائق (مثال: 30)"
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # حفظ البيانات في state
        await state.update_data(chat_id=chat_id)
        
        # تغيير حالة FSM
        await state.set_state(SilentStates.waiting_for_timer_duration)
        
        # طلب المدة
        await callback.message.edit_text(
            f"⏰ **قفل مؤقت**\n\n"
            f"أرسل المدة بالدقائق:\n"
            f"مثال: `30` (نصف ساعة)\n"
            f"مثال: `60` (ساعة واحدة)\n"
            f"مثال: `120` (ساعتين)\n\n"
            f"ℹ️ سيتم قفل المجموعة فوراً وفتحها تلقائياً بعد المدة المحددة",
            reply_markup=build_cancel_keyboard()
        )
        
        await callback.answer("✍️ أرسل المدة")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_timer_lock_setup: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.message(SilentStates.waiting_for_timer_duration)
async def process_timer_duration(message: Message, state: FSMContext):
    """
    الوصف:
        معالج استقبال مدة القفل المؤقت
    
    المعاملات:
        message (Message): رسالة المستخدم
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        1. استقبال المدة والتحقق من صحتها
        2. قفل المجموعة فوراً
        3. جدولة فتح المجموعة بعد المدة
    """
    try:
        # الحصول على البيانات
        data = await state.get_data()
        chat_id = data.get("chat_id")
        
        if not chat_id:
            await message.answer("❌ حدث خطأ")
            await state.clear()
            return
        
        # استخراج المدة
        try:
            duration = int(message.text.strip())
            
            if duration <= 0 or duration > 1440:  # حد أقصى 24 ساعة
                raise ValueError("Invalid duration")
                
        except:
            await message.answer(
                "❌ المدة غير صحيحة\n\n"
                "يرجى إرسال رقم بين 1 و 1440 (دقيقة)"
            )
            return
        
        # قفل المجموعة
        from bot.services.permissions import close_group
        await close_group(message.bot, chat_id)
        
        # جدولة الفتح
        from bot.services.scheduler import schedule_timer_unlock
        unlock_time = datetime.now() + timedelta(minutes=duration)
        await schedule_timer_unlock(message.bot, chat_id, unlock_time)
        
        # حفظ في قاعدة البيانات
        group = await Group.find_one(Group.chat_id == chat_id)
        if group:
            group.silent.timer_unlock_time = unlock_time
            await group.save()
        
        logger.info(
            f"User {message.from_user.id} set timer lock for group {chat_id}: "
            f"{duration} minutes"
        )
        
        # عرض رسالة نجاح
        hours = duration // 60
        minutes = duration % 60
        duration_text = ""
        if hours > 0:
            duration_text += f"{hours} ساعة "
        if minutes > 0:
            duration_text += f"{minutes} دقيقة"
        
        await message.answer(
            f"{EMOJI_SUCCESS} **تم قفل المجموعة مؤقتاً!**\n\n"
            f"⏰ المدة: {duration_text}\n"
            f"🔓 وقت الفتح: {unlock_time.strftime('%H:%M')}\n\n"
            f"ℹ️ سيتم فتح المجموعة تلقائياً"
        )
        
        # إرسال رسالة في المجموعة
        try:
            await message.bot.send_message(
                chat_id,
                f"🔕 **تم قفل المجموعة مؤقتاً**\n\n"
                f"⏰ المدة: {duration_text}\n"
                f"🔓 سيتم الفتح في: {unlock_time.strftime('%H:%M')}"
            )
        except:
            pass
        
        # إنهاء FSM
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in process_timer_duration: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.callback_query(F.data.startswith("silent:permissions:"))
async def show_permissions_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "ضبط الصلاحيات"
        يعرض قائمة بجميع الصلاحيات (8 أنواع) مع حالة كل صلاحية
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
    
    الإرجاع:
        None
    
    السلوك:
        1. عرض قائمة الصلاحيات:
           - إرسال الرسائل
           - إرسال الوسائط
           - إرسال الملصقات
           - إرسال الاستفتاءات
           - معاينة الروابط
           - تغيير معلومات المجموعة
           - إضافة الأعضاء
           - تثبيت الرسائل
        2. كل صلاحية لها زر للتبديل
    
    الملفات المرتبطة:
        - bot/keyboards/builders.py: build_permissions_keyboard
        - bot/utils/constants.py: PERMISSION_NAMES
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # تحويل الصلاحيات إلى dict
        permissions = group.silent.saved_permissions.dict() if group.silent.saved_permissions else {}
        
        # إذا لم تكن محفوظة، استخدم الصلاحيات الحالية
        if not permissions:
            try:
                chat = await callback.bot.get_chat(chat_id)
                permissions = {
                    "can_send_messages": chat.permissions.can_send_messages,
                    "can_send_media_messages": chat.permissions.can_send_media_messages,
                    "can_send_other_messages": chat.permissions.can_send_other_messages,
                    "can_send_polls": chat.permissions.can_send_polls,
                    "can_add_web_page_previews": chat.permissions.can_add_web_page_previews,
                    "can_change_info": chat.permissions.can_change_info,
                    "can_invite_users": chat.permissions.can_invite_users,
                    "can_pin_messages": chat.permissions.can_pin_messages
                }
            except:
                # استخدام القيم الافتراضية
                permissions = {key: True for key in PERMISSION_NAMES.keys()}
        
        # عرض إعدادات الصلاحيات
        await callback.message.edit_text(
            f"🏷 **ضبط الصلاحيات**\n\n"
            f"📌 المجموعة: {group.chat_title}\n\n"
            f"ℹ️ هذه الصلاحيات سيتم استعادتها عند فتح المجموعة\n"
            f"✅ = مسموح\n"
            f"❌ = ممنوع\n\n"
            f"اضغط على الصلاحية لتبديلها:",
            reply_markup=build_permissions_keyboard(chat_id, permissions)
        )
        
        await callback.answer("🏷 ضبط الصلاحيات")
        
        logger.info(f"User {callback.from_user.id} opened permissions for group {chat_id}")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_permissions_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("permissions:toggle:"))
async def toggle_permission(callback: CallbackQuery):
    """
    الوصف:
        معالج تبديل صلاحية معينة
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "permissions:toggle:{chat_id}:{permission_key}"
    
    الإرجاع:
        None
    
    السلوك:
        1. تبديل حالة الصلاحية
        2. حفظ في قاعدة البيانات
        3. تحديث الأزرار
    """
    try:
        # استخراج البيانات
        parts = callback.data.split(":", 3)
        chat_id = int(parts[2])
        permission_key = parts[3]
        
        # التحقق من صحة الصلاحية
        if permission_key not in PERMISSION_NAMES:
            await callback.answer("❌ صلاحية غير صحيحة", show_alert=True)
            return
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # الحصول على الصلاحيات الحالية
        if not group.silent.saved_permissions:
            from bot.database.models import SavedPermissions
            group.silent.saved_permissions = SavedPermissions()
        
        # تبديل الصلاحية
        current_value = getattr(group.silent.saved_permissions, permission_key)
        new_value = not current_value
        setattr(group.silent.saved_permissions, permission_key, new_value)
        
        # حفظ التغيير
        await group.save()
        
        # تحديد نص الإشعار
        permission_name = PERMISSION_NAMES[permission_key]
        status_text = "مسموح" if new_value else "ممنوع"
        status_emoji = EMOJI_SUCCESS if new_value else EMOJI_ERROR
        
        logger.info(
            f"User {callback.from_user.id} toggled permission {permission_key} "
            f"to {new_value} for group {chat_id}"
        )
        
        # تحديث الأزرار
        permissions = group.silent.saved_permissions.dict()
        await callback.message.edit_reply_markup(
            reply_markup=build_permissions_keyboard(chat_id, permissions)
        )
        
        # إرسال إشعار
        await callback.answer(f"{status_emoji} {permission_name}: {status_text}")
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in toggle_permission: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("silent:messages:"))
async def show_lock_messages_settings(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "ضبط رسائل القفل"
        يسمح بتخصيص الرسائل التي تظهر عند القفل والفتح
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        1. عرض الرسائل الحالية
        2. السماح بتعديل رسالة القفل
        3. السماح بتعديل رسالة الفتح
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        #الرسائل الحالية
        lock_msg = group.silent.lock_message or "🔕 تم قفل المجموعة"
        unlock_msg = group.silent.unlock_message or "🔔 تم فتح المجموعة"
        
        # عرض الإعدادات
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 تعديل رسالة القفل", callback_data=f"silent:edit_lock_msg:{chat_id}")],
            [InlineKeyboardButton(text="📝 تعديل رسالة الفتح", callback_data=f"silent:edit_unlock_msg:{chat_id}")],
            [InlineKeyboardButton(text="🔙 الرجوع", callback_data=f"back:silent:{chat_id}")]
        ])
        
        await callback.message.edit_text(
            f"📨 **ضبط رسائل القفل**\n\n"
            f"📌 المجموعة: {group.chat_title}\n\n"
            f"🔕 رسالة القفل الحالية:\n{lock_msg}\n\n"
            f"🔔 رسالة الفتح الحالية:\n{unlock_msg}\n\n"
            f"اختر الرسالة التي تريد تعديلها:",
            reply_markup=keyboard
        )
        
        await callback.answer("📨 ضبط الرسائل")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_lock_messages_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("silent:edit_lock_msg:"))
async def start_edit_lock_message(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "تعديل رسالة القفل"
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        طلب الرسالة الجديدة من المستخدم
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # حفظ البيانات في state
        await state.update_data(chat_id=chat_id, message_type="lock")
        
        # تغيير حالة FSM
        await state.set_state(SilentStates.waiting_for_lock_message)
        
        # طلب الرسالة
        await callback.message.edit_text(
            f"📝 **تعديل رسالة القفل**\n\n"
            f"أرسل الرسالة الجديدة التي تريد عرضها عند قفل المجموعة:\n\n"
            f"ℹ️ يمكنك استخدام Markdown للتنسيق",
            reply_markup=build_cancel_keyboard()
        )
        
        await callback.answer("✍️ أرسل الرسالة")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_edit_lock_message: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("silent:edit_unlock_msg:"))
async def start_edit_unlock_message(callback: CallbackQuery, state: FSMContext):
    """
    الوصف:
        معالج زر "تعديل رسالة الفتح"
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        طلب الرسالة الجديدة من المستخدم
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # حفظ البيانات في state
        await state.update_data(chat_id=chat_id, message_type="unlock")
        
        # تغيير حالة FSM
        await state.set_state(SilentStates.waiting_for_lock_message)
        
        # طلب الرسالة
        await callback.message.edit_text(
            f"📝 **تعديل رسالة الفتح**\n\n"
            f"أرسل الرسالة الجديدة التي تريد عرضها عند فتح المجموعة:\n\n"
            f"ℹ️ يمكنك استخدام Markdown للتنسيق",
            reply_markup=build_cancel_keyboard()
        )
        
        await callback.answer("✍️ أرسل الرسالة")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_edit_unlock_message: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.message(SilentStates.waiting_for_lock_message)
async def process_lock_message(message: Message, state: FSMContext):
    """
    الوصف:
        معالج استقبال رسالة القفل/الفتح من المستخدم
    
    المعاملات:
        message (Message): رسالة المستخدم
        state (FSMContext): حالة FSM
    
    الإرجاع:
        None
    
    السلوك:
        1. استقبال الرسالة
        2. حفظها في قاعدة البيانات
        3. عرض رسالة نجاح
    """
    try:
        # الحصول على البيانات
        data = await state.get_data()
        chat_id = data.get("chat_id")
        message_type = data.get("message_type")
        
        if not chat_id or not message_type:
            await message.answer("❌ حدث خطأ")
            await state.clear()
            return
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await message.answer("❌ المجموعة غير موجودة")
            await state.clear()
            return
        
        # حفظ الرسالة
        new_message = message.text.strip()
        
        if message_type == "lock":
            group.silent.lock_message = new_message
            message_name = "القفل"
        else:
            group.silent.unlock_message = new_message
            message_name = "الفتح"
        
        await group.save()
        
        logger.info(
            f"User {message.from_user.id} updated {message_type} message "
            f"for group {chat_id}"
        )
        
        # عرض رسالة نجاح
        await message.answer(
            f"{EMOJI_SUCCESS} **تم تحديث رسالة {message_name}**\n\n"
            f"الرسالة الجديدة:\n{new_message}"
        )
        
        # إنهاء FSM
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in process_lock_message: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ")
        await state.clear()


@router.callback_query(F.data.startswith("back:silent:"))
async def back_to_silent_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "الرجوع" إلى إعدادات القفل الرئيسية
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
    
    الإرجاع:
        None
    
    السلوك:
        العودة لقائمة إعدادات القفل الرئيسية
    """
    try:
        # استخراج chat_id
        chat_id = callback.data.split(":", 2)[2]
        
        # إنشاء callback جديد
        new_callback_data = f"group_settings:silent:{chat_id}"
        callback.data = new_callback_data
        
        # استدعاء دالة عرض إعدادات القفل
        await show_silent_settings(callback)
        
    except Exception as e:
        logger.error(f"Error in back_to_silent_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


def register_callbacks(dp):
    """
    الوصف:
        تسجيل معالجات أزرار نظام القفل في الـ Dispatcher
        يتم استدعاء هذه الدالة من bot/keyboards/callbacks/__init__.py
    
    المعاملات:
        dp (Dispatcher): الـ Dispatcher الخاص بـ aiogram
    
    الإرجاع:
        None
    
    الملفات المرتبطة:
        - bot/keyboards/callbacks/__init__.py: يستدعي هذه الدالة
    """
    dp.include_router(router)