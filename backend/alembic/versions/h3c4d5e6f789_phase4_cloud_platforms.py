"""phase4_cloud_platforms

Revision ID: h3c4d5e6f789
Revises: g2b3c4d5e678
Create Date: 2026-07-21 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h3c4d5e6f789"
down_revision: Union[str, Sequence[str], None] = "g2b3c4d5e678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("connection_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("endpoint", sa.String(length=500), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_collect_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collect_status", sa.String(length=50), server_default="idle", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_platform_connections_connection_type"), "platform_connections", ["connection_type"], unique=False)
    op.create_index(op.f("ix_platform_connections_id"), "platform_connections", ["id"], unique=False)
    op.create_index(op.f("ix_platform_connections_organization_id"), "platform_connections", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_platform_connections_organization_id"), table_name="platform_connections")
    op.drop_index(op.f("ix_platform_connections_id"), table_name="platform_connections")
    op.drop_index(op.f("ix_platform_connections_connection_type"), table_name="platform_connections")
    op.drop_table("platform_connections")
