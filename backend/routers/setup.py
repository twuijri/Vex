from fastapi import APIRouter, HTTPException
from backend.models.config import SystemConfig
from backend.database.local_db import save_system_config, get_system_config
import bcrypt

# ==============================================================================
# 📄 File: backend/routers/setup.py
# 📝 Description: API endpoints for the initial system setup wizard.
# 📝 الوصف: نقاط الاتصال الخاصة بمعالج الإعداد الأولي للنظام.
# ==============================================================================

router = APIRouter()

@router.post("/api/setup")
async def setup_system(config: SystemConfig):
    """
    Perform the initial system setup.
    🔹 تنفيذ الإعداد الأولي للنظام.
    
    Steps:
    1. Check if already setup -> Error if true.
    2. Hash the Admin Password.
    3. Save Config to SQLite.
    
    الخطوات:
    1. التحقق من الإعداد المسبق -> خطأ إذا كان معداً.
    2. تشفير كلمة مرور المدير.
    3. حفظ الإعدادات في قاعدة البيانات المحلية.
    """
    # Security check | فحص أمني
    current = get_system_config()
    if current.is_setup_complete:
        raise HTTPException(status_code=400, detail="تم إعداد النظام مسبقاً (System already setup).")
    
    # Hash password logic | منطق تشفير كلمة المرور
    if config.admin_password_hash:
        # bcrypt.hashpw requires bytes, so encode username/password
        hashed = bcrypt.hashpw(config.admin_password_hash.encode('utf-8'), bcrypt.gensalt())
        config.admin_password_hash = hashed.decode('utf-8')
    
    config.is_setup_complete = True
    save_system_config(config)
    
    return {"status": "success", "message": "تم إعداد النظام بنجاح. يرجى إعادة تشغيل الواجهة الخلفية (System configured successfully)."}

@router.get("/api/status")
async def get_status():
    """
    Check if the system is setup or not.
    🔹 التحقق مما إذا كان النظام معداً أم لا.
    """
    config = get_system_config()
    return {"setup_complete": config.is_setup_complete}
