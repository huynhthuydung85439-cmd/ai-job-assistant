from redis.asyncio import Redis

from app.core.config import get_settings


def create_redis_client() -> Redis:
    """Create a lazy Redis client without opening a connection immediately."""
    return Redis.from_url(get_settings().redis_url, decode_responses=True)

