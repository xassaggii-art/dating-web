from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class ChatListItemDTO(BaseModel):
    id: UUID
    partner_id: UUID
    partner_name: str
    partner_avatar: str | None
    is_mutual: bool
    updated_at: datetime
    my_circles: int
    their_circles: int


class ChatListResponse(BaseModel):
    chats: list[ChatListItemDTO]
    max_active: int
