from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from loguru import logger
from functools import lru_cache

class Settings(BaseSettings):
    MONGODB_URI: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    OPENAI_API_KEY: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    API_KEY: str
    META_APP_SECRET: str | None = None
    META_ACCESS_TOKEN: str | None = None
    META_PHONE_NUMBER_ID: str | None = None
    META_VERIFY_TOKEN: str | None = None
    REDIS_URL: str
    USE_ATLAS_VECTOR_SEARCH: bool = False
    ATLAS_VECTOR_INDEX_NAME: str = "embedding_index_cosine"
    ATLAS_VECTOR_NUM_CANDIDATES: int = 50
    ATLAS_VECTOR_LIMIT: int = 3
    STORE_AGENT_EMBEDDINGS: bool = False
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(Path.cwd() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

@lru_cache()
def get_settings() -> Settings:
    logger.info("Carregando configurações da aplicação...")
    return Settings()

settings = get_settings()