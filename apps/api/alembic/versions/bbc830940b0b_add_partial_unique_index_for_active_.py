"""add partial unique index for active promotion purchases

Revision ID: bbc830940b0b
Revises: 034cb2aa8fc1
Create Date: 2026-08-14 08:03:26.831941

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "bbc830940b0b"
down_revision: str | None = "034cb2aa8fc1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_promotion_purchases_active",
        "promotion_purchases",
        ["property_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_promotion_purchases_active", table_name="promotion_purchases")
