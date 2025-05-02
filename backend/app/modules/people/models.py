# app/modules/people/models.py
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from bson import ObjectId
from decimal import Decimal

# --- Constants ---
USER_ROLES = Literal["admin", "driver", "customer", "reseller", "support", "manager", "system"]

# --- Internal/DB Models ---
class UserProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    document: Optional[str] = Field(None, description="CPF/CNPJ or other document")
    address: Optional[Dict[str, Any]] = Field(None, description="Standard address object")
    photo_url: Optional[str] = Field(None, description="URL for user's profile picture")
    tags: List[str] = Field(default_factory=list, description="General purpose tags")
    balance: Decimal = Field(default=Decimal("0.00"), description="Customer balance. Negative means debt.")

    model_config = ConfigDict(arbitrary_types_allowed=True)

class UserCreateInternal(BaseModel):
    email: EmailStr
    hashed_password: str
    profile: UserProfile = Field(default_factory=UserProfile)
    roles: List[USER_ROLES] = ["customer"]
    is_active: bool = True

class UserUpdateInternal(BaseModel):
    email: Optional[EmailStr] = None
    hashed_password: Optional[str] = None
    profile: Optional[UserProfile] = None
    roles: Optional[List[USER_ROLES]] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="ignore")

class UserInDB(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    email: EmailStr
    hashed_password: str
    profile: UserProfile = Field(default_factory=UserProfile)
    roles: List[USER_ROLES] = Field(default=["customer"])
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda dt: dt.isoformat(), Decimal: str}
    )

# --- API Models ---
class UserProfileAPI(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    document: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    photo_url: Optional[str] = None
    tags: List[str] = []

class UserAPI(BaseModel):
    id: str
    email: EmailStr
    profile: UserProfileAPI
    roles: List[USER_ROLES]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserCreateAdminAPI(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    profile: Optional[UserProfileAPI] = None
    roles: List[USER_ROLES] = ["customer"]
    is_active: bool = True

class UserProfileUpdateAPI(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1)
    last_name: Optional[str] = Field(None, min_length=1)
    phone: Optional[str] = None
    document: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    photo_url: Optional[str] = None
    tags: Optional[List[str]] = None

class UserAdminUpdateAPI(BaseModel):
    roles: Optional[List[USER_ROLES]] = None
    is_active: Optional[bool] = None

class AdjustBalancePayloadAPI(BaseModel):
    amount: str = Field(..., description="Amount to adjust as string (e.g., '10.50' or '-5.00')")
    reason: str = Field(..., min_length=5, description="Mandatory reason for the adjustment")
    order_ref: Optional[str] = Field(None, description="Optional linked order reference")