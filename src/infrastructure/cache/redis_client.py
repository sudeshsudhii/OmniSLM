"""
OmniSLM Redis Client.

Provides async Redis connection management and common operations.
"""

from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis

from src.config.settings import get_settings

settings = get_settings()

redis_client: aioredis.Redis = aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
    max_connections=50,
)


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency for Redis client."""
    return redis_client


async def check_redis_health() -> bool:
    """Check if Redis is reachable."""
    try:
        return await redis_client.ping()
    except Exception:
        return False


class CacheService:
    """Simple cache abstraction over Redis."""

    def __init__(self, client: aioredis.Redis):
        self._client = client

    async def get(self, key: str) -> str | None:
        """Get a cached value by key."""
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        """Set a cached value with TTL in seconds."""
        await self._client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        """Delete a cached value."""
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return bool(await self._client.exists(key))

    async def incr(self, key: str) -> int:
        """Increment a counter and return new value."""
        return await self._client.incr(key)

    async def expire(self, key: str, ttl: int) -> None:
        """Set expiry on an existing key."""
        await self._client.expire(key, ttl)
