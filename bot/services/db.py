from motor.motor_asyncio import AsyncIOMotorClient
from bot.config_loader import get_mongo_uri, get_mongo_db_name
import logging
import dns.resolver
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, unquote

logger = logging.getLogger(__name__)

def get_current_timestamp():
    return datetime.utcnow()

def resolve_mongo_uri(uri: str) -> str:
    """
    Manually resolve mongodb+srv:// URI to mongodb:// using Google DNS.
    Workaround for Docker/PyMongo SRV resolution timeouts.
    """
    if not uri.startswith("mongodb+srv://"):
        return uri
        
    try:
        logger.info("🔄 Attempting manual SRV resolution for MongoDB...")
        
        # Parse URI parts manually (urllib.parse doesn't handle mongodb+srv scheme well sometimes)
        # Scheme: mongodb+srv://[username:password@]host[/[database]][?options]
        
        prefix = "mongodb+srv://"
        rest = uri[len(prefix):]
        
        if "@" in rest:
            auth_part, rest = rest.rsplit("@", 1)
        else:
            auth_part = None
            
        if "/" in rest:
            host_part, rest = rest.split("/", 1)
            if "?" in rest:
                db_name, params = rest.split("?", 1)
            else:
                db_name = rest
                params = ""
        else:
            host_part = rest
            if "?" in host_part:
                host_part, params = host_part.split("?", 1)
            else:
                params = ""
            db_name = ""

        # Configure Resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8']
        
        # Resolve SRV
        # Format: _mongodb._tcp.hostname
        srv_target = f"_mongodb._tcp.{host_part}"
        answers = resolver.resolve(srv_target, 'SRV')
        
        hosts = []
        for r in answers:
            target = r.target.to_text().rstrip('.')
            hosts.append(f"{target}:{r.port}")
            
        # Resolve TXT (Options like replicaSet)
        try:
            txt_answers = resolver.resolve(host_part, 'TXT')
            txt_options = {}
            for r in txt_answers:
                # TXT records are strings like 'authSource=admin&replicaSet=atlas-...'
                txt_str = b"".join(r.strings).decode("utf-8")
                for pair in txt_str.split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        txt_options[k] = v
        except Exception as e:
            logger.warning(f"TXT resolution failed (ignoring): {e}")
            txt_options = {}

        # Reconstruct standard URI
        # mongodb://[username:password@]host1,host2,host3/[database]?[options]
        
        new_hosts = ",".join(hosts)
        
        # Merge params
        # Existing params + TXT options
        # Note: We just append TXT options if not present?
        # Simple rebuild:
        
        base_uri = f"mongodb://"
        if auth_part:
            base_uri += f"{auth_part}@"
        
        base_uri += new_hosts
        if db_name:
            base_uri += f"/{db_name}"
        else:
            base_uri += "/"
            
        # Handle Query Params
        query_parts = []
        if params:
            query_parts.append(params)
        
        # Add TXT options + enforce SSL/tls
        # SRV implies ssl=true implicitly. Standard URI needs explicit.
        if "ssl" not in params and "tls" not in params:
             query_parts.append("ssl=true")
        
        for k, v in txt_options.items():
            if k not in params: # Simple check
                query_parts.append(f"{k}={v}")
        
        if query_parts:
            base_uri += "?" + "&".join(query_parts)
            
        logger.info(f"✅ Resolved to Standard URI: mongodb://... (Hosts: {len(hosts)})")
        return base_uri

    except Exception as e:
        logger.error(f"❌ Manual SRV resolution failed: {e}")
        return uri # Fallback

logger = logging.getLogger(__name__)

# ==============================================================================
# 📄 File: bot/services/db.py
# 📝 Description: Async MongoDB Service using Motor.
# 📝 الوصف: خدمة الاتصال بقاعدة بيانات مونجو بشكل غير متزامن.
# ==============================================================================

