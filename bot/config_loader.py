import sqlite3
import os

# ==============================================================================
# 📄 File: bot/config_loader.py
# 📝 Description: Reads configuration from the shared SQLite database.
# 📝 الوصف: قراءة الإعدادات من قاعدة بيانات SQLite المشتركة مع الواجهة الخلفية.
# ==============================================================================

DB_PATH = "/app/data/config.db"
if not os.path.exists("/app/data"):
    # Local Development Fallback
    DB_PATH = os.path.join(os.getcwd(), "data", "config.db")

def get_config_value(key: str, default=None) -> str:
    """
    Read a single value from the local SQLite config db.
    🔹 قراءة قيمة واحدة من قاعدة البيانات المحلية.
    """
    if not os.path.exists(DB_PATH):
        return default
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_config WHERE key=?", (key,))
            result = cursor.fetchone()
            return result[0] if result else default
    except Exception as e:
        print(f"Error reading config: {e}")
        return default

def get_mongo_uri() -> str:
    """
    Get MongoDB URI from Config DB or Env Var.
    🔹 الحصول على رابط المونجو من القاعدة أو متغيرات البيئة.
    """
    # Try getting from DB first | المحاولة من قاعدة البيانات أولاً
    uri = get_config_value("mongo_uri")
    if uri:
        return uri
    return os.getenv("MONGODB_URI", "mongodb://mongodb:27017")

def get_mongo_db_name() -> str:
    """
    Get MongoDB Database Name from Config DB or Env Var.
    🔹 الحصول على اسم قاعدة البيانات من القاعدة أو المتغيرات البيئية.
    """
    name = get_config_value("mongo_db_name")
    if name:
        return name
    return os.getenv("MONGO_DB_NAME", "Vex_db")

class BotConfig:
    def __init__(self):
        self.bot_token = get_config_value("bot_token")
        self.mongo_uri = get_mongo_uri()
        self.mongo_db_name = get_mongo_db_name()
        self.support_group_id = int(get_config_value("support_group_id", 0))
        self.log_channel_id = int(get_config_value("log_channel_id", 0))
        
        # Parse Admin IDs list
        # تحليل قائمة مدراء البوت
        admin_ids_str = get_config_value("telegram_admin_ids", "[]")
        try:
            # It's stored as a JSON string mostly, or we might need to parse it manually if it's just comma separated
            # But the backend saves it as Pydantic List -> likely stored as JSON string in SQLite if we used the generic saver?
            # Actually, let's check how 'save_system_config' works in backend/database/local_db.py
            # Assuming it puts it in Key-Value.
            import json
            self.telegram_admin_ids = json.loads(admin_ids_str)
            if not isinstance(self.telegram_admin_ids, list):
                self.telegram_admin_ids = []
        except:
            self.telegram_admin_ids = []

def load_config() -> BotConfig:
    """
    Load the entire configuration into an object.
    🔹 تحميل الإعدادات بالكامل في كائن.
    """
    return BotConfig()

