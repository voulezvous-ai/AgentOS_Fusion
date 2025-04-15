from pydantic import BaseModel
from typing import Optional

class APIResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None