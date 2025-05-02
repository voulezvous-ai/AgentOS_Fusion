# app/modules/delivery/repository.py
from pymongo.results import UpdateResult
from bson import ObjectId
from datetime import datetime
from typing import Optional
from loguru import logger
from app.core.database import BaseRepository
from .models import DeliveryInDB, DeliveryCreateInternal, DeliveryUpdateInternal, TrackingEvent, ChatMessage, GeoPoint

class DeliveryRepository(BaseRepository[DeliveryInDB, DeliveryCreateInternal, DeliveryUpdateInternal]):
    # Create indexes for delivery collection
    async def create_indexes(self):
        await self.collection.create_index("delivery_ref", unique=True)
        await self.collection.create_index("order_id", unique=True)

    async def get_by_order_id(self, order_id: ObjectId) -> Optional[DeliveryInDB]:
        """Fetch delivery by order ID."""
        delivery = await self.collection.find_one({"order_id": order_id})
        return self.model.model_validate(delivery) if delivery else None

    async def add_tracking_event(
        self,
        delivery_id: ObjectId,
        event: TrackingEvent
    ) -> bool:
        """Adds a tracking event and potentially updates last_known_location."""
        log = logger.bind(delivery_id=str(delivery_id), event_status=event.status)
        log.debug("Adding tracking event...")
        try:
            event_dict = event.model_dump(mode="json", exclude_none=True)
            update_payload = {
                "$push": {
                    "tracking_history": {
                        "$each": [event_dict],
                        "$position": 0,
                        "$slice": 50  # Limit history size
                    }
                },
                "$set": {"updated_at": datetime.utcnow()}
            }

            # Update last_known_location IF the event has location data
            if event.location:
                update_payload["$set"]["last_known_location"] = event.location.model_dump()

            result: UpdateResult = await self.collection.update_one(
                {"_id": delivery_id},
                update_payload
            )
            success = result.modified_count > 0
            if success:
                log.info("Tracking event added successfully.")
            else:
                log.warning("Failed to add tracking event (delivery not found?).")
            return success
        except Exception as e:
            self._handle_db_exception(e, "add_tracking_event", delivery_id)
            return False

    async def add_chat_message(
        self,
        delivery_id: ObjectId,
        message: ChatMessage
    ) -> bool:
        """Adds a chat message to the delivery's chat history."""
        log = logger.bind(delivery_id=str(delivery_id), sender=message.sender_role)
        log.debug("Adding chat message...")
        try:
            message_dict = message.model_dump(mode="json", exclude_none=True)
            result: UpdateResult = await self.collection.update_one(
                {"_id": delivery_id},
                {
                    "$push": {
                        "chat_history": {
                            "$each": [message_dict],
                            # "$position": 0, # Add to end usually for chat
                            "$slice": -100  # Keep last 100 messages
                        }
                    },
                    "$set": {"updated_at": datetime.utcnow()}  # Also update main timestamp
                }
            )
            success = result.modified_count > 0
            if success:
                log.info("Chat message added successfully.")
            else:
                log.warning("Failed to add chat message (delivery not found?).")
            return success
        except Exception as e:
            self._handle_db_exception(e, "add_chat_message", delivery_id)
            return False

# Factory to get repository instance
async def get_delivery_repository() -> DeliveryRepository:
    return DeliveryRepository(collection_name="deliveries")