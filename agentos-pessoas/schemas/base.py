from pydantic import BaseModel, Field

class MsgDetail(BaseModel):
    msg: str = Field(..., description="Mensagem descritiva.")

class Settings(BaseModel):
    APP_NAME: str = "AgentOS Pessoas"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"