class Database:
    """
    Main Database Class (Singleton).
    🔹 كلاس إدارة قاعدة البيانات الرئيسي.
    """
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None

    async def connect(self):
        """
        Connect to MongoDB.
        🔹 إنشاء الاتصال بقاعدة البيانات.
        """
        uri = get_mongo_uri()
        # First encode credentials
        from urllib.parse import quote_plus
        uri = encode_mongo_credentials(uri)
        # Then resolve SRV
        uri = resolve_mongo_uri(uri)
        db_name = get_mongo_db_name() or "Vex_db"
        logger.info(f"Connecting to MongoDB (db={db_name})...")
        try:
            self.client = AsyncIOMotorClient(uri)
            self.db = self.client.get_default_database(db_name)
            logger.info("MongoDB connected successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    async def init_database(self):
        """
        Initialize database collections and indexes.
        🔹 تهيئة مجموعات قاعدة البيانات والفهارس.
        """
        try:
            # 1. Groups Collection Index (non-destructive)
            await self.db.groups.create_index("chat_id", unique=True)
            
            # 2. Users Collection Index
            await self.db.users.create_index("id", unique=True)
            
            # 3. Support Logs Index
            await self.db.support_logs.create_index("ticket_id", unique=True)
            
            logger.info("✅ Database initialized and indexes verified (non-destructive).")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")

def encode_mongo_credentials(uri: str) -> str:
    """
    Encode username and password in MongoDB URI according to RFC 3986.
    This fixes the "Username and password must be escaped" error.
    """
    from urllib.parse import quote_plus
    if not uri or "@" not in uri:
        return uri
    
    try:
        # Extract protocol (mongodb:// or mongodb+srv://)
        if uri.startswith("mongodb+srv://"):
            protocol = "mongodb+srv://"
        elif uri.startswith("mongodb://"):
            protocol = "mongodb://"
        else:
            return uri
        
        # Remove protocol
        rest = uri[len(protocol):]
        
        # Split credentials from host
        if "@" not in rest:
            return uri
        
        credentials, host_and_rest = rest.split("@", 1)
        
        # Split username and password
        if ":" in credentials:
            username, password = credentials.split(":", 1)
            # Encode both username and password
            encoded_username = quote_plus(username)
            encoded_password = quote_plus(password)
            encoded_credentials = f"{encoded_username}:{encoded_password}"
        else:
            # Only username, no password
            encoded_credentials = quote_plus(credentials)
        
        # Reconstruct URI
        return f"{protocol}{encoded_credentials}@{host_and_rest}"
    
    except Exception as e:
        logger.warning(f"Failed to encode credentials: {e}, using original URI")
        return uri




    async def add_or_update_user(self, user_data: dict):
        """
        Add a new user or update existing one.
        🔹 إضافة مستخدم جديد أو تحديث بياناته.
        """
        try:
            await self.db.users.update_one(
                {"id": user_data["id"]},
                {"$set": user_data},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False

    async def get_group_settings(self, chat_id: int) -> dict:
        """
        Get group settings. If not exists, return defaults.
        """
        try:
            settings = await self.db.groups.find_one({"chat_id": chat_id})
            if settings:
                return settings
            
            # Default Settings Structure
            default_settings = {
                "chat_id": chat_id,
                "is_active": False, # 🔴 Not active by default
                "language": "ar",  # Default Language
                "media": {
                    "photo": True,
                    "video": True,
                    "sticker": False,      # Default: Blocked
                    "voice": True,
                    "audio": False,        # Default: Blocked (Music)
                    "document": True,
                    "video_note": False,   # Default: Blocked (Round Video)
                    "animation": True,     # GIFs
                    "link": False,         # Default: Blocked
                    "forward": False,      # Default: Blocked
                    "text": True,
                    "game": True,
                    "location": True,
                    "contact": True,
                    "poll": True,
                    "venue": True,
                    "mention": True,
                    "hashtag": True,
                    "telegram_link": False,
                    "bot_invite": False,
                    "entry_msg": True,
                    "exit_msg": True
                },
                "banned_words": [],
                "banned_words_action": "delete", # delete, mute, none
                "mute_duration_minutes": 60, # Default mute duration
                "violation_threshold": 3, # Mute after 3 violations
                "whitelist": [], # User IDs or Links
                "welcome_message": {
                    "enabled": True,
                    "text": "مرحباً بك في المجموعة! 👋"
                },
                "silent": {
                    "is_locked": False,
                    "schedule": {
                        "active": False,
                        "open_time": "08:00",
                        "close_time": "23:00"
                    },
                    "timer": {
                        "active": False,
                        "end_time": None
                    },
                    "messages": {
                        "daily_open": "🔓 <b>تم فتح المجموعة حسب الجدول اليومي.</b>",
                        "daily_close": "🔒 <b>تم قفل المجموعة حسب الجدول اليومي. نراكم غداً!</b>",
                        "timer_lock": "⏱️ <b>تم قفل المجموعة مؤقتاً.</b>",
                        "manual_lock": "🔒 <b>تم قفل المجموعة من قبل المشرفين.</b>",
                        "manual_unlock": "🔓 <b>تم فتح المجموعة من قبل المشرفين.</b>" 
                    }
                },
                "rules": "",
                "rules_enabled": True
            }
            # Create default entry
            await self.db.groups.insert_one(default_settings)
            return default_settings
            
        except Exception as e:
            logger.error(f"Error getting group settings: {e}")
            return None

    async def update_group_settings(self, chat_id: int, updates: dict):
        """
        Update specific fields in group settings.
        Example updates: {"media_permissions.photo": False, "welcome_message.enabled": True}
        """
        try:
            await self.db.groups.update_one(
                {"chat_id": chat_id},
                {"$set": updates},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error updating group settings: {e}")
            return False

    async def get_active_groups(self) -> list:
        """
        Get all groups where is_active=True.
        """
        try:
            cursor = self.db.groups.find({"is_active": True})
            return await cursor.to_list(length=100) # Limit 100 for now
        except Exception as e:
            logger.error(f"Error getting active groups: {e}")
            return []

    async def log_support_message(self, ticket_id: int, user_id: int, original_msg_id: int):
        """
        Log a forwarded message ID to map it back to the user.
        🔹 حفظ معرف الرسالة المحولة لربطها بالمستخدم.
        
        Args:
            ticket_id (int): ID of the message inside the Support Group.
            user_id (int): The original user sending the DM.
            original_msg_id (int): The message ID in the user's private chat.
        """
        try:
            await self.db.support_logs.insert_one({
                "ticket_id": ticket_id,
                "user_id": user_id,
                "original_msg_id": original_msg_id
            })
            return True
        except Exception as e:
            logger.error(f"Error logging support message: {e}")
            return False

    async def get_ticket_user(self, ticket_id: int):
        """
        Get the User ID owner of a support ticket (Group Message ID).
        🔹 معرفة صاحب الرسالة من خلال معرف الرسالة في المجموعة.
        """
        doc = await self.db.support_logs.find_one({"ticket_id": ticket_id})
        return doc["user_id"] if doc else None

    async def log_admin_reply(self, admin_msg_id: int, user_id: int, user_msg_id: int, reply_text: str = None):
        """
        Log an admin reply to track it for deletion.
        🔹 حفظ رد المشرف لتتبعه وحذفه لاحقاً.
        
        Args:
            admin_msg_id: The ID of the admin's message in the group.
            user_id: The ID of the user who received the reply.
            user_msg_id: The ID of the message sent to the user (Bot -> User).
            reply_text: Content snippet for UI preview.
        """
        try:
            await self.db.reply_logs.insert_one({
                "admin_msg_id": admin_msg_id,
                "user_id": user_id,
                "user_msg_id": user_msg_id,
                "reply_text": reply_text,
                "created_at": get_current_timestamp() 
            })

            return True
        except Exception as e:
            logger.error(f"Error logging reply: {e}")
            return False

    async def get_reply_info(self, admin_msg_id: int):
        """
        Get info about an admin reply using its Group Message ID.
        🔹 الحصول على معلومات الرد باستخدام معرف رسالة المجموعة.
        """
        return await self.db.reply_logs.find_one({"admin_msg_id": admin_msg_id})

    async def get_recent_replies(self, limit: int = 5):
        """
        Get recent admin replies.
        🔹 الحصول على آخر الردود.
        """
        cursor = self.db.reply_logs.find().sort("_id", -1).limit(limit)
        return await cursor.to_list(length=limit)

    # --------------------------------------------------------------------------
    # Block & Appeal System
    # --------------------------------------------------------------------------
    async def block_user(self, user_id: int):
        """Block a user and reset appeal status."""
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"is_blocked": True, "appeal_status": "none"}},
            upsert=True
        )

    async def unblock_user(self, user_id: int):
        """Unblock a user."""
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"is_blocked": False, "appeal_status": "none"}},
            upsert=True
        )

    async def get_user_status(self, user_id: int):
        """Get block and appeal status."""
        doc = await self.db.users.find_one({"id": user_id}, {"is_blocked": 1, "appeal_status": 1})
        if doc:
            return {
                "is_blocked": doc.get("is_blocked", False),
                "appeal_status": doc.get("appeal_status", "none")
            }
        return {"is_blocked": False, "appeal_status": "none"}

    async def set_appeal_status(self, user_id: int, status: str):
        """Set appeal status: none, pending, rejected"""
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"appeal_status": status}},
            upsert=True
        )

    # --------------------------------------------------------------------------
    # 👮 Admin Management (Cloud)
    # --------------------------------------------------------------------------
    async def get_admins(self):
        """Get all admin IDs from MongoDB."""
        cursor = self.db.admins.find({})
        admins = await cursor.to_list(length=1000)
        return [admin["user_id"] for admin in admins]

    async def add_admin(self, user_id: int, username: str = "Unknown"):
        """Add a new admin."""
        await self.db.admins.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "username": username, "added_at": get_current_timestamp()}},
            upsert=True
        )

    async def remove_admin(self, user_id: int):
        """Remove an admin."""
        await self.db.admins.delete_one({"user_id": user_id})

    # -------------------------------------------------------------------------
    # ⚙️ GROUP SETTINGS MANAGEMENT (New)
    # -------------------------------------------------------------------------

    async def get_group_settings(self, chat_id: int) -> dict:
        """
        Get group settings. If not exists, return defaults.
        """
        try:
            settings = await self.db.groups.find_one({"chat_id": chat_id})
            if settings:
                return settings
            
            # Default Settings Structure
            default_settings = {
                "chat_id": chat_id,
                "title": None,
                "is_active": False, # 🔴 Not active by default
                "language": "ar",  # Default Language
                "media": {
                    "photo": True,
                    "video": True,
                    "sticker": False,      # Default: Blocked
                    "voice": True,
                    "audio": False,        # Default: Blocked (Music)
                    "document": True,
                    "video_note": False,   # Default: Blocked (Round Video)
                    "animation": True,     # GIFs
                    "link": False,         # Default: Blocked
                    "forward": False,      # Default: Blocked
                    "text": True,
                    "game": True,
                    "location": True,
                    "contact": True,
                    "poll": True,
                    "venue": True,
                    "mention": True,
                    "hashtag": True,
                    "telegram_link": False,
                    "bot_invite": False,
                    "entry_msg": True,
                    "exit_msg": True
                },
                "banned_words": [],
                "banned_words_action": "delete", # delete, mute, none
                "mute_duration_minutes": 60, # Default mute duration
                "violation_threshold": 3, # Mute after 3 violations
                "whitelist": [], # User IDs or Links
                "welcome_message": {
                    "enabled": True,
                    "text": "مرحباً بك في المجموعة! 👋"
                },
                "silent": {
                    "is_locked": False,
                    "schedule": {
                        "active": False,
                        "open_time": "08:00",
                        "close_time": "23:00"
                    },
                    "timer": {
                        "active": False,
                        "end_time": None
                    },
                    "messages": {
                        "daily_open": "🔓 <b>تم فتح المجموعة حسب الجدول اليومي.</b>",
                        "daily_close": "🔒 <b>تم قفل المجموعة حسب الجدول اليومي. نراكم غداً!</b>",
                        "timer_lock": "⏱️ <b>تم قفل المجموعة مؤقتاً.</b>",
                        "manual_lock": "🔒 <b>تم قفل المجموعة من قبل المشرفين.</b>",
                        "manual_unlock": "🔓 <b>تم فتح المجموعة من قبل المشرفين.</b>" 
                    }
                },
                "rules": "",
                "rules_enabled": True
            }
            # Create default entry
            await self.db.groups.insert_one(default_settings)
            return default_settings
            
        except Exception as e:
            logger.error(f"Error getting group settings: {e}")
            return None

    async def update_group_settings(self, chat_id: int, updates: dict):
        """
        Update specific fields in group settings.
        Example updates: {"media_permissions.photo": False, "welcome_message.enabled": True}
        """
        try:
            await self.db.groups.update_one(
                {"chat_id": chat_id},
                {"$set": updates},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error updating group settings: {e}")
            return False

    async def get_active_groups(self) -> list:
        """
        Get all groups where is_active=True.
        """
        try:
            cursor = self.db.groups.find({"is_active": True})
            return await cursor.to_list(length=100) # Limit 100 for now
        except Exception as e:
            logger.error(f"Error getting active groups: {e}")
            return []

# Singleton Instance | نسخة واحدة مشتركة
db = Database()

