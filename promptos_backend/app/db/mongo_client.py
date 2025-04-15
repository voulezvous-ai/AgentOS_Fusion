from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from loguru import logger

_mongo_client: AsyncIOMotorClient | None = None
_mongo_db: AsyncIOMotorDatabase | None = None

async def connect_to_mongo():
    global _mongo_client, _mongo_db
    if _mongo_client and _mongo_db:
        logger.debug("MongoDB connection already established.")
        return
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
        _mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
        db_name = settings.MONGODB_URI.split('/')[-1].split('?')[0] or "promptos_db"
        _mongo_db = _mongo_client[db_name]
        await _mongo_client.admin.command('ping')
        logger.success(f"Connected to MongoDB database '{db_name}' successfully.")
    except Exception as e:
        logger.critical(f"FATAL: Failed to connect to MongoDB: {e}")
        _mongo_client = None
        _mongo_db = None
        raise

async def close_mongo_connection():
    global _mongo_client, _mongo_db
    if _mongo_client:
        logger.info("Closing MongoDB connection...")
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        logger.info("MongoDB connection closed.")

def get_database() -> AsyncIOMotorDatabase:
    if _mongo_db is None:
        logger.error("Database instance is not available.")
        raise RuntimeError("Database not connected")
    return _mongo_db