from uuid import UUID

from pydantic import BaseModel, Field


class VideoQuestionsResponse(BaseModel):
    max_duration_sec: int
    question_interval_sec: int
    questions: list[str]


class VideoUploadUrlRequest(BaseModel):
    content_type: str = Field(default="video/webm", pattern=r"^video/")


class VideoUploadUrlResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in: int = 3600


class VideoConfirmRequest(BaseModel):
    object_key: str = Field(min_length=10, max_length=512)


class VideoStatusResponse(BaseModel):
    status: str
    video_profile_url: str | None = None
    avatar_url: str | None = None


class ProfileResponse(BaseModel):
    id: UUID
    name: str | None
    birth_date: str | None
    city: str | None
    gender: str | None
    avatar_url: str | None
    video_profile_url: str | None
    video_status: str
    description: str | None = None
    occupation: str | None = None
    balance_kopecks: int = 0
    balance_rubles: float = 0
    profile_frozen: bool = False
    attractiveness_score: float | None = None
    overall_rating: float | None = None


class ProfileUpdateDTO(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=40)
    occupation: str | None = Field(default=None, max_length=100)


class AvatarUploadUrlRequest(BaseModel):
    content_type: str = Field(default="image/jpeg", pattern=r"^image/")


class AvatarConfirmRequest(BaseModel):
    object_key: str = Field(min_length=10, max_length=512)
