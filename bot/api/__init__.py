"""
API settings - لتغيير اسم قاعدة البيانات من لوحة التحكم
"""
from typing import Optional
from bot.database.models import Group


async def update_group_database_name(
    chat_id: int,
    db_name: str
) -> bool:
    """
    تحديث اسم قاعدة البيانات للمجموعة
    
    Args:
        chat_id: معرّف المجموعة
        db_name: اسم قاعدة البيانات الجديد
    
    Returns:
        True إذا نجح التحديث
    """
    try:
        group = await Group.find_one(Group.chat_id == chat_id)
        if group:
            group.mongo_db_name = db_name
            await group.save()
            return True
        return False
    except Exception as e:
        print(f"خطأ في تحديث قاعدة البيانات: {e}")
        return False


async def get_group_database_name(chat_id: int) -> Optional[str]:
    """
    الحصول على اسم قاعدة البيانات للمجموعة
    
    Args:
        chat_id: معرّف المجموعة
    
    Returns:
        اسم قاعدة البيانات أو None
    """
    try:
        group = await Group.find_one(Group.chat_id == chat_id)
        if group:
            return group.mongo_db_name
        return None
    except Exception as e:
        print(f"خطأ في الحصول على قاعدة البيانات: {e}")
        return None
