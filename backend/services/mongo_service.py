# backend/services/mongo_service.py
# Logic to query groups stats etc.

from backend.database.local_db import get_system_config
from motor.motor_asyncio import AsyncIOMotorClient
import dns.resolver
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = None
db = None

def resolve_mongo_uri(uri: str) -> str:
    """
    Manually resolve mongodb+srv:// URI to mongodb:// using Google DNS.
    Workaround for Docker/PyMongo SRV resolution timeouts.
    """
    if not uri.startswith("mongodb+srv://"):
        return uri
        
    try:
        logger.info("🔄 (Backend) Attempting manual SRV resolution for MongoDB...")
        
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
        srv_target = f"_mongodb._tcp.{host_part}"
        answers = resolver.resolve(srv_target, 'SRV')
        
        hosts = []
        for r in answers:
            target = r.target.to_text().rstrip('.')
            hosts.append(f"{target}:{r.port}")
            
        # Resolve TXT
        try:
            txt_answers = resolver.resolve(host_part, 'TXT')
            txt_options = {}
            for r in txt_answers:
                txt_str = b"".join(r.strings).decode("utf-8")
                for pair in txt_str.split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        txt_options[k] = v
        except Exception as e:
            logger.warning(f"TXT resolution failed (ignoring): {e}")
            txt_options = {}

        # Reconstruct standard URI
        new_hosts = ",".join(hosts)
        
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
        
        if "ssl" not in params and "tls" not in params:
             query_parts.append("ssl=true")
        
        for k, v in txt_options.items():
            if k not in params:
                query_parts.append(f"{k}={v}")
        
        if query_parts:
            base_uri += "?" + "&".join(query_parts)
            
        logger.info(f"✅ (Backend) Resolved to Standard URI: mongodb://... (Hosts: {len(hosts)})")
        return base_uri

    except Exception as e:
        logger.error(f"❌ (Backend) Manual SRV resolution failed: {e}")
        return uri # Fallback

async def connect_mongo():
    global client, db
    config = get_system_config()
    if config.mongo_uri:
        try:
            resolved_uri = resolve_mongo_uri(config.mongo_uri)
            client = AsyncIOMotorClient(resolved_uri)
            db_name = config.mongo_db_name or "Vex_db"
            db = client.get_default_database(db_name)
            # Trigger connection check
            await db.command("ismaster")
            print(f"✅ Backend Connected to Mongo: {db.name}")
        except Exception as e:
            print(f"❌ Backend Failed to Connect to Mongo: {e}")
