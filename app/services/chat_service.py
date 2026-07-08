from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.contracts.chat import ChatListItemDTO, ChatListResponse
from app.guards.auth_guard import CurrentActor
from app.infra.database import Chat, ChatStatus, User


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_chats(self, actor: CurrentActor) -> ChatListResponse:
        settings = get_settings()
        result = await self._session.execute(
            select(Chat, User)
            .join(
                User,
                or_(
                    (Chat.user_one_id == actor.id) & (User.id == Chat.user_two_id),
                    (Chat.user_two_id == actor.id) & (User.id == Chat.user_one_id),
                ),
            )
            .where(
                Chat.status == ChatStatus.ACTIVE,
                or_(Chat.user_one_id == actor.id, Chat.user_two_id == actor.id),
            )
            .order_by(Chat.updated_at.desc())
        )

        items: list[ChatListItemDTO] = []
        for chat, partner in result.all():
            is_user_one = chat.user_one_id == actor.id
            items.append(
                ChatListItemDTO(
                    id=chat.id,
                    partner_id=partner.id,
                    partner_name=partner.name or "Unknown",
                    partner_avatar=partner.avatar_url,
                    is_mutual=True,
                    updated_at=chat.updated_at,
                    my_circles=chat.circle_count_user_one if is_user_one else chat.circle_count_user_two,
                    their_circles=chat.circle_count_user_two if is_user_one else chat.circle_count_user_one,
                )
            )

        return ChatListResponse(chats=items, max_active=settings.max_active_chats)
