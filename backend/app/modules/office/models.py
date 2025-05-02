# app/modules/office/models.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from bson import ObjectId

# Assuming PyObjectId is defined centrally, e.g., in app/models/api_common.py
# If not, define it here or import from where it exists (e.g., people module)
try:
    from app.models.api_common import PyObjectId
except ImportError:
    class PyObjectId(ObjectId):
        @classmethod
        def __get_validators__(cls): yield cls.validate
        @classmethod
        def validate(cls, v, _: Any):
            if not ObjectId.is_valid(v): raise ValueError("Invalid ObjectId")
            return ObjectId(v)
        @classmethod
        def __get_pydantic_json_schema__(cls, field_schema): field_schema.update(type="string")


# --- Setting Models ---
class SettingBase(BaseModel):
    key: str = Field(..., alias="_id", description="Unique key for the setting")
    value: Any = Field(..., description="Value of the setting")
    description: Optional[str] = None
    is_sensitive: bool = Field(default=False, description="Whether the value should be hidden")

class SettingCreateInternal(BaseModel): # Used by Repo/Service
    key: str
    value: Any
    description: Optional[str] = None
    is_sensitive: bool = False

class SettingUpdateInternal(BaseModel): # Used by Repo/Service
    value: Optional[Any] = None
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None

class SettingInDB(SettingBase):
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        arbitrary_types_allowed=True, # Allow 'Any' for value
        json_encoders={ObjectId: str, datetime: lambda dt: dt.isoformat()}
    )

# --- Feature Flag Models ---
class FeatureFlagBase(BaseModel):
    key: str = Field(..., alias="_id", description="Unique key for the feature flag")
    is_enabled: bool = Field(...)
    description: Optional[str] = None

class FeatureFlagCreateInternal(BaseModel):
    key: str
    is_enabled: bool
    description: Optional[str] = None

class FeatureFlagUpdateInternal(BaseModel):
    is_enabled: Optional[bool] = None
    description: Optional[str] = None

class FeatureFlagInDB(FeatureFlagBase):
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={ObjectId: str, datetime: lambda dt: dt.isoformat()}
    )


# --- Audit Log Models ---
AUDIT_STATUSES = Literal["success", "failure"]

class AuditLogBase(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[PyObjectId] = Field(None, description="ID of user performing action")
    user_email: Optional[str] = Field(None, description="Email of user (denormalized)")
    action: str = Field(..., description="Identifier of the action performed (e.g., 'order_created')")
    status: AUDIT_STATUSES = Field(..., description="Outcome of the action")
    entity_type: Optional[str] = Field(None, description="Type of entity affected (e.g., 'Order', 'User')")
    entity_id: Optional[str] = Field(None, description="ID of the entity affected (can be ObjectId string or other ref)")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional context/data about the event")
    ip_address: Optional[str] = Field(None, description="IP address of the request origin")
    user_agent: Optional[str] = Field(None, description="User agent of the request origin")
    error_message: Optional[str] = Field(None, description="Error details if status is 'failure'")

class AuditLogCreateInternal(AuditLogBase):
    # Used by service to create log entries
    pass

class AuditLogInDB(AuditLogBase):
    id: PyObjectId = Field(..., alias="_id") # Internal DB ID

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda dt: dt.isoformat()}
    )


# --- API Models ---

# Settings API
class SettingAPI(BaseModel):
    key: str
    value: Any # Value might be masked by service/router if sensitive
    description: Optional[str] = None
    is_sensitive: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})

class SettingCreateAPI(BaseModel):
    key: str = Field(..., min_length=3, pattern=r"^[a-zA-Z0-9_.-]+$")
    value: Any
    description: Optional[str] = None
    is_sensitive: bool = False

class SettingUpdateAPI(BaseModel):
    value: Optional[Any] = None
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None

# Feature Flags API
class FeatureFlagAPI(BaseModel):
    key: str
    is_enabled: bool
    description: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})

class FeatureFlagCreateAPI(BaseModel):
    key: str = Field(..., min_length=3, pattern=r"^[a-zA-Z0-9_.-]+$")
    is_enabled: bool = True
    description: Optional[str] = None

class FeatureFlagUpdateAPI(BaseModel):
    is_enabled: Optional[bool] = None
    description: Optional[str] = None

# Audit Log API
class AuditLogAPI(BaseModel):
    id: str # Return ID as string
    timestamp: datetime
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    status: AUDIT_STATUSES
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None # Expose user agent? Maybe optional
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})
