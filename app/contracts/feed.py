from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class FeedCardDTO(BaseModel):
    user_id: UUID
    name: str
    age: int
    city: str | None
    description: str | None = None
    avatar_url: str | None
    video_profile_url: str | None
    attractiveness_score: float | None = None
    compatibility_percent: int | None = None


class FeedResponse(BaseModel):
    cards: list[FeedCardDTO]
    remaining_likes: int | None = None


class FeedFilterDTO(BaseModel):
    age_from: int = Field(default=18, ge=18)
    age_to: int = Field(default=99, le=99)
    city: str | None = None
