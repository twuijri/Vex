import sqlite3
import os
import json
from contextlib import contextmanager
from typing import Optional
from backend.models.config import SystemConfig


# ==============================================================================
# 📄 File: backend/database/local_db.py
# 📝 Description: Handles local SQLite database for system configuration.
# 📝 الوصف: إدارة قاعدة بيانات SQLite المحلية لتخزين إعدادات النظام.
#
# 💡 Why SQLite? 
# We use SQLite here to store "Bootstrap Data" (like Mongo URI) so the system 
# can start even if MongoDB is down or not configured yet.
# 💡 لماذا SQLite؟
# نستخدمها لتخزين بيانات بدء التشغيل (مثل رابط المونجو) لضمان عمل النظام
# حتى لو كانت قاعدة البيانات الرئيسية غير متصلة.
# ==============================================================================

DB_PATH = "/app/data/config.db"
if not os.path.exists("/app/data"):
    DB_PATH = os.path.join(os.getcwd(), "data", "config.db")



def init_db():
    """
    Initialize the SQLite table if it doesn't exist.
    🔹 إنشاء جدول الإعدادات إذا لم يكن موجوداً.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Key-Value store table | جدول تخزين مفتاح-قيمة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        conn.commit()

@contextmanager
def get_db_connection():
    """
    Context manager for database connection.
    🔹 مدير سياق للاتصال بقاعدة البيانات (يضمن إغلاق الاتصال).
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def get_system_config() -> SystemConfig:
    """
    Retrieve system configuration from SQLite.
    🔹 جلب إعدادات النظام من قاعدة البيانات المحلية.
    """
    init_db()
    config = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM system_config")
        rows = cursor.fetchall()
        for key, value in rows:
            if key == "telegram_admin_ids":
                try:
                    config[key] = json.loads(value)
                except:
                    config[key] = []
            elif key in ["support_group_id", "log_channel_id"]:
                 # Helper to ensure ints, though pydantic does it too.
                 if value:
                     try:
                         config[key] = int(value)
                     except:
                         pass
            else:
                config[key] = value

    
    # Defaults if config is empty (First Run)
    # قيم افتراضية إذا كانت الإعدادات فارغة (أول تشغيل)
    # Defaults if config is empty (First Run)
    # قيم افتراضية إذا كانت الإعدادات فارغة (أول تشغيل)
    if not config:
        # Check Environment Variables first
        env_admin_user = os.getenv("ADMIN_USERNAME", "")
        env_admin_pass = os.getenv("ADMIN_PASSWORD", "")
        env_mongo_uri = os.getenv("MONGODB_URI")
        env_bot_token = os.getenv("BOT_TOKEN")

        password_hash = ""
        if env_admin_pass:
             try:
                 from backend.auth import get_password_hash
                 password_hash = get_password_hash(env_admin_pass)
             except ImportError:
                 pass # Should not happen

        return SystemConfig(
            admin_username=env_admin_user, 
            admin_password_hash=password_hash,
            mongo_uri=env_mongo_uri,
            bot_token=env_bot_token, 
            is_setup_complete=False
        )
    
    return SystemConfig(**config)

def save_system_config(config: SystemConfig):
    """
    Save system configuration to SQLite.
    🔹 حفظ إعدادات النظام في قاعدة البيانات المحلية.
    """
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        data = config.model_dump()
        for key, value in data.items():
            if value is not None:
                # Handle Lists like telegram_admin_ids
                if isinstance(value, list) or isinstance(value, dict):
                    import json
                    value = json.dumps(value)
                
                # Insert or Update existing key
                # إدراج أو تحديث المفتاح الموجود
                cursor.execute(
                    "INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)",
                    (key, str(value))
                )

        conn.commit()
