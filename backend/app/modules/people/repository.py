# app/modules/people/repository.py
from bson import ObjectId
from datetime import datetime
from typing import Optional
from pymongo.results import UpdateResult
from loguru import logger
from app.core.database import BaseRepository
from .models import UserInDB, UserCreateInternal, UserUpdateInternal

class UserRepository(BaseRepository[UserInDB, UserCreateInternal, UserUpdateInternal]):
    async def update_balance(self, user_id: ObjectId, amount: float) -> bool:
        """Updates the balance for a specific user."""
        log = logger.bind(user_id=str(user_id))
        log.debug(f"Attempting to update balance by {amount}...")
        try:
            result: UpdateResult = await self.collection.update_one(
                {"_id": user_id},
                {
                    "$inc": {"profile.balance": amount},
                    "$set": {"updated_at": datetime.utcnow()},
                }
            )
            success = result.modified_count > 0
            if success:
                log.info("Balance updated successfully.")
            else:
                log.warning("Balance update failed. User not found?")
            return success
        except Exception as e:
            log.exception("Exception while updating balance.")
            return False

# Factory to get repository instance
async def get_user_repository() -> UserRepository:
    return UserRepository(collection_name="users")