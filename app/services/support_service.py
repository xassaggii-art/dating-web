import json
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.support import FaqItemDTO, SupportFaqResponse, SupportMessageDTO
from app.guards.auth_guard import CurrentActor
from app.services.audit_service import AuditService

SUPPORT_PATH = Path(__file__).resolve().parents[2] / "design" / "support.json"


@lru_cache
def load_faq() -> SupportFaqResponse:
    data = json.loads(SUPPORT_PATH.read_text(encoding="utf-8"))
    return SupportFaqResponse(items=[FaqItemDTO(**item) for item in data["faq"]])


class SupportService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def submit_message(self, actor: CurrentActor, dto: SupportMessageDTO) -> None:
        audit = AuditService(self._session)
        await audit.log(
            "support.message",
            user_id=None if actor.is_guest else actor.id,
            metadata={"email": dto.email, "preview": dto.message[:120]},
        )
        await self._session.commit()

    async def report_profile(self, actor: CurrentActor, reported_user_id: UUID, reason: str) -> None:
        if actor.id == reported_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot report yourself")

        audit = AuditService(self._session)
        await audit.log(
            "profile.report",
            user_id=None if actor.is_guest else actor.id,
            metadata={"reported_user_id": str(reported_user_id), "reason": reason[:200]},
        )
        await self._session.commit()
