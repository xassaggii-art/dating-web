import asyncio
import subprocess
import tempfile
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.infra.database import User, VideoProfileStatus
from app.infra.storage import build_object_key, delete_object, download_object, upload_object


async def process_video_profile(ctx: dict, user_id: str, raw_key: str) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        user = await session.get(User, UUID(user_id))
        if user is None:
            return

        try:
            raw_bytes = await asyncio.to_thread(download_object, raw_key)
            video_url, avatar_url = await asyncio.to_thread(
            _transcode_and_extract, raw_bytes, UUID(user_id)
        )
            user.video_profile_url = video_url
            user.avatar_url = avatar_url
            user.video_profile_status = VideoProfileStatus.APPROVED
        except Exception:
            user.video_profile_status = VideoProfileStatus.REJECTED
            await session.commit()
            raise
        else:
            await session.commit()
        finally:
            try:
                await asyncio.to_thread(delete_object, raw_key)
            except Exception:
                pass
        await engine.dispose()


def _transcode_and_extract(raw_bytes: bytes, user_id: UUID) -> tuple[str, str]:
    settings = get_settings()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw_file = tmp_path / "input.webm"
        mp4_file = tmp_path / "output.mp4"
        jpg_file = tmp_path / "avatar.jpg"

        raw_file.write_bytes(raw_bytes)

        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(raw_file),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                str(mp4_file),
            ],
            check=True,
            capture_output=True,
        )

        extract_at = settings.video_avatar_extract_sec
        subprocess.run(
            [
                "ffmpeg", "-y", "-ss", str(extract_at), "-i", str(mp4_file),
                "-vframes", "1", "-q:v", "2", str(jpg_file),
            ],
            check=True,
            capture_output=True,
        )

        video_key = build_object_key(user_id, "video", "mp4")
        avatar_key = build_object_key(user_id, "avatar", "jpg")

        video_url = upload_object(video_key, mp4_file.read_bytes(), "video/mp4")
        avatar_url = upload_object(avatar_key, jpg_file.read_bytes(), "image/jpeg")
        return video_url, avatar_url
