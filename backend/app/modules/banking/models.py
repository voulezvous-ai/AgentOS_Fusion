from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from bson import ObjectId
from decimal import Decimal

from app.models.api_common import PyObjectId

# --- Constants ---
TRANSACTION_TYPES = Literal[
    "sale_income",
    "shift_fee",
    "refund_outgoing",
    "bonus_income",
    "manual_adjustment",
    "correction",
    "payment_received",
    "commission_payout",
    "other_income",
    "other_expense"
]
TRANSACTION_STATUSES = Literal[
    "pending",
    "completed",
    "failed",
    "cancelled",
    "rolled_back",
    "pending_rollback"
]

# --- Internal/DB Models ---
class TransactionBase(BaseModel):
    transaction_ref: str = Field(..., unique=True)
    type: TRANSACTION_TYPES
    amount: Decimal
    currency: str = Field(default="BRL", max_length=3)
    description: str
    status: TRANSACTION_STATUSES
    associated_user_id: Optional[ObjectId] = None
    associated_order_id: Optional[ObjectId] = None
    associated_shift_id: Optional[ObjectId] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('amount')
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.00"):
            raise ValueError('Internal transaction amount must be positive.')
        return v.quantize(Decimal("0.01"))

class TransactionCreateInternal(TransactionBase):
    status: TRANSACTION_STATUSES = "completed"

class TransactionUpdateInternal(BaseModel):
    status: Optional[TRANSACTION_STATUSES] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    rollback_reason: Optional[str] = None

    model_config = ConfigDict(extra='ignore')

class TransactionInDB(TransactionBase):
    id: PyObjectId = Field(..., alias="_id")
    rollback_reason: Optional[str] = None
    rolled_back_by_trx_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda dt: dt.isoformat(), Decimal: str}
    )

# --- API Models ---
class TransactionAPI(BaseModel):
    id: str
    transaction_ref: str
    type: TRANSACTION_TYPES
    amount: str
    currency: str
    description: str
    status: TRANSACTION_STATUSES
    associated_user_id: Optional[str] = None
    associated_order_id: Optional[str] = None
    associated_shift_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    rollback_reason: Optional[str] = None
    rolled_back_by_trx_ref: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionCreateAPI(BaseModel):
    type: TRANSACTION_TYPES
    amount_str: str = Field(..., alias="amount", description="Positive value of transaction. Type determines direction.")
    currency: str = Field(default="BRL")
    description: str
    status: Optional[TRANSACTION_STATUSES] = "completed"
    associated_user_id: Optional[str] = None
    associated_order_id: Optional[str] = None
    associated_shift_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    _amount_decimal: Optional[Decimal] = None

    @field_validator('amount_str')
    @classmethod
    def validate_amount_str(cls, v: str) -> str:
        try:
            dec_val = Decimal(v).quantize(Decimal("0.01"))
            if dec_val <= Decimal("0.00"):
                raise ValueError("Amount must be a positive number string.")
            cls._amount_decimal = dec_val
            return v
        except InvalidOperation:
            raise ValueError("Invalid amount format. Use string like '123.45'.")

class RollbackPayloadAPI(BaseModel):
    reason: str = Field(..., min_length=10, description="Mandatory reason for rollback")