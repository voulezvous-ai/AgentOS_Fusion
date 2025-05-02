# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient
from redis.asyncio import Redis as AsyncRedis
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import patch

# Add app path to sys path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    mock_settings = {
        "PROJECT_NAME": "AgentOS Test",
        "API_V1_STR": "/api/v1",
        "LOG_LEVEL": "DEBUG",
        "MONGODB_URI": "mongodb://test:test@localhost:27017",
        "REDIS_URL": "redis://localhost:6379/1",
        "CELERY_BROKER_URL": "redis://localhost:6379/2",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/3",
        "SECRET_KEY": "test-secret-key",
        "ALGORITHM": "HS256",
    }
    with patch.dict(os.environ, mock_settings, clear=True):
        yield

@pytest.fixture(scope="session")
def mongo_container() -> Generator[MongoDbContainer, None, None]:
    with MongoDbContainer("mongo:latest") as mongo:
        yield mongo

@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    with RedisContainer("redis:latest") as redis:
        yield redis

@pytest_asyncio.fixture(scope="function")
async def db_client(mongo_container: MongoDbContainer) -> AsyncGenerator[AsyncMongoMockClient, None]:
    from motor.motor_asyncio import AsyncIOMotorClient
    url = mongo_container.get_connection_url()
    client = AsyncIOMotorClient(url)
    db_name = f"test_db_{os.urandom(4).hex()}"
    yield client[db_name]
    await client.drop_database(db_name)
    client.close()

@pytest_asyncio.fixture(scope="function")
async def redis_client(redis_container: RedisContainer) -> AsyncGenerator[AsyncRedis, None]:
    url = redis_container.get_connection_url()
    client = AsyncRedis.from_url(url, decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()

@pytest_asyncio.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client