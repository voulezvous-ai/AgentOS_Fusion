# app/modules/people/routers.py
from fastapi import APIRouter, Depends, HTTPException, Path, Body, status
from bson import ObjectId
from app.core.security import CurrentUser
from .services import UserService, get_user_service
from .repository import UserRepository, get_user_repository
from .models import UserProfileAPI, AdjustBalancePayloadAPI

users_router = APIRouter()

@users_router.post(
    "/{user_id}/balance/adjust",
    status_code=status.HTTP_200_OK,
    summary="Adjust a user's balance",
    tags=["Users & People - Admin"]
)
async def adjust_customer_balance(
    user_id: str = Path(..., description="ID of the user whose balance is being adjusted"),
    payload: AdjustBalancePayloadAPI = Body(...),
    current_user: CurrentUser = Depends(),
    user_service: UserService = Depends(get_user_service),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Adjust a user's balance by a given amount."""
    try:
        user_id_obj = ObjectId(user_id)
        amount_decimal = Decimal(payload.amount)
        await user_service.adjust_customer_balance(
            user_id=user_id_obj,
            amount_change_decimal=amount_decimal,
            reason=payload.reason,
            actor=current_user,
            user_repo=user_repo,
        )
        return {"message": "Balance adjusted successfully."}
    except Exception as e:
        logger.exception("Error adjusting balance.")
        raise HTTPException(status_code=500, detail=str(e))