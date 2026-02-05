"""add live_url to broadcast_slots

Revision ID: 0004_add_live_url_to_broadcast_slots
Revises: 0003_add_channel_live_url
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0004_add_live_url_to_broadcast_slots"
down_revision = "0003_add_channel_live_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("broadcast_slots")}
    # why: 이미 수동/부분 적용된 환경에서 중복 컬럼 에러를 피하기 위해 방어
    if "live_url" not in columns:
        op.add_column(
            "broadcast_slots", sa.Column("live_url", sa.String(length=500), nullable=True)
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("broadcast_slots")}
    if "live_url" in columns:
        op.drop_column("broadcast_slots", "live_url")
