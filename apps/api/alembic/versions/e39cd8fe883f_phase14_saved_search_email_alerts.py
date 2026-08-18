"""phase14 saved search email alerts

Revision ID: e39cd8fe883f
Revises: 0cb5ce33bd37
Create Date: 2026-08-15 19:23:03.598061

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e39cd8fe883f"
down_revision: str | None = "0cb5ce33bd37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column(
            "payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")
        ),
    )
    op.add_column(
        "saved_searches",
        sa.Column(
            "email_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )


def downgrade() -> None:
    op.drop_column("saved_searches", "email_enabled")
    op.drop_column("notifications", "payload")
