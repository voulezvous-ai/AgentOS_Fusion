from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from loguru import logger
from typing import Optional, List

JWT_SECRET = "your-very-secret-key"  # Deve vir de um settings seguro
ALGORITHM = "HS256"

class TokenData(BaseModel):
    username: Optional[str] = None
    roles: List[str] = []

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Erro na validação do JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(request: Request) -> dict:
    user = getattr(request.state, "user", {"id": "guest", "roles": ["guest"]})
    if user["id"] == "guest":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    return user

def require_role(required_roles: List[str]):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_roles = set(current_user.get("roles", []))
        if not set(required_roles).intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer uma das roles: {', '.join(required_roles)}"
            )
    return role_checker