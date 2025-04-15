
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.core.config import settings
from app.db.schemas import UserInDB
from app.core.security import get_password_hash
from loguru import logger

class UserService:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]

    async def get_user_by_username(self, username: str) -> UserInDB | None:
        data = await self.db["users"].find_one({"username": username})
        if data:
            return UserInDB(**data)
        return None

    async def get_user_by_id(self, user_id: str) -> UserInDB | None:
        if not ObjectId.is_valid(user_id):
            return None
        data = await self.db["users"].find_one({"_id": ObjectId(user_id)})
        if data:
            return UserInDB(**data)
        return None

    async def create_user(self, user: UserInDB):
        try:
            user_dict = user.dict()
            user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
            await self.db["users"].insert_one(user_dict)
        except DuplicateKeyError:
            logger.warning("Usuário já existe.")
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
