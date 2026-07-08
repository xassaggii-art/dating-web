from arq.connections import RedisSettings

from app.config import get_settings
from app.workers.video import process_video_profile

_settings = get_settings()


class WorkerSettings:
    functions = [process_video_profile]
    redis_settings = RedisSettings.from_dsn(_settings.redis_url)
