from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from backend.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect(self):
        if not settings.MONGO_URI:
            logger.warning("⚠️ MONGO_URI not found. Database features will be disabled.")
            return

        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.MONGO_DB_NAME]
            # Test connection
            await self.db.command("ping")
            logger.success("✅ Connected to MongoDB Atlas")
        except Exception as e:
            logger.error(f"❌ Database Connection Failed: {e}")
            self.client = None
            self.db = None

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("Database connection closed.")

db = Database()