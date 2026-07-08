"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    chat_status = postgresql.ENUM("active", "archived", name="chat_status", create_type=False)
    chat_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone", sa.String(20), unique=True, nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("birth_time", sa.String(10), nullable=True),
        sa.Column("birth_place", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("gender", sa.String(10), nullable=True),
        sa.Column("balance", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_registered", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("video_profile_url", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receiver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_mutual", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("sender_id", "receiver_id", name="uq_like_sender_receiver"),
    )
    op.create_index("ix_likes_sender_id", "likes", ["sender_id"])
    op.create_index("ix_likes_receiver_id", "likes", ["receiver_id"])

    op.create_table(
        "chats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_one_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_two_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", chat_status, server_default="active", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_one_id", "user_two_id", name="uq_chat_users"),
    )
    op.create_index("ix_chats_user_one_id", "chats", ["user_one_id"])
    op.create_index("ix_chats_user_two_id", "chats", ["user_two_id"])


def downgrade() -> None:
    op.drop_table("chats")
    op.drop_table("likes")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS chat_status")
