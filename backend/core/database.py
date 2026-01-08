from motor.motor_asyncio import AsyncIOMotorClient
from backend.core.config import settings
from loguru import logger

class Database:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.MONGO_DB_NAME]
            logger.success("Connected to MongoDB Atlas")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")

    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB Connection Closed")

db = Database()
