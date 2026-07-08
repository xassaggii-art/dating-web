import re
from datetime import date
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.infra.database import User, VideoProfileStatus
from app.contracts.profile import ProfileUpdateDTO
from app.infra.storage import build_object_key, create_presigned_upload, public_url


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_profile(self, user_id: UUID) -> User:
        user = await self._session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def get_video_questions(self) -> dict:
        settings = get_settings()
        return {
            "max_duration_sec": settings.video_max_duration_sec,
            "question_interval_sec": settings.video_question_interval_sec,
            "questions": settings.video_questions,
        }

    async def update_profile(self, user_id: UUID, dto: ProfileUpdateDTO) -> User:
        user = await self.get_profile(user_id)
        updates = dto.model_dump(exclude_unset=True)
        if not updates:
            return user
        for field, value in updates.items():
            setattr(user, field, value)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def create_avatar_upload_url(self, user_id: UUID, content_type: str) -> tuple[str, str]:
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image content allowed")
        ext = "jpg" if "jpeg" in content_type else "png" if "png" in content_type else "webp"
        key = build_object_key(user_id, "avatar", ext)
        url = create_presigned_upload(key, content_type)
        return url, key

    async def confirm_avatar(self, user_id: UUID, object_key: str) -> User:
        if not re.match(rf"^users/{user_id}/avatar/", object_key):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid object key")
        user = await self.get_profile(user_id)
        user.avatar_url = public_url(object_key)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def create_upload_url(self, user_id: UUID, content_type: str) -> tuple[str, str]:
        if not content_type.startswith("video/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only video content allowed")

        ext = "webm" if "webm" in content_type else "mp4"
        key = build_object_key(user_id, "raw", ext)
        url = create_presigned_upload(key, content_type)
        return url, key

    async def confirm_upload(self, user_id: UUID, object_key: str) -> None:
        if not re.match(rf"^users/{user_id}/raw/", object_key):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid object key")

        user = await self._session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user.video_profile_status == VideoProfileStatus.PROCESSING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Video already processing")

        user.video_profile_status = VideoProfileStatus.PROCESSING
        await self._session.commit()

        settings = get_settings()
        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        try:
            await redis.enqueue_job("process_video_profile", str(user_id), object_key)
        finally:
            await redis.aclose()

    async def set_profile_frozen(self, user_id: UUID, frozen: bool) -> User:
        user = await self.get_profile(user_id)
        user.profile_frozen = frozen
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def soft_delete_profile(self, user_id: UUID) -> None:
        user = await self.get_profile(user_id)
        user.deleted_at = datetime.now(UTC)
        user.is_registered = False
        user.profile_frozen = True
        await self._session.commit()

    @staticmethod
    def truncate_description(text: str | None, limit: int = 40) -> str | None:
        if not text:
            return None
        text = text.strip()
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"

    @staticmethod
    def map_video_status(status: VideoProfileStatus) -> str:
        mapping = {
            VideoProfileStatus.NONE: "none",
            VideoProfileStatus.PROCESSING: "processing",
            VideoProfileStatus.APPROVED: "ready",
            VideoProfileStatus.REJECTED: "failed",
        }
        return mapping.get(status, "none")

    @staticmethod
    def calc_age(birth_date: date | None) -> int | None:
        if birth_date is None:
            return None
        today = date.today()
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
