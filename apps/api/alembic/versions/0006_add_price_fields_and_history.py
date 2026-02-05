"""add price fields and history table

Revision ID: 0006_add_price_fields_and_history
Revises: 0005_add_channel_stream_url
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0006_add_price_fields_and_history"
down_revision = "0005_add_channel_stream_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("broadcast_slots")}

    if "sale_price" not in columns:
        op.add_column("broadcast_slots", sa.Column("sale_price", sa.Integer(), nullable=True))
    if "original_price" not in columns:
        op.add_column("broadcast_slots", sa.Column("original_price", sa.Integer(), nullable=True))
    if "discount_rate" not in columns:
        op.add_column("broadcast_slots", sa.Column("discount_rate", sa.Float(), nullable=True))

    tables = set(inspector.get_table_names())
    if "broadcast_price_history" not in tables:
        op.create_table(
            "broadcast_price_history",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("broadcast_slot_id", sa.Integer(), sa.ForeignKey("broadcast_slots.id"), index=True),
            sa.Column("collected_at", sa.DateTime(), nullable=False),
            sa.Column("sale_price", sa.Integer(), nullable=True),
            sa.Column("original_price", sa.Integer(), nullable=True),
            sa.Column("discount_rate", sa.Float(), nullable=True),
        )
        op.create_index(
            "idx_price_history_slot_time",
            "broadcast_price_history",
            ["broadcast_slot_id", "collected_at"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "broadcast_price_history" in tables:
        op.drop_index("idx_price_history_slot_time", table_name="broadcast_price_history")
        op.drop_table("broadcast_price_history")

    columns = {col["name"] for col in inspector.get_columns("broadcast_slots")}
    if "discount_rate" in columns:
        op.drop_column("broadcast_slots", "discount_rate")
    if "original_price" in columns:
        op.drop_column("broadcast_slots", "original_price")
    if "sale_price" in columns:
        op.drop_column("broadcast_slots", "sale_price")
