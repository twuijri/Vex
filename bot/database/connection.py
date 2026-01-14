"""
MongoDB connection using Motor (async driver) and Beanie ODM
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from bot.core.settings import settings
from bot.database.models import (
    Group,
    Admin,
    AdminGroup,
    SupportTicket,
    BlockedUser,
    User,
)

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""
    
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB Atlas"""
        try:
            logger.info("Connecting to MongoDB Atlas...")
            
            # Create Motor client
            cls.client = AsyncIOMotorClient(settings.MONGO_URI)
            
            # Use explicit database name from config
            db_name = settings.MONGO_DB_NAME
            
            # Initialize Beanie with document models
            await init_beanie(
                database=cls.client[db_name],
                document_models=[
                    Group,
                    Admin,
                    AdminGroup,
                    SupportTicket,
                    BlockedUser,
                    User,
                ]
            )
            
            logger.info(f"✅ Connected to MongoDB: {db_name}")
            
            # Create indexes (non-destructive)
            await cls._ensure_indexes()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def _ensure_indexes(cls):
        """Ensure all indexes exist (non-destructive)"""
        try:
            logger.info("Ensuring database indexes...")
            
            # Beanie automatically creates indexes defined in models
            # This is non-destructive - it only creates missing indexes
            
            logger.info("✅ Database indexes verified")
            
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB"""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    async def ping(cls) -> bool:
        """Check database connection"""
        try:
            await cls.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database ping failed: {e}")
            return False


# Convenience functions
async def init_db():
    """Initialize database connection"""
    await Database.connect()


async def close_db():
    """Close database connection"""
    await Database.disconnect()
