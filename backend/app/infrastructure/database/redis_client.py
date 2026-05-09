"""Async Redis client for caching session data and results."""
import json
from typing import Any, Optional
import redis.asyncio as redis
from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_redis_pool: Optional[redis.ConnectionPool] = None


def get_redis_pool() -> redis.ConnectionPool:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            str(settings.REDIS_URL),
            max_connections=20,
            decode_responses=True,
        )
    return _redis_pool


def get_redis_client() -> redis.Redis:
    return redis.Redis(connection_pool=get_redis_pool())


async def cache_set(key: str, value: Any, ttl: int = None) -> None:
    client = get_redis_client()
    ttl = ttl or settings.REDIS_TTL_SECONDS
    serialized = json.dumps(value, default=str)
    await client.setex(key, ttl, serialized)
    logger.debug("cache_set", key=key, ttl=ttl)


async def cache_get(key: str) -> Optional[Any]:
    client = get_redis_client()
    value = await client.get(key)
    if value is None:
        return None
    return json.loads(value)


async def cache_delete(key: str) -> None:
    client = get_redis_client()
    await client.delete(key)


async def cache_exists(key: str) -> bool:
    client = get_redis_client()
    return bool(await client.exists(key))


async def check_redis_connection() -> bool:
    try:
        client = get_redis_client()
        await client.ping()
        return True
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        return False
