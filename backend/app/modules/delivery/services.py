# app/modules/delivery/services.py
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from loguru import logger
from .repository import DeliveryRepository
from .models import (
    DeliveryInDB,
    DeliveryCreateInternal,
    TrackingEvent,
    ChatMessage,
    GeoPoint,
    SENDER_ROLES,
    DeliveryAPI,
    TrackingEventAPI,
    ChatMessageAPI,
    DeliveryLocationAPI,
)
from app.modules.sales.models import OrderInDB  # Need OrderInDB model
from app.core.counters import CounterService
from app.modules.people.repository import UserRepository
from app.modules.people.models import UserInDB
from app.modules.office.services_audit import AuditService
from app.websocket.connection_manager import manager as ws_manager  # For WebSocket notifications


# --- Utility Function ---
def generate_map_link(lat: float, lon: float) -> str:
    return f"https://maps.google.com/?q={lat},{lon}"


class DeliveryService:
    async def create_delivery_from_order(
        self,
        order: OrderInDB,
        delivery_repo: DeliveryRepository,
        counter_service: CounterService,
    ) -> DeliveryInDB:
        """
        Creates a delivery record from the given order.
        """
        log = logger.bind(order_id=str(order.id), service="DeliveryService")
        log.info("Creating delivery record from confirmed order...")

        # Check if delivery already exists for the order
        existing_delivery = await delivery_repo.get_by_order_id(order.id)
        if existing_delivery:
            log.warning(f"Delivery already exists for order {order.order_ref}.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Delivery already exists for order {order.order_ref}",
            )

        # Validate order shipping address
        if not order.shipping_address or not order.shipping_address.get("street"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is missing a valid shipping address",
            )

        # Generate delivery reference
        try:
            delivery_ref = await counter_service.generate_reference("DLV")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not generate delivery reference: {e}")

        # Prepare delivery data
        delivery_internal_data = DeliveryCreateInternal(
            delivery_ref=delivery_ref,
            order_id=order.id,
            customer_id=order.customer_id,
            delivery_address=order.shipping_address,
            current_status="pending",
            shipping_notes=getattr(order, "shipping_notes", None),
        )

        # Save delivery in the database
        try:
            created_delivery_db = await delivery_repo.create(delivery_internal_data)
            log.success(f"Delivery {delivery_ref} created successfully for order {order.order_ref}.")
            return created_delivery_db
        except Exception as e:
            log.error(f"Failed to create delivery in DB: {e}")
            raise HTTPException(status_code=500, detail=f"Could not save delivery record: {e}")

    async def add_chat_message_service(
        self,
        delivery_id_str: str,
        message_text: str,
        sender_role: SENDER_ROLES,
        sender_id: str,
        delivery_repo: DeliveryRepository,
        user_repo: UserRepository,
        audit_service: Optional[AuditService] = None,
        current_user: Optional[UserInDB] = None,
    ) -> ChatMessageAPI:
        """
        Adds a chat message to the delivery's chat history and broadcasts it via WebSocket.
        """
        log = logger.bind(delivery_id=delivery_id_str, sender_role=sender_role, sender_id=sender_id)
        log.info("Adding chat message...")

        delivery_id = delivery_repo._to_objectid(delivery_id_str)
        if not delivery_id:
            raise HTTPException(400, "Invalid Delivery ID")

        if not message_text.strip():
            raise HTTPException(400, "Message cannot be empty")

        chat_message = ChatMessage(
            sender_role=sender_role,
            sender_id=sender_id,
            message=message_text.strip(),
        )

        success = await delivery_repo.add_chat_message(delivery_id, chat_message)
        if not success:
            if not await delivery_repo.exists({"_id": delivery_id}):
                raise HTTPException(404, "Delivery not found")
            log.error("Failed to add chat message to repository.")
            raise HTTPException(500, "Failed to save chat message.")

        log.success("Chat message added to delivery.")

        # Enrich with sender name
        sender_name = sender_id
        if sender_role != "system":
            user = await user_repo.get_by_id(sender_id)
            if user and user.profile:
                sender_name = f"{user.profile.first_name or ''} {user.profile.last_name or ''}".strip() or user.email

        chat_api = ChatMessageAPI(
            message_id=chat_message.message_id,
            sender_role=chat_message.sender_role,
            sender_id=chat_message.sender_id,
            sender_display_name=sender_name,
            message=chat_message.message,
            timestamp=chat_message.timestamp,
        )

        # Emit WebSocket event
        ws_payload = {
            "type": "new_delivery_message",
            "payload": {
                "delivery_id": delivery_id_str,
                "chat_message": chat_api.model_dump(mode="json"),
            },
        }

        # Determine recipients (customer, driver)
        delivery = await delivery_repo.get_by_id(delivery_id)
        if delivery:
            recipients = {str(delivery.customer_id)}
            if delivery.assigned_driver_id:
                recipients.add(str(delivery.assigned_driver_id))

            for user_id_to_notify in recipients:
                try:
                    await ws_manager.send_personal_message(ws_payload, user_id_to_notify)
                    log.debug(f"Sent WebSocket notification to user {user_id_to_notify}")
                except Exception as ws_err:
                    log.error(f"Failed to send WebSocket message to user {user_id_to_notify}: {ws_err}")

        # Optionally log audit event
        if audit_service and current_user:
            await audit_service.log_audit_event(
                action="delivery_chat_message_sent",
                status="success",
                entity_type="Delivery",
                entity_id=delivery_id,
                details={"sender": sender_role, "preview": message_text[:50]},
                current_user=current_user,
            )

        return chat_api

    async def get_tracking_history(
        self,
        delivery_id_str: str,
        delivery_repo: DeliveryRepository,
    ) -> List[TrackingEventAPI]:
        """
        Retrieves the tracking history of a delivery.
        """
        delivery = await delivery_repo.get_by_id(delivery_id_str)
        if not delivery:
            raise HTTPException(404, "Delivery not found")
        return [TrackingEventAPI.model_validate(event) for event in delivery.tracking_history]

    async def get_last_location(
        self,
        delivery_id_str: str,
        delivery_repo: DeliveryRepository,
    ) -> DeliveryLocationAPI:
        """
        Retrieves the last known location of the delivery.
        """
        delivery = await delivery_repo.get_by_id(delivery_id_str)
        if not delivery:
            raise HTTPException(404, "Delivery not found")

        location_api = DeliveryLocationAPI(address_description=delivery.delivery_address.get("street", "N/A"))
        if delivery.last_known_location:
            location_api.latitude = delivery.last_known_location.latitude
            location_api.longitude = delivery.last_known_location.longitude
            location_api.map_link = generate_map_link(location_api.latitude, location_api.longitude)
            last_loc_event = next((e for e in delivery.tracking_history if e.location), None)
            location_api.last_update = last_loc_event.timestamp if last_loc_event else delivery.updated_at

        return location_api

    async def get_chat_history(
        self,
        delivery_id_str: str,
        delivery_repo: DeliveryRepository,
        user_repo: UserRepository,
    ) -> List[ChatMessageAPI]:
        """
        Retrieves the chat history of a delivery.
        """
        delivery = await delivery_repo.get_by_id(delivery_id_str)
        if not delivery:
            raise HTTPException(404, "Delivery not found")

        enriched_chat = []
        user_cache = {}

        for msg in delivery.chat_history:
            sender_name = msg.sender_id
            if msg.sender_role != "system" and msg.sender_id not in user_cache:
                user = await user_repo.get_by_id(msg.sender_id)
                user_cache[msg.sender_id] = user
                if user and user.profile:
                    sender_name = f"{user.profile.first_name or ''} {user.profile.last_name or ''}".strip() or user.email
            elif msg.sender_id in user_cache:
                user = user_cache[msg.sender_id]
                if user and user.profile:
                    sender_name = f"{user.profile.first_name or ''} {user.profile.last_name or ''}".strip() or user.email

            enriched_chat.append(
                ChatMessageAPI(
                    message_id=msg.message_id,
                    sender_role=msg.sender_role,
                    sender_id=msg.sender_id,
                    sender_display_name=sender_name,
                    message=msg.message,
                    timestamp=msg.timestamp,
                )
            )

        return enriched_chat

# Factory to get service instance
async def get_delivery_service() -> DeliveryService:
    return DeliveryService()