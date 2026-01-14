"""
معالجات أزرار فلاتر الوسائط

هذا الملف مسؤول عن معالجة الأزرار الخاصة بتبديل فلاتر الوسائط (20 نوع)
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.database.models import Group
from bot.keyboards.builders import build_media_settings_keyboard
from bot.utils.constants import EMOJI_SUCCESS, EMOJI_ERROR, MEDIA_NAMES

logger = logging.getLogger(__name__)

# إنشاء Router للمعالجات
router = Router(name="media_callbacks")


@router.callback_query(F.data.startswith("group_settings:media:"))
async def show_media_settings(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "إعدادات الوسائط"
        يعرض قائمة بجميع أنواع الوسائط (20 نوع) مع حالة كل نوع
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "group_settings:media:{chat_id}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id من callback.data
        2. جلب إعدادات الوسائط من قاعدة البيانات
        3. عرض قائمة بجميع أنواع الوسائط مع حالتها (✅/❌)
        4. كل نوع له زر للتبديل بين السماح والمنع
    
    أنواع الوسائط (20 نوع):
        - document: الملفات
        - photo: الصور
        - video: الفيديو
        - voice: تسجيلات الصوت
        - audio: الموسيقى
        - sticker: الملصقات
        - video_note: ملاحظات الفيديو
        - gif: الصور المتحركة
        - forward: إعادة التوجيه
        - telegram_link: روابط تيليجرام
        - link: الروابط
        - mobile: أرقام الجوال
        - tag: التاقات (@username)
        - hashtag: الهاشتاق (#tag)
        - bots: البوتات
        - join_service: إشعارات الدخول
        - left_service: إشعارات الخروج
        - location: المواقع
        - games: الألعاب
        - text: النصوص
    
    الملفات المرتبطة:
        - bot/database/models.py: Group.media_filters
        - bot/keyboards/builders.py: build_media_settings_keyboard
        - bot/utils/constants.py: MEDIA_NAMES
    
    مثال:
        المشرف يضغط على: "🌌 إعدادات الوسائط"
        البوت يعرض: قائمة الوسائط مع حالة كل نوع
    """
    try:
        # استخراج chat_id
        chat_id = int(callback.data.split(":", 2)[2])
        
        # جلب بيانات المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # تحويل MediaFilters إلى dict
        media_filters = group.media_filters.dict()
        
        # عرض إعدادات الوسائط
        await callback.message.edit_text(
            f"🌌 **إعدادات الوسائط**\n\n"
            f"📌 المجموعة: {group.chat_title}\n\n"
            f"✅ = مسموح به\n"
            f"❌ = ممنوع\n\n"
            f"اضغط على الحالة لتبديلها:",
            reply_markup=build_media_settings_keyboard(chat_id, media_filters)
        )
        
        await callback.answer("🌌 إعدادات الوسائط")
        
        logger.info(f"User {callback.from_user.id} opened media settings for group {chat_id}")
        
    except ValueError:
        await callback.answer("❌ معرف مجموعة غير صحيح", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_media_settings: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


@router.callback_query(F.data.startswith("media:toggle:"))
async def toggle_media_filter(callback: CallbackQuery):
    """
    الوصف:
        معالج تبديل حالة فلتر وسائط معين
        يقوم بتبديل الحالة بين السماح (True) والمنع (False)
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "media:toggle:{chat_id}:{media_type}"
            - media_type: نوع الوسائط (photo, video, sticker, etc.)
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج chat_id و media_type من callback.data
        2. جلب المجموعة من قاعدة البيانات
        3. تبديل حالة الفلتر (True <-> False)
        4. حفظ التغيير في قاعدة البيانات
        5. تحديث الأزرار لإظهار الحالة الجديدة
        6. إرسال إشعار Toast للمستخدم
    
    الملفات المرتبطة:
        - bot/database/models.py: Group.media_filters
        - bot/keyboards/builders.py: build_media_settings_keyboard
        - bot/handlers/groups/filters.py: تطبيق الفلاتر في المجموعات
    
    مثال:
        المشرف يضغط على: "✅" بجانب "الصور"
        البوت ينفذ: تغيير الحالة إلى "❌"
        البوت يعرض: Toast "❌ تم منع الصور"
    """
    try:
        # استخراج البيانات
        parts = callback.data.split(":", 3)
        chat_id = int(parts[2])
        media_type = parts[3]
        
        # التحقق من صحة نوع الوسائط
        if media_type not in MEDIA_NAMES:
            await callback.answer("❌ نوع وسائط غير صحيح", show_alert=True)
            return
        
        # جلب المجموعة
        group = await Group.find_one(Group.chat_id == chat_id)
        
        if not group:
            await callback.answer("❌ المجموعة غير موجودة", show_alert=True)
            return
        
        # الحصول على الحالة الحالية
        current_value = getattr(group.media_filters, media_type)
        
        # تبديل الحالة
        new_value = not current_value
        setattr(group.media_filters, media_type, new_value)
        
        # حفظ التغيير
        await group.save()
        
        # تحديد نص الإشعار
        media_name = MEDIA_NAMES[media_type]
        status_text = "مسموح به" if new_value else "ممنوع"
        status_emoji = EMOJI_SUCCESS if new_value else EMOJI_ERROR
        
        logger.info(
            f"User {callback.from_user.id} toggled {media_type} "
            f"to {new_value} for group {chat_id}"
        )
        
        # تحديث الأزرار
        media_filters = group.media_filters.dict()
        await callback.message.edit_reply_markup(
            reply_markup=build_media_settings_keyboard(chat_id, media_filters)
        )
        
        # إرسال إشعار Toast
        await callback.answer(
            f"{status_emoji} {media_name}: {status_text}",
            show_alert=False
        )
        
    except ValueError:
        await callback.answer("❌ بيانات غير صحيحة", show_alert=True)
    except Exception as e:
        logger.error(f"Error in toggle_media_filter: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ أثناء التبديل", show_alert=True)


@router.callback_query(F.data.startswith("media:info:"))
async def show_media_info(callback: CallbackQuery):
    """
    الوصف:
        معالج زر "معلومات" لنوع وسائط معين
        يعرض معلومات توضيحية عن نوع الوسائط
    
    المعاملات:
        callback (CallbackQuery): بيانات الزر المضغوط
            - callback.data format: "media:info:{media_type}"
    
    الإرجاع:
        None
    
    السلوك:
        1. استخراج media_type من callback.data
        2. عرض معلومات توضيحية عن هذا النوع
        3. الإشعار يظهر كـ Toast (لا يغير الشاشة)
    
    معلومات كل نوع:
        - document: ملفات PDF, Word, Excel, etc.
        - photo: الصور العادية
        - video: مقاطع الفيديو
        - voice: تسجيلات الصوت
        - audio: ملفات الموسيقى
        - sticker: الملصقات
        - video_note: الفيديوهات الدائرية
        - gif: الصور المتحركة
        - forward: الرسائل المعاد توجيهها
        - telegram_link: روابط القنوات والمجموعات
        - link: الروابط الخارجية
        - mobile: أرقام الهاتف
        - tag: منشن المستخدمين (@username)
        - hashtag: الوسوم (#tag)
        - bots: البوتات الأخرى
        - join_service: رسائل "انضم للمجموعة"
        - left_service: رسائل "غادر المجموعة"
        - location: المواقع الجغرافية
        - games: الألعاب
        - text: الرسائل النصية
    
    مثال:
        المستخدم يضغط على: "🎆 الصور"
        البوت يعرض: Toast "الصور العادية التي يرسلها الأعضاء"
    """
    try:
        # استخراج نوع الوسائط
        media_type = callback.data.split(":", 2)[2]
        
        # معلومات كل نوع
        media_info = {
            "document": "📄 الملفات: PDF, Word, Excel, ZIP, وغيرها",
            "photo": "🖼 الصور: الصور العادية التي يرسلها الأعضاء",
            "video": "🎬 الفيديو: مقاطع الفيديو العادية",
            "voice": "🎤 تسجيلات الصوت: الرسائل الصوتية",
            "audio": "🎵 الموسيقى: ملفات الموسيقى والأغاني",
            "sticker": "😊 الملصقات: الملصقات المتحركة والثابتة",
            "video_note": "⭕️ ملاحظات الفيديو: الفيديوهات الدائرية",
            "gif": "🎭 الصور المتحركة: GIF animations",
            "forward": "↪️ إعادة التوجيه: الرسائل المعاد توجيهها من قنوات أو مجموعات",
            "telegram_link": "📢 روابط تيليجرام: روابط القنوات والمجموعات (t.me/...)",
            "link": "🔗 الروابط: الروابط الخارجية (http://...)",
            "mobile": "📱 أرقام الجوال: أرقام الهاتف في الرسائل",
            "tag": "👤 التاقات: منشن المستخدمين (@username)",
            "hashtag": "#️⃣ الهاشتاق: الوسوم (#tag)",
            "bots": "🤖 البوتات: البوتات الأخرى في المجموعة",
            "join_service": "🔻 إشعارات الدخول: رسائل 'انضم للمجموعة'",
            "left_service": "🔺 إشعارات الخروج: رسائل 'غادر المجموعة'",
            "location": "📍 المواقع: المواقع الجغرافية",
            "games": "🎮 الألعاب: ألعاب تيليجرام",
            "text": "📝 النصوص: الرسائل النصية العادية"
        }
        
        # الحصول على المعلومات
        info_text = media_info.get(media_type, "ℹ️ معلومات غير متوفرة")
        
        # عرض المعلومات كـ Toast
        await callback.answer(info_text, show_alert=True)
        
    except Exception as e:
        logger.error(f"Error in show_media_info: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ", show_alert=True)


def register_callbacks(dp):
    """
    الوصف:
        تسجيل معالجات أزرار فلاتر الوسائط في الـ Dispatcher
        يتم استدعاء هذه الدالة من bot/keyboards/callbacks/__init__.py
    
    المعاملات:
        dp (Dispatcher): الـ Dispatcher الخاص بـ aiogram
    
    الإرجاع:
        None
    
    الملفات المرتبطة:
        - bot/keyboards/callbacks/__init__.py: يستدعي هذه الدالة
    """
    dp.include_router(router)
