"""
معالجات الأوامر والرسائل (Handlers)

هذا الملف مسؤول عن تسجيل جميع معالجات البوت في الـ Dispatcher
"""
from aiogram import Dispatcher


def setup_handlers(dp: Dispatcher):
    """
    الوصف:
        تسجيل جميع معالجات البوت في الـ Dispatcher
        يتم استدعاء هذه الدالة من bot/core/bot.py
    
    المعاملات:
        dp (Dispatcher): الـ Dispatcher الخاص بـ aiogram
    
    الإرجاع:
        None
    
    الملفات المرتبطة:
        - bot/core/bot.py: يستدعي هذه الدالة عند تهيئة البوت
        - bot/handlers/start.py: معالج أمر /start
        - bot/handlers/admin.py: معالج أمر /admin
        - bot/handlers/groups/: معالجات المجموعات
        - bot/handlers/support/: معالجات الدعم
    """
    from . import start, admin
    
    # تسجيل معالجات الأوامر الأساسية
    start.register_handlers(dp)
    admin.register_handlers(dp)
    
    # TODO: تسجيل معالجات المجموعات
    # from .groups import activation, filters, welcome, rules, members
    # activation.register_handlers(dp)
    # filters.register_handlers(dp)
    # welcome.register_handlers(dp)
    # rules.register_handlers(dp)
    # members.register_handlers(dp)
    
    # TODO: تسجيل معالجات الدعم
    # from .support import relay, block
    # relay.register_handlers(dp)
    # block.register_handlers(dp)
