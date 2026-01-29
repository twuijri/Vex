from fastapi import APIRouter, HTTPException
from backend.models.config import SystemConfig
from backend.database.local_db import save_system_config, get_system_config
import bcrypt
import secrets
import string

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
    
    # Ensure database name has a safe default
    if not config.mongo_db_name:
        config.mongo_db_name = "Vex_db"

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

@router.post("/api/reset-password")
async def reset_password():
    """
    Reset admin password - generates random password and logs it.
    🔹 إعادة تعيين كلمة مرور المدير - يولد كلمة مرور عشوائية ويسجلها في logs.
    
    Security: Only works if system is already setup.
    الأمان: يعمل فقط إذا كان النظام معداً مسبقاً.
    """
    import datetime
    
    current = get_system_config()
    if not current.is_setup_complete:
        raise HTTPException(status_code=400, detail="النظام غير معد. استخدم /setup أولاً (System not setup yet).")
    
    # Generate random password | توليد كلمة مرور عشوائية
    alphabet = string.ascii_letters + string.digits
    random_password = ''.join(secrets.choice(alphabet) for _ in range(16))
    
    # Hash the new password | تشفير كلمة المرور الجديدة
    hashed = bcrypt.hashpw(random_password.encode('utf-8'), bcrypt.gensalt())
    current.admin_password_hash = hashed.decode('utf-8')
    
    # Save updated config | حفظ الإعدادات المحدثة
    save_system_config(current)
    
    # Log the password prominently | تسجيل كلمة المرور في logs بشكل واضح
    log_message = f"""
    ═══════════════════════════════════════════════════════════
    🔐 PASSWORD RESET - إعادة تعيين كلمة المرور
    ═══════════════════════════════════════════════════════════
    Timestamp: {datetime.datetime.now()}
    Username: {current.admin_username}
    New Password: {random_password}
    ═══════════════════════════════════════════════════════════
    ⚠️  IMPORTANT: Save this password! It will not be shown again.
    ⚠️  مهم: احفظ كلمة المرور! لن تظهر مرة أخرى.
    ═══════════════════════════════════════════════════════════
    """
    
    print(log_message)
    
    # Also save to file for easier retrieval | حفظ في ملف للوصول السهل
    try:
        with open("/app/data/password_reset.log", "a") as f:
            f.write(log_message + "\n")
    except Exception as e:
        print(f"Could not write to password reset log file: {e}")
    
    return {
        "status": "success",
        "message": "تم إعادة تعيين كلمة المرور. راجع logs للحصول على كلمة المرور الجديدة (Password reset. Check container logs for new password).",
        "username": current.admin_username
    }
