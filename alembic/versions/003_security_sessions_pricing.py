"""security: sessions, audit, consent, pricing, payments

Revision ID: 003
Revises: 002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pricing_type = postgresql.ENUM("package", "per_minute", name="pricing_type", create_type=False)
    payment_status = postgresql.ENUM(
        "pending", "completed", "failed", "refunded", name="payment_status", create_type=False
    )
    payment_kind = postgresql.ENUM(
        "balance_topup", "video_date", "package_purchase", name="payment_kind", create_type=False
    )

    for enum_type in (pricing_type, payment_status, payment_kind):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.add_column("users", sa.Column("accepted_terms_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("accepted_privacy_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("pd_consent_version", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("totp_secret_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("totp_enabled", sa.Boolean(), server_default="false", nullable=False))

    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("device_info", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("trusted_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_refresh_token_hash", "user_sessions", ["refresh_token_hash"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    op.create_table(
        "pricing_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("pricing_type", pricing_type, nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("price_kopecks", sa.Integer(), nullable=False),
        sa.Column("per_minute_rate_kopecks", sa.Integer(), nullable=True),
        sa.Column("min_minutes", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
    )

    op.create_table(
        "payment_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", payment_kind, nullable=False),
        sa.Column("amount_kopecks", sa.Integer(), nullable=False),
        sa.Column("status", payment_status, server_default="pending", nullable=False),
        sa.Column("idempotency_key", sa.String(64), unique=True, nullable=False),
        sa.Column("provider_ref", sa.String(255), nullable=True),
        sa.Column("pricing_plan_slug", sa.String(50), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_payment_transactions_user_id", "payment_transactions", ["user_id"])

    op.add_column("video_dates", sa.Column("pricing_plan_slug", sa.String(50), nullable=True))
    op.add_column("video_dates", sa.Column("purchased_minutes", sa.Integer(), nullable=True))
    op.add_column("video_dates", sa.Column("price_kopecks", sa.Integer(), server_default="0", nullable=False))

    # default pricing — легко менять через админку (этап 9)
    op.execute("""
        INSERT INTO pricing_plans (id, slug, name, pricing_type, duration_minutes, price_kopecks, per_minute_rate_kopecks, min_minutes, sort_order)
        VALUES
            (gen_random_uuid(), 'package_1h', '1 час', 'package', 60, 40000, NULL, NULL, 1),
            (gen_random_uuid(), 'package_2h', '2 часа', 'package', 120, 76000, NULL, NULL, 2),
            (gen_random_uuid(), 'package_3h', '3 часа', 'package', 180, 108000, NULL, NULL, 3),
            (gen_random_uuid(), 'package_4h', '4 часа', 'package', 240, 140000, NULL, NULL, 4),
            (gen_random_uuid(), 'per_minute', 'Поминутный', 'per_minute', NULL, 0, 667, 15, 5)
    """)


def downgrade() -> None:
    op.drop_column("video_dates", "price_kopecks")
    op.drop_column("video_dates", "purchased_minutes")
    op.drop_column("video_dates", "pricing_plan_slug")
    op.drop_table("payment_transactions")
    op.drop_table("pricing_plans")
    op.drop_table("audit_log")
    op.drop_table("user_sessions")
    op.drop_column("users", "totp_enabled")
    op.drop_column("users", "totp_secret_encrypted")
    op.drop_column("users", "pd_consent_version")
    op.drop_column("users", "accepted_privacy_at")
    op.drop_column("users", "accepted_terms_at")
    op.execute("DROP TYPE IF EXISTS payment_kind")
    op.execute("DROP TYPE IF EXISTS payment_status")
    op.execute("DROP TYPE IF EXISTS pricing_type")
