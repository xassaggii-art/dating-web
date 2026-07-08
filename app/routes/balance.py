from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.balance import BalanceResponse, TopUpPreviewRequest, TopUpPreviewResponse
from app.guards.auth_guard import CurrentActor, require_registered
from app.infra.database import get_session
from app.services.balance_service import BalanceService

router = APIRouter(prefix="/balance", tags=["balance"])


@router.get("/me", response_model=BalanceResponse)
async def get_my_balance(
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> BalanceResponse:
    return await BalanceService(session).get_balance(actor.id)


@router.post("/topup", response_model=TopUpPreviewResponse)
async def topup_balance(
    dto: TopUpPreviewRequest,
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> TopUpPreviewResponse:
    return await BalanceService(session).topup_preview(actor.id, dto)
