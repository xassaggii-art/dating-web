from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.interaction import BasketItemDTO
from app.guards.auth_guard import CurrentActor, get_current_actor
from app.infra.database import get_session
from app.services.match_service import MatchService

router = APIRouter(tags=["basket"])


@router.get("/basket/sent", response_model=list[BasketItemDTO])
async def basket_sent(
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> list[BasketItemDTO]:
    service = MatchService(session)
    return await service.get_basket_sent(actor)


@router.get("/basket/received", response_model=list[BasketItemDTO])
async def basket_received(
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> list[BasketItemDTO]:
    service = MatchService(session)
    return await service.get_basket_received(actor)


@router.get("/basket/mutual-count")
async def basket_mutual_count(
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    service = MatchService(session)
    count = await service.get_mutual_count(actor)
    return {"count": count}
