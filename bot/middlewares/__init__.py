"""
Middlewares للبوت

هذا المجلد يحتوي على الـ Middlewares:
- admin_check.py: التحقق من صلاحيات المشرفين
- throttling.py: منع الإزعاج (Rate limiting)
"""
import logging

logger = logging.getLogger(__name__)


def setup_middlewares(dp):
    """
    الوصف:
        تسجيل جميع الـ Middlewares في الـ Dispatcher
    
    المعاملات:
        dp (Dispatcher): الـ Dispatcher الخاص بـ aiogram
    
    الإرجاع:
        None
    
    الملفات المرتبطة:
        - bot/core/bot.py: يستدعي هذه الدالة
    """
    # TODO: إضافة Middlewares عند الحاجة
    # from . import admin_check, throttling
    # dp.message.middleware(admin_check.AdminCheckMiddleware())
    # dp.message.middleware(throttling.ThrottlingMiddleware())
    
    logger.info("Middlewares setup completed (currently empty)")
