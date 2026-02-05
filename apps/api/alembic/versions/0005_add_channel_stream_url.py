"""add channel_stream_url to channels

Revision ID: 0005_add_channel_stream_url
Revises: 0004_add_live_url_to_broadcast_slots
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0005_add_channel_stream_url"
down_revision = "0004_add_live_url_to_broadcast_slots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("channels")}
    # why: 이미 수동 적용된 환경에서 중복 컬럼 에러 방지
    if "channel_stream_url" not in columns:
        op.add_column(
            "channels", sa.Column("channel_stream_url", sa.String(length=500), nullable=True)
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("channels")}
    if "channel_stream_url" in columns:
        op.drop_column("channels", "channel_stream_url")
