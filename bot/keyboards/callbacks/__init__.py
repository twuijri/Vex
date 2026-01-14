"""
معالجات الأزرار التفاعلية (Callback Handlers)

هذا الملف مسؤول عن تسجيل جميع معالجات الأزرار في الـ Dispatcher
"""
from aiogram import Dispatcher


def setup_callbacks(dp: Dispatcher):
    """
    الوصف:
        تسجيل جميع معالجات الأزرار في الـ Dispatcher
        يتم استدعاء هذه الدالة من bot/core/bot.py
    
    المعاملات:
        dp (Dispatcher): الـ Dispatcher الخاص بـ aiogram
    
    الإرجاع:
        None
    
    الملفات المرتبطة:
        - bot/core/bot.py: يستدعي هذه الدالة عند تهيئة البوت
        - bot/keyboards/callbacks/main.py: معالجات القائمة الرئيسية
        - bot/keyboards/callbacks/groups.py: معالجات إدارة المجموعات
        - bot/keyboards/callbacks/media.py: معالجات فلاتر الوسائط
        - bot/keyboards/callbacks/words.py: معالجات الكلمات
        - bot/keyboards/callbacks/silent.py: معالجات نظام القفل
        - bot/keyboards/callbacks/welcome.py: معالجات الترحيب
        - bot/keyboards/callbacks/rules.py: معالجات القوانين
    """
    from . import main, groups, media, words, silent, welcome, rules, database
    
    # تسجيل معالجات القائمة الرئيسية
    main.register_callbacks(dp)
    
    # تسجيل معالجات إدارة المجموعات
    groups.register_callbacks(dp)
    
    # تسجيل معالجات فلاتر الوسائط
    media.register_callbacks(dp)
    
    # تسجيل معالجات الكلمات المحظورة/المسموح بها
    words.register_callbacks(dp)
    
    # تسجيل معالجات نظام القفل
    silent.register_callbacks(dp)
    
    # تسجيل معالجات الترحيب
    welcome.register_callbacks(dp)
    
    # تسجيل معالجات القوانين
    rules.register_callbacks(dp)
    
    # تسجيل معالجات قاعدة البيانات
    dp.include_router(database.router)
    
    # TODO: تسجيل نظام الدعم
    # from . import support
    # support.register_callbacks(dp)
