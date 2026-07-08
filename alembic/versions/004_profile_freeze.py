"""Profile freeze and soft delete."""

import sqlalchemy as sa
from alembic import op

revision = "004_profile_freeze"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("profile_frozen", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_profile_frozen", "users", ["profile_frozen"])
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_index("ix_users_profile_frozen", table_name="users")
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "profile_frozen")
