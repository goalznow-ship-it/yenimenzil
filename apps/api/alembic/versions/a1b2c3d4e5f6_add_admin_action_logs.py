"""add admin action audit logs

Revision ID: a1b2c3d4e5f6
Revises: 42d8525bb4fd
Create Date: 2026-08-12 09:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = '42d8525bb4fd'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'admin_action_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('admin_id', sa.Uuid(), nullable=True),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('entity_type', sa.String(length=32), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_admin_action_logs_action', 'admin_action_logs', ['action'])
    op.create_index('ix_admin_action_logs_entity_type', 'admin_action_logs', ['entity_type'])
    op.create_index('ix_admin_action_logs_admin_id', 'admin_action_logs', ['admin_id'])
    op.create_index('ix_admin_action_logs_created_at', 'admin_action_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_admin_action_logs_created_at', table_name='admin_action_logs')
    op.drop_index('ix_admin_action_logs_admin_id', table_name='admin_action_logs')
    op.drop_index('ix_admin_action_logs_entity_type', table_name='admin_action_logs')
    op.drop_index('ix_admin_action_logs_action', table_name='admin_action_logs')
    op.drop_table('admin_action_logs')