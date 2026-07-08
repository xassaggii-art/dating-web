from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LikeRequestDTO(BaseModel):
    receiver_id: UUID


class LikeResponseDTO(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    is_mutual: bool
    created_at: datetime
    chat_id: UUID | None = None


class BasketItemDTO(BaseModel):
    user_id: UUID
    name: str
    avatar_url: str | None
    is_mutual: bool
    liked_at: datetime
