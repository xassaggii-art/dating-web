"""profile, moderation, ratings, subscriptions

Revision ID: 002
Revises: 001
Create Date: 2026-07-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    video_profile_status = postgresql.ENUM(
        "none",
        "processing",
        "ai_review",
        "admin_review",
        "approved",
        "rejected",
        name="video_profile_status",
        create_type=False,
    )
    moderation_status = postgresql.ENUM(
        "pending",
        "ai_passed",
        "ai_failed",
        "admin_approved",
        "admin_rejected",
        name="moderation_status",
        create_type=False,
    )
    subscription_status = postgresql.ENUM(
        "active",
        "expired",
        "cancelled",
        name="subscription_status",
        create_type=False,
    )

    for enum_type in (video_profile_status, moderation_status, subscription_status):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column("video_profile_status", video_profile_status, server_default="none", nullable=False),
    )
    op.add_column("users", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("occupation", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("has_children", sa.Boolean(), nullable=True))
    op.add_column("users", sa.Column("children_count", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("attractiveness_score", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("overall_rating", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("compatibility_cache", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("is_online", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("users", sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_city", "users", ["city"])
    op.create_index("ix_users_gender", "users", ["gender"])
    op.create_index("ix_users_has_children", "users", ["has_children"])
    op.create_index("ix_users_attractiveness_score", "users", ["attractiveness_score"])
    op.create_index("ix_users_overall_rating", "users", ["overall_rating"])
    op.create_index("ix_users_video_profile_status", "users", ["video_profile_status"])

    op.add_column("likes", sa.Column("is_visible_to_receiver", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("chats", sa.Column("circle_count_user_one", sa.Integer(), server_default="0", nullable=False))
    op.add_column("chats", sa.Column("circle_count_user_two", sa.Integer(), server_default="0", nullable=False))

    op.create_table(
        "interests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(50), unique=True, nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
    )
    op.create_index("ix_interests_slug", "interests", ["slug"])

    op.create_table(
        "user_interests",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("interest_id", sa.Integer(), sa.ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_user_interests_interest_id", "user_interests", ["interest_id"])

    op.create_table(
        "user_goals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(50), unique=True, nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
    )

    op.create_table(
        "user_goal_links",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("goal_id", sa.Integer(), sa.ForeignKey("user_goals.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_user_goal_links_goal_id", "user_goal_links", ["goal_id"])

    op.create_table(
        "moderation_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_s3_key", sa.Text(), nullable=False),
        sa.Column("status", moderation_status, server_default="pending", nullable=False),
        sa.Column("ai_score", sa.Float(), nullable=True),
        sa.Column("ai_flags", postgresql.JSONB(), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_moderation_queue_status", "moderation_queue", ["status"])
    op.create_index("ix_moderation_queue_user_id", "moderation_queue", ["user_id"])

    op.create_table(
        "video_dates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False),
        sa.Column("initiator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_cost", sa.Integer(), server_default="0", nullable=False),
        sa.Column("recording_consent", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("webrtc_room_id", sa.String(100), nullable=True),
    )

    op.create_table(
        "ratings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("video_date_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("video_dates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rater_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rated_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("adequacy", sa.Integer(), nullable=False),
        sa.Column("humor", sa.Integer(), nullable=False),
        sa.Column("kindness", sa.Integer(), nullable=False),
        sa.Column("empathy", sa.Integer(), nullable=False),
        sa.Column("communicability", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("adequacy BETWEEN 1 AND 5", name="ck_rating_adequacy"),
        sa.CheckConstraint("humor BETWEEN 1 AND 5", name="ck_rating_humor"),
        sa.CheckConstraint("kindness BETWEEN 1 AND 5", name="ck_rating_kindness"),
        sa.CheckConstraint("empathy BETWEEN 1 AND 5", name="ck_rating_empathy"),
        sa.CheckConstraint("communicability BETWEEN 1 AND 5", name="ck_rating_communicability"),
        sa.UniqueConstraint("video_date_id", "rater_id", name="uq_rating_per_date"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_slug", sa.String(50), nullable=False),
        sa.Column("status", subscription_status, server_default="active", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("ratings")
    op.drop_table("video_dates")
    op.drop_table("moderation_queue")
    op.drop_table("user_goal_links")
    op.drop_table("user_goals")
    op.drop_table("user_interests")
    op.drop_table("interests")
    op.drop_column("chats", "circle_count_user_two")
    op.drop_column("chats", "circle_count_user_one")
    op.drop_column("likes", "is_visible_to_receiver")
    op.drop_index("ix_users_video_profile_status", table_name="users")
    op.drop_index("ix_users_overall_rating", table_name="users")
    op.drop_index("ix_users_attractiveness_score", table_name="users")
    op.drop_index("ix_users_has_children", table_name="users")
    op.drop_index("ix_users_gender", table_name="users")
    op.drop_index("ix_users_city", table_name="users")
    op.drop_column("users", "last_active_at")
    op.drop_column("users", "is_online")
    op.drop_column("users", "compatibility_cache")
    op.drop_column("users", "overall_rating")
    op.drop_column("users", "attractiveness_score")
    op.drop_column("users", "children_count")
    op.drop_column("users", "has_children")
    op.drop_column("users", "occupation")
    op.drop_column("users", "description")
    op.drop_column("users", "video_profile_status")
    op.execute("DROP TYPE IF EXISTS subscription_status")
    op.execute("DROP TYPE IF EXISTS moderation_status")
    op.execute("DROP TYPE IF EXISTS video_profile_status")
