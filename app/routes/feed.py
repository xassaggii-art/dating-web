from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.feed import FeedResponse
from app.guards.auth_guard import CurrentActor, get_current_actor
from app.infra.database import get_session
from app.services.feed_service import FeedService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/cards", response_model=FeedResponse)
async def feed_cards(
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> FeedResponse:
    service = FeedService(session)
    return await service.get_cards(actor, limit=limit, offset=offset)


@router.get("/reels", response_model=FeedResponse)
async def feed_reels(
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    exclude: str = Query(default="", description="Comma-separated user UUIDs from cards tab"),
    limit: int = Query(default=20, ge=1, le=50),
) -> FeedResponse:
    exclude_ids: list[UUID] = []
    if exclude.strip():
        exclude_ids = [UUID(x.strip()) for x in exclude.split(",") if x.strip()]

    service = FeedService(session)
    return await service.get_reels(actor, exclude_ids=exclude_ids or None, limit=limit)
