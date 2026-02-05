"""add category to broadcast_slots

Revision ID: 0002_add_category
Revises: 0001_init
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_category"
# noqa: RUF012
# alembic requires these module-level variables
# (자동 생성 규칙을 따르기 위해 명시적으로 유지)
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("broadcast_slots", sa.Column("category", sa.String(length=50), nullable=True))
    op.create_index("idx_broadcast_category", "broadcast_slots", ["category"])


def downgrade() -> None:
    op.drop_index("idx_broadcast_category", table_name="broadcast_slots")
    op.drop_column("broadcast_slots", "category")
