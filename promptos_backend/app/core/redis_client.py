import redis.asyncio as redis
from app.core.config import settings

_redis_pool = None

def get_redis_client() -> redis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=getattr(settings, "REDIS_MAX_CONNECTIONS", 20),
        )
    return _redis_pool

async def connect_redis():
    client = get_redis_client()
    try:
        await client.ping()
    except Exception as e:
        raise RuntimeError("Erro ao conectar ao Redis.") from e

async def close_redis():
    client = get_redis_client()
    await client.aclose()
