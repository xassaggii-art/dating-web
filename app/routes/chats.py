from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.chat import ChatListResponse
from app.guards.auth_guard import CurrentActor, get_current_actor
from app.infra.database import get_session
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=ChatListResponse)
async def list_chats(
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> ChatListResponse:
    if actor.is_guest or not actor.is_registered:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration required")
    service = ChatService(session)
    return await service.list_chats(actor)
