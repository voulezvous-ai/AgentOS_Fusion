# app/modules/scheduling/models.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime, date, time
from bson import ObjectId
from decimal import Decimal

SHIFT_STATUSES = Literal["pending_assignment", "assigned", "in_progress", "completed", "cancelled"]
ASSIGNMENT_STATUS = Literal["pending", "confirmed", "rejected"]

class UserAssignment(BaseModel):
    user_id: ObjectId
    assigned_at: datetime = Field(default_factory=datetime.utcnow)

class ShiftBase(BaseModel):
    shift_date: date = Field(...)
    start_time: time = Field(...)
    end_time: time = Field(...)
    required_role: Optional[str] = Field(None, description="Role required for this shift")
    max_participants: int = Field(default=1, gt=0, description="Maximum number of users for this shift")
    required_balance: Decimal = Field(default=Decimal("0.00"), description="Minimum balance required to be assigned")

    @Field.validate("end_time")
    @classmethod
    def validate_end_time(cls, v: time, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("End time must be after start time")
        return v

class ShiftCreateInternal(ShiftBase):
    status: SHIFT_STATUSES = "pending_assignment"
    notes: Optional[str] = None
    assigned_users: List[UserAssignment] = Field(default_factory=list)

class ShiftUpdateInternal(BaseModel):
    status: Optional[SHIFT_STATUSES] = None
    notes: Optional[str] = None
    model_config = ConfigDict(extra="ignore")

class ShiftInDB(ShiftBase):
    id: ObjectId = Field(..., alias="_id")
    status: SHIFT_STATUSES
    notes: Optional[str] = None
    assigned_users: List[UserAssignment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda dt: dt.isoformat(), Decimal: str}
    )

class AssignedUserAPI(BaseModel):
    user_id: str
    user_name: Optional[str] = None

class ShiftAPI(BaseModel):
    id: str
    shift_date: date
    start_time: time
    end_time: time
    required_role: Optional[str] = None
    max_participants: int
    required_balance: str
    status: SHIFT_STATUSES
    notes: Optional[str] = None
    assigned_users: List[AssignedUserAPI] = Field(default_factory=list)
    assigned_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat() if dt else None}
    )

class AutoAssignShiftCreateAPI(BaseModel):
    shift_date: date
    start_time: time
    end_time: time
    required_role: Optional[str] = None
    max_participants: int = Field(default=1, gt=0)
    required_balance: str = Field(default="0.00", description="Minimum balance as string")
    notes: Optional[str] = None

    @Field.validate("required_balance")
    @classmethod
    def validate_balance(cls, v: str):
        try:
            balance = Decimal(v).quantize(Decimal("0.01"))
            if balance < Decimal("0.00"):
                raise ValueError("Balance cannot be negative")
            return v
        except:
            raise ValueError("Invalid format for required_balance")

    @Field.validate("end_time")
    @classmethod
    def validate_end_time(cls, v: time, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("End time must be after start time")
        return v

class AutoAssignResponseAPI(BaseModel):
    message: str
    shift: ShiftAPI
    assigned_count: int
    unfilled_slots: int