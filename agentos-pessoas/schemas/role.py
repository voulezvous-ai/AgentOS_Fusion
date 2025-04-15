from pydantic import BaseModel, Field
from typing import Optional

class RoleBase(BaseModel):
    name: str = Field(..., max_length=50, description="Nome da role")
    description: Optional[str] = Field(None, max_length=255)

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: str

    class Config:
        orm_mode = True