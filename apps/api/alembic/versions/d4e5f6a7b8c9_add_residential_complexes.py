"""Add developers and residential complexes.

Revision ID: d4e5f6a7b8c9
Revises: bbc830940b0b
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "bbc830940b0b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "developers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(220), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("cover_url", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_developers_slug", "developers", ["slug"], unique=True)
    op.create_index("ix_developers_is_verified", "developers", ["is_verified"])

    op.create_table(
        "residential_complexes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("developer_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(220), nullable=False),
        sa.Column("slug", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("city", sa.String(120), nullable=False),
        sa.Column("district", sa.String(120), nullable=True),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=True),
        sa.Column("delivery_status", sa.String(32), nullable=False),
        sa.Column("min_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("price_per_sqm_from", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("cover_url", sa.String(500), nullable=True),
        sa.Column("gallery", sa.JSON(), nullable=False),
        sa.Column("amenities", sa.JSON(), nullable=False),
        sa.Column("payment_terms", sa.Text(), nullable=True),
        sa.Column("buildings_count", sa.Integer(), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["developer_id"], ["developers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for name in ("developer_id", "slug", "is_featured", "is_published"):
        op.create_index(f"ix_residential_complexes_{name}", "residential_complexes", [name], unique=name == "slug")

    op.create_table(
        "complex_unit_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("complex_id", sa.Uuid(), nullable=False),
        sa.Column("rooms", sa.Integer(), nullable=False),
        sa.Column("area_from", sa.Numeric(10, 2), nullable=False),
        sa.Column("area_to", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_from", sa.Numeric(14, 2), nullable=True),
        sa.Column("available_count", sa.Integer(), nullable=False),
        sa.Column("plan_url", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["complex_id"], ["residential_complexes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complex_unit_types_complex_id", "complex_unit_types", ["complex_id"])


def downgrade() -> None:
    op.drop_table("complex_unit_types")
    op.drop_table("residential_complexes")
    op.drop_table("developers")
