"""phase5_billing_2fa_platform_metrics

Revision ID: i4d5e6f7a890
Revises: h3c4d5e6f789
Create Date: 2026-07-21 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "i4d5e6f7a890"
down_revision: Union[str, Sequence[str], None] = "h3c4d5e6f789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("totp_secret", sa.String(length=64), nullable=True))
    op.add_column(
        "users",
        sa.Column("totp_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("organizations", sa.Column("stripe_customer_id", sa.String(length=255), nullable=True))
    op.add_column(
        "organizations", sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True)
    )
    op.add_column("platform_connections", sa.Column("asset_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_platform_connections_asset_id",
        "platform_connections",
        "infrastructure_assets",
        ["asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_platform_connections_asset_id"), "platform_connections", ["asset_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_platform_connections_asset_id"), table_name="platform_connections")
    op.drop_constraint("fk_platform_connections_asset_id", "platform_connections", type_="foreignkey")
    op.drop_column("platform_connections", "asset_id")
    op.drop_column("organizations", "stripe_subscription_id")
    op.drop_column("organizations", "stripe_customer_id")
    op.drop_column("users", "totp_enabled")
    op.drop_column("users", "totp_secret")
