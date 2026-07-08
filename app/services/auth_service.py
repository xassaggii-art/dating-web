from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.contracts.auth import UserLoginDTO, UserRegisterDTO
from app.infra.database import Like, User
from app.infra.http import get_client_ip, get_user_agent
from app.infra.security import hash_password, verify_password
from app.infra.session import SessionService, get_guest_session
from app.services.audit_service import AuditService
from app.services.match_service import MatchService


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._match = MatchService(session)
        self._sessions = SessionService(session)
        self._audit = AuditService(session)

    async def register(
        self,
        dto: UserRegisterDTO,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, str, str]:
        settings = get_settings()
        now = datetime.now(UTC)

        if dto.email is not None:
            existing = await self._session.execute(select(User).where(User.email == dto.email))
            if existing.scalar_one_or_none() is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        if dto.phone is not None:
            existing = await self._session.execute(select(User).where(User.phone == dto.phone))
            if existing.scalar_one_or_none() is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")

        user = User(
            name=dto.name,
            birth_date=dto.birth_date,
            city=dto.city,
            email=dto.email,
            phone=dto.phone,
            password_hash=hash_password(dto.password),
            is_registered=True,
            accepted_terms_at=now,
            accepted_privacy_at=now,
            pd_consent_version=settings.pd_consent_version,
        )

        if dto.guest_session_id is not None:
            guest = await get_guest_session(dto.guest_session_id)
            if guest is not None:
                user.gender = str(guest["gender"])

        self._session.add(user)
        await self._session.flush()

        if dto.guest_session_id is not None:
            await self._merge_guest_likes(dto.guest_session_id, user.id)

        access, refresh, _ = await self._sessions.create_session(
            user.id, ip_address=ip_address, device_info=user_agent
        )
        await self._audit.log(
            "auth.register",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"pd_consent_version": settings.pd_consent_version},
        )
        await self._session.commit()
        await self._session.refresh(user)
        return user, access, refresh

    async def _merge_guest_likes(self, guest_id: UUID, user_id: UUID) -> None:
        await self._session.execute(
            update(Like)
            .where(Like.sender_id == guest_id)
            .values(sender_id=user_id, is_visible_to_receiver=True)
        )
        await self._session.flush()

        guest_likes = await self._session.execute(select(Like).where(Like.sender_id == user_id))
        for like in guest_likes.scalars().all():
            await self._match.try_create_mutual_match(like.sender_id, like.receiver_id)

    async def login(
        self,
        dto: UserLoginDTO,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, str, str, bool]:
        query = select(User)
        if "@" in dto.login:
            query = query.where(User.email == dto.login)
        else:
            query = query.where(User.phone == dto.login)

        result = await self._session.execute(query)
        user = result.scalar_one_or_none()
        if user is None or user.password_hash is None or not verify_password(dto.password, user.password_hash):
            await self._audit.log("auth.login_failed", ip_address=ip_address, user_agent=user_agent)
            await self._session.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access, refresh, _ = await self._sessions.create_session(
            user.id, ip_address=ip_address, device_info=user_agent
        )
        await self._audit.log("auth.login", user_id=user.id, ip_address=ip_address, user_agent=user_agent)
        await self._session.commit()
        await self._session.refresh(user)
        return user, access, refresh, user.totp_enabled

    async def refresh(
        self,
        refresh_token: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, str, str]:
        rotated = await self._sessions.rotate_session(
            refresh_token, ip_address=ip_address, device_info=user_agent
        )
        if rotated is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user_id, access, new_refresh, _ = rotated
        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        await self._audit.log("auth.refresh", user_id=user.id, ip_address=ip_address, user_agent=user_agent)
        await self._session.commit()
        return user, access, new_refresh

    async def logout(
        self,
        refresh_token: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        user_id: UUID | None = None,
    ) -> None:
        await self._sessions.revoke_by_refresh_token(refresh_token)
        await self._audit.log("auth.logout", user_id=user_id, ip_address=ip_address, user_agent=user_agent)
        await self._session.commit()
