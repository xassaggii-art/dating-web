from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.contracts.interaction import BasketItemDTO, LikeResponseDTO
from app.guards.auth_guard import CurrentActor
from app.guards.limit_guard import increment_like_counter
from app.infra.database import Chat, ChatStatus, Like, User


class MatchService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_like(self, actor: CurrentActor, receiver_id: UUID) -> LikeResponseDTO:
        if actor.id == receiver_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot like yourself")

        receiver = await self._session.execute(select(User).where(User.id == receiver_id))
        if receiver.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        existing = await self._session.execute(
            select(Like).where(Like.sender_id == actor.id, Like.receiver_id == receiver_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already liked")

        is_visible = actor.is_registered
        like = Like(
            sender_id=actor.id,
            receiver_id=receiver_id,
            is_visible_to_receiver=is_visible,
        )
        self._session.add(like)
        await self._session.flush()

        chat_id = await self.try_create_mutual_match(actor.id, receiver_id)
        await increment_like_counter(actor)
        await self._session.commit()
        await self._session.refresh(like)

        return LikeResponseDTO(
            id=like.id,
            sender_id=like.sender_id,
            receiver_id=like.receiver_id,
            is_mutual=like.is_mutual,
            created_at=like.created_at,
            chat_id=chat_id,
        )

    async def try_create_mutual_match(self, sender_id: UUID, receiver_id: UUID) -> UUID | None:
        reverse = await self._session.execute(
            select(Like).where(
                Like.sender_id == receiver_id,
                Like.receiver_id == sender_id,
                Like.is_visible_to_receiver.is_(True),
            )
        )
        reverse_like = reverse.scalar_one_or_none()
        if reverse_like is None:
            return None

        forward_like = await self._session.execute(
            select(Like).where(Like.sender_id == sender_id, Like.receiver_id == receiver_id)
        )
        forward_like_obj = forward_like.scalar_one_or_none()
        if forward_like_obj is None:
            return None

        forward_like_obj.is_mutual = True
        reverse_like.is_mutual = True
        await self._session.flush()

        return await self._create_chat(sender_id, receiver_id)

    async def _create_chat(self, user_a: UUID, user_b: UUID) -> UUID | None:
        settings = get_settings()
        for user_id in (user_a, user_b):
            count = await self._session.execute(
                select(func.count())
                .select_from(Chat)
                .where(
                    Chat.status == ChatStatus.ACTIVE,
                    or_(Chat.user_one_id == user_id, Chat.user_two_id == user_id),
                )
            )
            if count.scalar_one() >= settings.max_active_chats:
                return None

        existing = await self._session.execute(
            select(Chat).where(
                or_(
                    and_(Chat.user_one_id == user_a, Chat.user_two_id == user_b),
                    and_(Chat.user_one_id == user_b, Chat.user_two_id == user_a),
                )
            )
        )
        chat = existing.scalar_one_or_none()
        if chat is not None:
            return chat.id

        user_one, user_two = (user_a, user_b) if str(user_a) < str(user_b) else (user_b, user_a)
        chat = Chat(user_one_id=user_one, user_two_id=user_two, status=ChatStatus.ACTIVE)
        self._session.add(chat)
        await self._session.flush()
        return chat.id

    async def get_basket_sent(self, actor: CurrentActor) -> list[BasketItemDTO]:
        result = await self._session.execute(
            select(Like, User)
            .join(User, User.id == Like.receiver_id)
            .where(Like.sender_id == actor.id)
            .order_by(Like.created_at.desc())
        )
        return [
            BasketItemDTO(
                user_id=user.id,
                name=user.name or "Unknown",
                avatar_url=user.avatar_url,
                is_mutual=like.is_mutual,
                liked_at=like.created_at,
            )
            for like, user in result.all()
        ]

    async def get_basket_received(self, actor: CurrentActor) -> list[BasketItemDTO]:
        if not actor.is_registered:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration required to view received likes",
            )

        result = await self._session.execute(
            select(Like, User)
            .join(User, User.id == Like.sender_id, isouter=True)
            .where(
                Like.receiver_id == actor.id,
                Like.is_visible_to_receiver.is_(True),
            )
            .order_by(Like.created_at.desc())
        )

        items: list[BasketItemDTO] = []
        for like, user in result.all():
            if user is not None:
                name = user.name or "Unknown"
                avatar = user.avatar_url
                user_id = user.id
            else:
                name = "Unknown"
                avatar = None
                user_id = like.sender_id

            items.append(
                BasketItemDTO(
                    user_id=user_id,
                    name=name,
                    avatar_url=avatar,
                    is_mutual=like.is_mutual,
                    liked_at=like.created_at,
                )
            )
        return items

    async def get_mutual_count(self, actor: CurrentActor) -> int:
        if actor.is_guest:
            return 0

        result = await self._session.execute(
            select(func.count())
            .select_from(Like)
            .where(
                Like.receiver_id == actor.id,
                Like.is_mutual.is_(True),
                Like.is_visible_to_receiver.is_(True),
            )
        )
        return result.scalar_one()
