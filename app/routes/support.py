from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.support import ReportProfileDTO, SupportFaqResponse, SupportMessageDTO
from app.guards.auth_guard import CurrentActor, get_current_actor
from app.infra.database import get_session
from app.services.support_service import SupportService, load_faq

router = APIRouter(prefix="/support", tags=["support"])


@router.get("/faq", response_model=SupportFaqResponse)
async def get_faq() -> SupportFaqResponse:
    return load_faq()


@router.post("/messages", status_code=status.HTTP_204_NO_CONTENT)
async def send_support_message(
    dto: SupportMessageDTO,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await SupportService(session).submit_message(actor, dto)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/report", status_code=status.HTTP_204_NO_CONTENT)
async def report_profile(
    dto: ReportProfileDTO,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await SupportService(session).report_profile(actor, UUID(dto.reported_user_id), dto.reason)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
