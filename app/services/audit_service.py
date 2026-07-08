from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def log(
        self,
        action: str,
        *,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_=metadata,
        )
        self._db.add(entry)
