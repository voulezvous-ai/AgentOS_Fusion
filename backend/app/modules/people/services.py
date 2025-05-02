# app/modules/people/services.py
from decimal import Decimal
from loguru import logger
from typing import Optional
from fastapi import HTTPException, status
from .repository import UserRepository
from .models import UserInDB, UserProfileAPI, UserProfileUpdateAPI

class UserService:
    async def get_user_profile_api(self, user_db: UserInDB) -> UserProfileAPI:
        """Converts UserInDB profile to UserProfileAPI."""
        return UserProfileAPI.model_validate(user_db.profile.model_dump(exclude={"balance"}))

    async def adjust_customer_balance(
        self,
        user_id: ObjectId,
        amount_change_decimal: Decimal,
        reason: str,
        actor: Optional[UserInDB],
        user_repo: UserRepository,
    ):
        """Adjusts customer balance using the repository method."""
        log = logger.bind(user_id=str(user_id), change=str(amount_change_decimal), reason=reason)
        log.info("Adjusting customer balance...")
        success = await user_repo.update_balance(user_id, float(amount_change_decimal))
        if not success:
            log.error("Failed to update customer balance.")
            raise HTTPException(status_code=500, detail="Failed to update customer balance.")
        log.success("Customer balance adjusted successfully.")

# Factory to get service instance
async def get_user_service() -> UserService:
    return UserService()