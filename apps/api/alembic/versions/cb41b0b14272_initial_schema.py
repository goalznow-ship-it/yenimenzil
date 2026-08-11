"""initial schema

Revision ID: cb41b0b14272
Revises:
Create Date: 2026-08-10 19:18:54.616627

"""
from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa

from alembic import op

revision: str = "cb41b0b14272"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "agencies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agencies_slug"), "agencies", ["slug"], unique=True)

    op.create_table(
        "property_features",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("label_az", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_property_features_code"), "property_features", ["code"], unique=True
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("agency_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("verified_identity", sa.Boolean(), nullable=False),
        sa.Column("verified_phone", sa.Boolean(), nullable=False),
        sa.Column("member_since", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("member_since", sa.Date(), nullable=True),
        sa.Column("phone_verified", sa.Boolean(), nullable=False),
        sa.Column("identity_verified", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "properties",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference_code", sa.String(length=32), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=True),
        sa.Column("agent_id", sa.Uuid(), nullable=True),
        sa.Column(
            "seller_kind",
            sa.Enum(
                "OWNER", "AGENCY", "AGENT", name="sellerkind", native_enum=False, length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "deal_type",
            sa.Enum(
                "SALE", "RENT", "DAILY", name="dealtype", native_enum=False, length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "property_type",
            sa.Enum(
                "APARTMENT",
                "NEW_BUILDING",
                "OLD_BUILDING",
                "HOUSE",
                "VILLA",
                "LAND",
                "OFFICE",
                "COMMERCIAL",
                "GARAGE",
                name="propertytype",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "PENDING_REVIEW",
                "ACTIVE",
                "REJECTED",
                "EXPIRED",
                "SOLD",
                "RENTED",
                "ARCHIVED",
                "SUSPENDED",
                name="propertystatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.Enum(
                "AZN", "USD", "EUR", name="currency", native_enum=False, length=32
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("rooms", sa.Integer(), nullable=False),
        sa.Column("bedrooms", sa.Integer(), nullable=True),
        sa.Column("bathrooms", sa.Integer(), nullable=True),
        sa.Column("area_total", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("area_living", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("area_land", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("total_floors", sa.Integer(), nullable=True),
        sa.Column(
            "building_type",
            sa.Enum("NEW", "OLD", name="buildingtype", native_enum=False, length=32),
            nullable=True,
        ),
        sa.Column(
            "repair_status",
            sa.Enum(
                "RENOVATED",
                "COSMETIC",
                "NEEDS_REPAIR",
                "NONE",
                name="repairstatus",
                native_enum=False,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column(
            "document_type",
            sa.Enum(
                "CITIZENSHIP",
                "EXTRACT",
                "CERTIFICATE",
                name="documenttype",
                native_enum=False,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("mortgage_available", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_premium", sa.Boolean(), nullable=False),
        sa.Column("is_promoted", sa.Boolean(), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_properties_area", "properties", ["area_total"], unique=False)
    op.create_index(
        "ix_properties_deal_status", "properties", ["deal_type", "status"], unique=False
    )
    op.create_index(
        op.f("ix_properties_deal_type"), "properties", ["deal_type"], unique=False
    )
    op.create_index("ix_properties_price", "properties", ["price"], unique=False)
    op.create_index(
        op.f("ix_properties_property_type"),
        "properties",
        ["property_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_properties_reference_code"),
        "properties",
        ["reference_code"],
        unique=True,
    )
    op.create_index(op.f("ix_properties_slug"), "properties", ["slug"], unique=True)
    op.create_index(op.f("ix_properties_status"), "properties", ["status"], unique=False)

    op.create_table(
        "favorites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "property_id", name="uq_user_property"),
    )
    op.create_index(
        op.f("ix_favorites_property_id"), "favorites", ["property_id"], unique=False
    )
    op.create_index(
        op.f("ix_favorites_user_id"), "favorites", ["user_id"], unique=False
    )

    op.create_table(
        "property_feature_items",
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("feature_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["feature_id"], ["property_features.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["property_id"], ["properties.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("property_id", "feature_id"),
    )

    op.create_table(
        "property_locations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "point",
            geoalchemy2.types.Geography(
                geometry_type="POINT",
                srid=4326,
                dimension=2,
                from_text="ST_GeogFromText",
                name="geography",
                nullable=False,
                spatial_index=False,
            ),
            nullable=False,
        ),
        sa.Column("address_text", sa.String(length=300), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("settlement", sa.String(length=100), nullable=True),
        sa.Column("neighborhood", sa.String(length=100), nullable=True),
        sa.Column("metro", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("property_id"),
    )
    op.create_index(
        "idx_property_locations_point",
        "property_locations",
        ["point"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        op.f("ix_property_locations_city"), "property_locations", ["city"], unique=False
    )
    op.create_index(
        op.f("ix_property_locations_district"),
        "property_locations",
        ["district"],
        unique=False,
    )

    op.create_table(
        "property_media",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "IMAGE", "VIDEO", name="mediakind", native_enum=False, length=32
            ),
            nullable=False,
        ),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("alt", sa.String(length=300), nullable=True),
        sa.Column("placeholder", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_cover", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_property_media_property_id"),
        "property_media",
        ["property_id"],
        unique=False,
    )

    op.create_table(
        "property_price_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_property_price_history_property_id"),
        "property_price_history",
        ["property_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_property_price_history_property_id"), table_name="property_price_history"
    )
    op.drop_table("property_price_history")
    op.drop_index(op.f("ix_property_media_property_id"), table_name="property_media")
    op.drop_table("property_media")
    op.drop_index(op.f("ix_property_locations_district"), table_name="property_locations")
    op.drop_index(op.f("ix_property_locations_city"), table_name="property_locations")
    op.drop_index("idx_property_locations_point", table_name="property_locations")
    op.drop_table("property_locations")
    op.drop_table("property_feature_items")
    op.drop_index(op.f("ix_favorites_user_id"), table_name="favorites")
    op.drop_index(op.f("ix_favorites_property_id"), table_name="favorites")
    op.drop_table("favorites")
    op.drop_index(op.f("ix_properties_status"), table_name="properties")
    op.drop_index(op.f("ix_properties_slug"), table_name="properties")
    op.drop_index(op.f("ix_properties_reference_code"), table_name="properties")
    op.drop_index(op.f("ix_properties_property_type"), table_name="properties")
    op.drop_index("ix_properties_price", table_name="properties")
    op.drop_index(op.f("ix_properties_deal_type"), table_name="properties")
    op.drop_index("ix_properties_deal_status", table_name="properties")
    op.drop_index("ix_properties_area", table_name="properties")
    op.drop_table("properties")
    op.drop_table("profiles")
    op.drop_table("agents")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_property_features_code"), table_name="property_features")
    op.drop_table("property_features")
    op.drop_index(op.f("ix_agencies_slug"), table_name="agencies")
    op.drop_table("agencies")
