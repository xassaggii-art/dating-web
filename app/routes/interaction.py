from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.interaction import BasketItemDTO, LikeRequestDTO, LikeResponseDTO
from app.guards.auth_guard import CurrentActor, get_current_actor
from app.guards.limit_guard import enforce_like_limit
from app.infra.database import get_session
from app.services.match_service import MatchService

router = APIRouter(tags=["interactions"])


@router.post("/interactions/like", response_model=LikeResponseDTO)
async def like_user(
    dto: LikeRequestDTO,
    actor: CurrentActor = Depends(enforce_like_limit),
    session: AsyncSession = Depends(get_session),
) -> LikeResponseDTO:
    service = MatchService(session)
    return await service.create_like(actor, dto.receiver_id)
