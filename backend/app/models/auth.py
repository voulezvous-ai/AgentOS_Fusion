# agentos_core/app/models/auth.py

from pydantic import BaseModel, Field, ConfigDict # Importar ConfigDict  
from typing import Optional

class Token(BaseModel):  
    """Schema da resposta do token de acesso JWT."""  
    access_token: str = Field(..., description="O token JWT de acesso.")  
    token_type: str = Field(default="bearer", description="Tipo do token (sempre 'bearer').")  
    # Opcional: Incluir refresh_token se implementado  
    # refresh_token: Optional[str] = Field(None, description="O token JWT de refresh.")

    # Adicionar exemplo para OpenAPI  
    model_config = ConfigDict(  
        json_schema_extra={  
            "example": {  
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcxNDE4MjYyNn0.abcdef...",  
                "token_type": "bearer"  
            }  
        }  
    )

class TokenPayload(BaseModel):  
    """  
    Schema para os dados essenciais decodificados do payload do JWT.  
    Usado internamente pela segurança, não exposto diretamente na API.  
    """  
    # 'sub' (subject) é o claim padrão para o identificador do usuário (nosso username/email)  
    sub: Optional[str] = Field(None, description="Subject (username/email) do token.")  
    # Adicionar outros claims se forem incluídos no token (ex: roles, user_id)  
    # exp: Optional[int] = None # Padrão JWT, validado pela lib jose  
    # iat: Optional[int] = None # Padrão JWT  
    # user_id: Optional[str] = None  
    # roles: Optional[List[str]] = []
