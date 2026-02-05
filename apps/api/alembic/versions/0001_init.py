"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-02-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
# noqa: RUF012
# alembic requires these module-level variables
# (자동 생성 규칙을 따르기 위해 명시적으로 유지)
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel_code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("channel_name", sa.String(length=100), nullable=False),
        sa.Column("channel_logo_url", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_channels_channel_code", "channels", ["channel_code"])

    op.create_table(
        "source_pages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_code", sa.String(length=100), nullable=False),
        sa.Column("page_url", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_source_pages_source_code", "source_pages", ["source_code"])

    op.create_table(
        "broadcast_slots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("source_code", sa.String(length=100), nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column("raw_title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.String(length=255), nullable=False),
        sa.Column("product_url", sa.String(length=500), nullable=True),
        sa.Column("price_text", sa.String(length=100), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.Enum("SCHEDULED", "LIVE", "ENDED", name="broadcast_status"),
            nullable=False,
            server_default="SCHEDULED",
        ),
        sa.Column("slot_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
    )
    op.create_unique_constraint("uq_broadcast_slots_slot_hash", "broadcast_slots", ["slot_hash"])
    op.create_index("ix_broadcast_slots_channel_id", "broadcast_slots", ["channel_id"])
    op.create_index("ix_broadcast_slots_start_at", "broadcast_slots", ["start_at"])
    op.create_index("ix_broadcast_slots_normalized_title", "broadcast_slots", ["normalized_title"])
    op.create_index(
        "idx_broadcast_channel_start", "broadcast_slots", ["channel_id", "start_at"]
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("alert_name", sa.String(length=100), nullable=False),
        sa.Column("target_channel_codes", sa.JSON(), nullable=False),
        sa.Column("keyword_list", sa.JSON(), nullable=False),
        sa.Column("category_list", sa.JSON(), nullable=True),
        sa.Column("notify_before_minutes", sa.Integer(), server_default="30", nullable=False),
        sa.Column(
            "destination_type",
            sa.Enum("SLACK", "EMAIL", name="destination_type"),
            server_default="SLACK",
            nullable=False,
        ),
        sa.Column("destination_value", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("broadcast_slots")
    op.drop_table("source_pages")
    op.drop_table("channels")
