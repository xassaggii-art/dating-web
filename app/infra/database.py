import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class ChatStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class VideoProfileStatus(str, Enum):
    NONE = "none"
    PROCESSING = "processing"
    AI_REVIEW = "ai_review"
    ADMIN_REVIEW = "admin_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ModerationStatus(str, Enum):
    PENDING = "pending"
    AI_PASSED = "ai_passed"
    AI_FAILED = "ai_failed"
    ADMIN_APPROVED = "admin_approved"
    ADMIN_REJECTED = "admin_rejected"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PricingType(str, Enum):
    PACKAGE = "package"
    PER_MINUTE = "per_minute"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentKind(str, Enum):
    BALANCE_TOPUP = "balance_topup"
    VIDEO_DATE = "video_date"
    PACKAGE_PURCHASE = "package_purchase"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    birth_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    birth_place: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    balance: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    video_profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_profile_status: Mapped[VideoProfileStatus] = mapped_column(
        SAEnum(VideoProfileStatus, name="video_profile_status", native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        default=VideoProfileStatus.NONE,
        server_default=VideoProfileStatus.NONE.value,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    has_children: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)
    children_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attractiveness_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    overall_rating: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    compatibility_cache: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_terms_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_privacy_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pd_consent_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    totp_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    profile_frozen: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    received_likes: Mapped[list["Like"]] = relationship(
        "Like",
        foreign_keys="Like.receiver_id",
        back_populates="receiver",
    )
    interests: Mapped[list["Interest"]] = relationship(
        "Interest",
        secondary="user_interests",
        back_populates="users",
    )
    goals: Mapped[list["UserGoal"]] = relationship(
        "UserGoal",
        secondary="user_goal_links",
        back_populates="users",
    )


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_interests",
        back_populates="interests",
    )


class UserInterest(Base):
    __tablename__ = "user_interests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    interest_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class UserGoal(Base):
    __tablename__ = "user_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_goal_links",
        back_populates="goals",
    )


class UserGoalLink(Base):
    __tablename__ = "user_goal_links"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    goal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_goals.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("sender_id", "receiver_id", name="uq_like_sender_receiver"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    receiver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_mutual: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_visible_to_receiver: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    receiver: Mapped["User"] = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_likes",
    )


class Chat(Base):
    __tablename__ = "chats"
    __table_args__ = (UniqueConstraint("user_one_id", "user_two_id", name="uq_chat_users"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_one_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_two_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ChatStatus] = mapped_column(
        SAEnum(ChatStatus, name="chat_status", native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        default=ChatStatus.ACTIVE,
        server_default=ChatStatus.ACTIVE.value,
    )
    circle_count_user_one: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    circle_count_user_two: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ModerationQueue(Base):
    __tablename__ = "moderation_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ModerationStatus] = mapped_column(
        SAEnum(ModerationStatus, name="moderation_status", native_enum=True),
        default=ModerationStatus.PENDING,
        server_default=ModerationStatus.PENDING.value,
        index=True,
    )
    ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_flags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VideoDate(Base):
    __tablename__ = "video_dates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )
    initiator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_cost: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pricing_plan_slug: Mapped[str | None] = mapped_column(String(50), nullable=True)
    purchased_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_kopecks: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    recording_consent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    webrtc_room_id: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("video_date_id", "rater_id", name="uq_rating_per_date"),
        CheckConstraint("adequacy BETWEEN 1 AND 5", name="ck_rating_adequacy"),
        CheckConstraint("humor BETWEEN 1 AND 5", name="ck_rating_humor"),
        CheckConstraint("kindness BETWEEN 1 AND 5", name="ck_rating_kindness"),
        CheckConstraint("empathy BETWEEN 1 AND 5", name="ck_rating_empathy"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_date_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("video_dates.id", ondelete="CASCADE"), nullable=False
    )
    rater_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rated_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    adequacy: Mapped[int] = mapped_column(Integer, nullable=False)
    humor: Mapped[int] = mapped_column(Integer, nullable=False)
    kindness: Mapped[int] = mapped_column(Integer, nullable=False)
    empathy: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status", native_enum=True),
        default=SubscriptionStatus.ACTIVE,
        server_default=SubscriptionStatus.ACTIVE.value,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    device_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    trusted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class PricingPlan(Base):
    __tablename__ = "pricing_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    pricing_type: Mapped[PricingType] = mapped_column(
        SAEnum(PricingType, name="pricing_type", native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_kopecks: Mapped[int] = mapped_column(Integer, nullable=False)
    per_minute_rate_kopecks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    kind: Mapped[PaymentKind] = mapped_column(
        SAEnum(PaymentKind, name="payment_kind", native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    amount_kopecks: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status", native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    provider_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pricing_plan_slug: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


settings = get_settings()
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
