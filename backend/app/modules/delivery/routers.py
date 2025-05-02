# app/modules/delivery/routers.py
from fastapi import APIRouter, Depends, HTTPException, status, Path, Request
from typing import List
from loguru import logger

from .services import DeliveryService, get_delivery_service
from .repository import DeliveryRepository, get_delivery_repository
from .models import (
    DeliveryAPI,
    TrackingEventAPI,
    ChatMessageAPI,
    DeliveryLocationAPI,
    DeliveryMessageCreateAPI,
    SENDER_ROLES,
)
from app.core.security import CurrentUser, UserInDB
from app.modules.people.repository import UserRepository, get_user_repository
from app.modules.office.services_audit import AuditService, get_audit_service

delivery_router = APIRouter()

# --- Helper ---
async def get_delivery_or_404(
    delivery_id: str = Path(..., description="Delivery ID (ObjectId)"),
    delivery_repo: DeliveryRepository = Depends(get_delivery_repository),
):
    delivery = await delivery_repo.get_by_id(delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found"
        )
    return delivery

# --- Helper Permission Check ---
def check_delivery_chat_permission(delivery: DeliveryAPI, user: UserInDB) -> bool:
    """
    Validates if the user has permission to interact with the delivery chat.
    """
    if not delivery or not user:
        return False
    is_customer = str(delivery.customer_id) == str(user.id)
    is_driver = delivery.assigned_driver_id and str(delivery.assigned_driver_id) == str(user.id)
    is_staff = any(role in user.roles for role in ["admin", "support", "sales_rep"])
    return is_customer or is_driver or is_staff

# --- Endpoints ---

@delivery_router.get(
    "/{delivery_id}/tracking",
    response_model=List[TrackingEventAPI],
    summary="Get delivery tracking history",
    tags=["Delivery"],
)
async def get_delivery_tracking_endpoint(
    delivery: DeliveryAPI = Depends(get_delivery_or_404),
    current_user: CurrentUser = Depends(),
    delivery_service: DeliveryService = Depends(get_delivery_service),
):
    """
    Retrieves the list of tracking events for a specific delivery.
    """
    if not check_delivery_chat_permission(delivery, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view tracking")
    return await delivery_service.get_tracking_history(
        str(delivery.id), delivery_repo=await get_delivery_repository()
    )

@delivery_router.get(
    "/{delivery_id}/maplink",
    response_model=DeliveryLocationAPI,
    summary="Get last known location and map link",
    tags=["Delivery"],
)
async def get_delivery_maplink_endpoint(
    delivery: DeliveryAPI = Depends(get_delivery_or_404),
    current_user: CurrentUser = Depends(),
    delivery_service: DeliveryService = Depends(get_delivery_service),
):
    """
    Retrieves the last known location coordinates and a Google Maps link.
    """
    if not check_delivery_chat_permission(delivery, current_user):
        raise HTTPException(
            status_code=403, detail="Not authorized to view location"
        )
    return await delivery_service.get_last_location(
        str(delivery.id), delivery_repo=await get_delivery_repository()
    )

@delivery_router.get(
    "/{delivery_id}/chat",
    response_model=List[ChatMessageAPI],
    summary="Get delivery chat history",
    tags=["Delivery"],
)
async def get_delivery_chat_endpoint(
    delivery: DeliveryAPI = Depends(get_delivery_or_404),
    current_user: CurrentUser = Depends(),
    delivery_service: DeliveryService = Depends(get_delivery_service),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Retrieves the chat message history for a specific delivery.
    """
    if not check_delivery_chat_permission(delivery, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view chat")
    return await delivery_service.get_chat_history(
        str(delivery.id),
        delivery_repo=await get_delivery_repository(),
        user_repo=user_repo,
    )

@delivery_router.post(
    "/{delivery_id}/message",
    response_model=ChatMessageAPI,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message in the delivery chat",
    tags=["Delivery"],
)
async def send_delivery_message_endpoint(
    payload: DeliveryMessageCreateAPI,
    delivery: DeliveryAPI = Depends(get_delivery_or_404),
    current_user: CurrentUser = Depends(),
    delivery_service: DeliveryService = Depends(get_delivery_service),
    delivery_repo: DeliveryRepository = Depends(get_delivery_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Sends a message associated with a delivery (customer or driver).
    """
    sender_role: SENDER_ROLES = None
    if str(delivery.customer_id) == str(current_user.id):
        sender_role = "customer"
    elif (
        delivery.assigned_driver_id
        and str(delivery.assigned_driver_id) == str(current_user.id)
    ):
        sender_role = "driver"
    elif any(role in current_user.roles for role in ["admin", "support"]):
        sender_role = "driver"

    if not sender_role:
        raise HTTPException(
            status_code=403,
            detail="User is not authorized to send messages for this delivery.",
        )

    return await delivery_service.add_chat_message_service(
        delivery_id_str=str(delivery.id),
        message_text=payload.message,
        sender_role=sender_role,
        sender_id=str(current_user.id),
        delivery_repo=delivery_repo,
        user_repo=user_repo,
        audit_service=audit_service,
        current_user=current_user,
    )