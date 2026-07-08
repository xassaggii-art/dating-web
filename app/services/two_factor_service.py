from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import User
from app.infra.security import (
    decrypt_secret,
    encrypt_secret,
    generate_totp_secret,
    get_totp_provisioning_uri,
    verify_totp,
)
from app.services.audit_service import AuditService


class TwoFactorService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._audit = AuditService(db)

    async def setup(self, user_id: UUID) -> dict[str, str]:
        result = await self._db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.totp_enabled:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="2FA already enabled")

        secret = generate_totp_secret()
        user.totp_secret_encrypted = encrypt_secret(secret)
        await self._db.flush()

        email = user.email or user.phone or str(user.id)
        return {
            "secret": secret,
            "provisioning_uri": get_totp_provisioning_uri(secret, email),
        }

    async def enable(self, user_id: UUID, code: str) -> None:
        result = await self._db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None or user.totp_secret_encrypted is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Run setup first")

        secret = decrypt_secret(user.totp_secret_encrypted)
        if secret is None or not verify_totp(secret, code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")

        user.totp_enabled = True
        await self._audit.log("auth.2fa_enabled", user_id=user_id)
        await self._db.commit()

    async def disable(self, user_id: UUID, code: str) -> None:
        result = await self._db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None or not user.totp_enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA not enabled")

        secret = decrypt_secret(user.totp_secret_encrypted or "")
        if secret is None or not verify_totp(secret, code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")

        await self._db.execute(
            update(User)
            .where(User.id == user_id)
            .values(totp_enabled=False, totp_secret_encrypted=None)
        )
        await self._audit.log("auth.2fa_disabled", user_id=user_id)
        await self._db.commit()
