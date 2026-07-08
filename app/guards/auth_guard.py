from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import User, get_session
from app.infra.security import decode_access_token, verify_totp, decrypt_secret
from app.infra.session import SessionService, get_guest_session
from app.services.audit_service import AuditService

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentActor:
    id: UUID
    is_guest: bool
    is_registered: bool
    session_id: UUID | None = None
    gender: str | None = None
    age: int | None = None
    name: str | None = None
    totp_enabled: bool = False
    session_trusted: bool = False


async def get_current_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_guest_uuid: UUID | None = Header(default=None, alias="X-Guest-UUID"),
    session: AsyncSession = Depends(get_session),
) -> CurrentActor:
    if credentials is not None:
        decoded = decode_access_token(credentials.credentials)
        if decoded is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        user_id, session_id = decoded
        session_service = SessionService(session)
        user_session = await session_service.get_active_session(session_id)
        if user_session is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked or expired")

        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        trusted = (
            user_session.trusted_until is not None and user_session.trusted_until > datetime.now(UTC)
        )
        return CurrentActor(
            id=user.id,
            is_guest=False,
            is_registered=user.is_registered,
            session_id=session_id,
            gender=user.gender,
            name=user.name,
            totp_enabled=user.totp_enabled,
            session_trusted=trusted,
        )

    if x_guest_uuid is not None:
        guest = await get_guest_session(x_guest_uuid)
        if guest is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid guest session")

        return CurrentActor(
            id=x_guest_uuid,
            is_guest=True,
            is_registered=False,
            gender=str(guest["gender"]),
            age=int(guest["age"]),
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authorization required: Bearer token or X-Guest-UUID",
    )


async def require_registered(actor: CurrentActor = Depends(get_current_actor)) -> CurrentActor:
    if actor.is_guest or not actor.is_registered:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration required")
    return actor


async def require_2fa(
    actor: CurrentActor = Depends(get_current_actor),
    x_2fa_code: str | None = Header(default=None, alias="X-2FA-Code"),
    session: AsyncSession = Depends(get_session),
) -> CurrentActor:
    if actor.is_guest or not actor.totp_enabled:
        return actor

    if actor.session_trusted:
        return actor

    if x_2fa_code is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA code required (X-2FA-Code header)",
        )

    result = await session.execute(select(User).where(User.id == actor.id))
    user = result.scalar_one_or_none()
    if user is None or user.totp_secret_encrypted is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="2FA not configured")

    secret = decrypt_secret(user.totp_secret_encrypted)
    if secret is None or not verify_totp(secret, x_2fa_code):
        audit = AuditService(session)
        await audit.log("auth.2fa_failed", user_id=actor.id)
        await session.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid 2FA code")

    if actor.session_id is not None:
        await SessionService(session).mark_trusted(actor.session_id)
        await session.commit()

    return actor
