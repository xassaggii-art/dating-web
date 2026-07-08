from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "VideoDating API"
    debug: bool = False
    api_prefix: str = "/v1"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/videodating"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    guest_session_ttl_days: int = 30

    encryption_key: str = "change-me-32-byte-key-for-totp!!"

    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    rate_limit_login_per_minute: int = 5
    rate_limit_register_per_hour: int = 3

    pd_consent_version: str = "1.0"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minio"
    s3_secret_key: str = "minio123"
    s3_bucket: str = "videodating"
    s3_region: str = "us-east-1"

    guest_like_limit: int = 5
    user_daily_like_limit: int = 30
    max_active_chats: int = 5

    video_max_duration_sec: int = 60
    video_question_interval_sec: int = 15
    video_avatar_extract_sec: float = 2.0

    s3_public_base_url: str = "http://localhost:9000/videodating"

    @property
    def video_questions(self) -> list[str]:
        return [
            "Как тебя зовут?",
            "Сколько тебе лет?",
            "Расскажи о себе",
            "Чем ты занимаешься?",
            "Какие у тебя увлечения?",
        ]

    trusted_device_days: int = 30

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str, info) -> str:
        env = info.data.get("environment", "development")
        if env == "production" and (len(value) < 32 or value == "change-me-in-production"):
            raise ValueError("JWT_SECRET must be at least 32 random characters in production")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
