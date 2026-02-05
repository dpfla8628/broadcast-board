"""add channel_live_url to channels

Revision ID: 0003_add_channel_live_url
Revises: 0002_add_category_to_broadcast_slots
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_channel_live_url"
down_revision = "0002_add_category"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("channels", sa.Column("channel_live_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("channels", "channel_live_url")
