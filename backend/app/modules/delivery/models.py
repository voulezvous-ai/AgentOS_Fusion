# app/modules/delivery/models.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from bson import ObjectId

from app.models.api_common import PyObjectId  # Assuming central PyObjectId

# --- Constants ---
DELIVERY_STATUSES = Literal["pending", "assigned", "in_transit", "out_for_delivery", "delivered", "failed", "returned", "cancelled"]
SENDER_ROLES = Literal["customer", "driver", "system"]  # Roles for chat

# --- Sub-Schemas ---
class GeoPoint(BaseModel):
    latitude: float
    longitude: float

class TrackingEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str  # Could be DELIVERY_STATUSES or more granular tracking points
    location: Optional[GeoPoint] = None
    location_note: Optional[str] = Field(None, description="Textual description of location/event")
    notes: Optional[str] = None
    author: Optional[str] = Field(None, description="Who triggered the event (e.g., driver_id, system, customer_action)")  # Optional author field

class ChatMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: f"msg_{ObjectId()}")  # Internal unique ID for chat message
    sender_role: SENDER_ROLES
    sender_id: str  # Could be user_id (customer/driver) or 'system'
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Internal/DB Models ---
class DeliveryBase(BaseModel):
    delivery_ref: str = Field(..., unique=True)
    order_id: ObjectId = Field(..., unique=True)
    customer_id: ObjectId
    delivery_address: Dict[str, Any]  # From order
    current_status: DELIVERY_STATUSES
    assigned_driver_id: Optional[ObjectId] = None
    estimated_delivery_date: Optional[datetime] = None
    shipping_notes: Optional[str] = None  # From order

class DeliveryCreateInternal(DeliveryBase):
    # Initial tracking event is added here
    tracking_history: List[TrackingEvent] = Field(default_factory=lambda: [TrackingEvent(status="pending", location_note="Delivery created")])
    # Initial chat history is empty
    chat_history: List[ChatMessage] = Field(default_factory=list)
    last_known_location: Optional[GeoPoint] = None  # Initial location

class DeliveryUpdateInternal(BaseModel):
    # Fields that can be updated via PATCH etc.
    current_status: Optional[DELIVERY_STATUSES] = None
    assigned_driver_id: Optional[ObjectId] = None
    actual_delivery_date: Optional[datetime] = None
    delivery_notes: Optional[str] = None
    last_known_location: Optional[GeoPoint] = None

    model_config = ConfigDict(extra="ignore")

class DeliveryInDB(DeliveryBase):
    id: PyObjectId = Field(..., alias="_id")
    actual_delivery_date: Optional[datetime] = None
    delivery_notes: Optional[str] = None
    tracking_history: List[TrackingEvent] = Field(default_factory=list)
    chat_history: List[ChatMessage] = Field(default_factory=list)  # <<< Added Chat History
    last_known_location: Optional[GeoPoint] = None  # <<< Added Last Location
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda dt: dt.isoformat()},
    )

# --- API Models ---

class TrackingEventAPI(BaseModel):
    timestamp: datetime
    status: str
    location_note: Optional[str] = None
    notes: Optional[str] = None
    author: Optional[str] = None
    # Optionally expose lat/lon or map link here if needed directly in history list

class DeliveryLocationAPI(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address_description: Optional[str] = None  # e.g., from delivery_address initially
    last_update: Optional[datetime] = None
    map_link: Optional[str] = None

class ChatMessageAPI(BaseModel):
    message_id: str
    sender_role: SENDER_ROLES
    sender_id: str  # Consider masking internal IDs if needed
    sender_display_name: Optional[str] = None  # Enriched name
    message: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class DeliveryMessageCreateAPI(BaseModel):
    message: str = Field(..., min_length=1)
    # sender_role is determined by the endpoint/user calling it

# Add DeliveryAPI if not present or needs updating
class DeliveryAPI(BaseModel):
    id: str
    delivery_ref: str
    order_id: str
    customer_id: str
    delivery_address: Dict[str, Any]
    current_status: DELIVERY_STATUSES
    assigned_driver_id: Optional[str] = None
    driver_details: Optional[Dict[str, Any]] = None  # Enriched
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    last_known_location: Optional[DeliveryLocationAPI] = None  # <<< Use API location model
    # tracking_history: List[TrackingEventAPI] = [] # Optionally expose full history here
    # chat_history: List[ChatMessageAPI] = [] # Optionally expose full chat here
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat() if dt else None},
    )