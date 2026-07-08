import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.infra.database import UserSession
from app.infra.redis import get_redis
from app.infra.security import (
    create_access_token,
    generate_refresh_token,
    hash_token,
)

GUEST_PREFIX = "guest:"


class SessionService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_session(
        self,
        user_id: UUID,
        *,
        ip_address: str | None = None,
        device_info: str | None = None,
        trust_device: bool = False,
    ) -> tuple[str, str, UUID]:
        settings = get_settings()
        refresh_raw = generate_refresh_token()
        session = UserSession(
            user_id=user_id,
            refresh_token_hash=hash_token(refresh_raw),
            ip_address=ip_address,
            device_info=device_info,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
            trusted_until=(
                datetime.now(UTC) + timedelta(days=settings.trusted_device_days) if trust_device else None
            ),
        )
        self._db.add(session)
        await self._db.flush()
        access = create_access_token(user_id, session.id)
        return access, refresh_raw, session.id

    async def rotate_session(
        self,
        refresh_token: str,
        *,
        ip_address: str | None = None,
        device_info: str | None = None,
    ) -> tuple[UUID, str, str, UUID] | None:
        token_hash = hash_token(refresh_token)
        result = await self._db.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.now(UTC),
            )
        )
        old_session = result.scalar_one_or_none()
        if old_session is None:
            return None

        old_session.revoked_at = datetime.now(UTC)
        await self._db.flush()

        access, new_refresh, session_id = await self.create_session(
            old_session.user_id,
            ip_address=ip_address or old_session.ip_address,
            device_info=device_info or old_session.device_info,
            trust_device=old_session.trusted_until is not None
            and old_session.trusted_until > datetime.now(UTC),
        )
        return old_session.user_id, access, new_refresh, session_id

    async def revoke_by_refresh_token(self, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        await self._db.execute(
            update(UserSession)
            .where(UserSession.refresh_token_hash == token_hash, UserSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )

    async def get_active_session(self, session_id: UUID) -> UserSession | None:
        result = await self._db.execute(
            select(UserSession).where(
                UserSession.id == session_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()

    async def mark_trusted(self, session_id: UUID) -> None:
        settings = get_settings()
        await self._db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(trusted_until=datetime.now(UTC) + timedelta(days=settings.trusted_device_days))
        )


async def store_guest_session(guest_id: UUID, gender: str, age: int) -> None:
    settings = get_settings()
    redis = await get_redis()
    ttl = settings.guest_session_ttl_days * 86400
    payload = json.dumps({"gender": gender, "age": age})
    await redis.set(f"{GUEST_PREFIX}{guest_id}", payload, ex=ttl)


async def get_guest_session(guest_id: UUID) -> dict[str, str | int] | None:
    redis = await get_redis()
    raw = await redis.get(f"{GUEST_PREFIX}{guest_id}")
    if raw is None:
        return None
    data = json.loads(raw)
    return {"gender": data["gender"], "age": int(data["age"])}
