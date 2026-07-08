from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status

from app.config import get_settings
from app.guards.auth_guard import CurrentActor, get_current_actor
from app.infra.redis import get_redis


def _daily_key(user_id: str) -> str:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"likes:daily:{user_id}:{today}"


def _guest_key(guest_id: str) -> str:
    return f"likes:guest:{guest_id}"


async def enforce_like_limit(actor: CurrentActor = Depends(get_current_actor)) -> CurrentActor:
    settings = get_settings()
    redis = await get_redis()

    if actor.is_guest:
        count = int(await redis.get(_guest_key(str(actor.id))) or 0)
        if count >= settings.guest_like_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Guest like limit reached. Please register to continue.",
            )
        return actor

    if not actor.is_registered:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration required to like profiles.",
        )

    count = int(await redis.get(_daily_key(str(actor.id))) or 0)
    if count >= settings.user_daily_like_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Daily like limit reached. Try again tomorrow.",
        )
    return actor


async def increment_like_counter(actor: CurrentActor) -> None:
    settings = get_settings()
    redis = await get_redis()

    if actor.is_guest:
        key = _guest_key(str(actor.id))
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, settings.guest_session_ttl_days * 86400)
        await pipe.execute()
        return

    key = _daily_key(str(actor.id))
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 86400)
    await pipe.execute()
