from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum

class ProfileType(str, Enum):
    CLIENTE = "cliente"
    VENDEDOR = "vendedor"
    REVENDEDOR = "revendedor"
    ESTAFETA = "estafeta"
    ADMIN = "admin"

class ProfileBase(BaseModel):
    email: EmailStr = Field(..., description="Email único do usuário")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    profile_type: ProfileType = Field(..., description="Tipo de perfil")
    is_active: bool = True

class ProfileCreate(ProfileBase):
    initial_roles: Optional[List[str]] = Field(None, description="Roles iniciais")

class ProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_type: Optional[ProfileType] = None
    is_active: Optional[bool] = None

class ProfileRead(ProfileBase):
    id: str = Field(..., description="ID do perfil")
    roles: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True