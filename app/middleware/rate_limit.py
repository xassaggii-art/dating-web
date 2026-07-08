from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.infra.redis import get_redis


async def check_rate_limit(request: Request, key: str, limit: int, window_seconds: int) -> None:
    redis = await get_redis()
    redis_key = f"ratelimit:{key}"
    count = await redis.incr(redis_key)
    if count == 1:
        await redis.expire(redis_key, window_seconds)
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )


async def rate_limit_login(request: Request) -> None:
    settings = get_settings()
    ip = request.client.host if request.client else "unknown"
    await check_rate_limit(request, f"login:{ip}", settings.rate_limit_login_per_minute, 60)


async def rate_limit_register(request: Request) -> None:
    settings = get_settings()
    ip = request.client.host if request.client else "unknown"
    await check_rate_limit(request, f"register:{ip}", settings.rate_limit_register_per_hour, 3600)
