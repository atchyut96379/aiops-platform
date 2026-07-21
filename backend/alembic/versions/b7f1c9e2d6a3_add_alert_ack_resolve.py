"""add_alert_ack_resolve

Revision ID: b7f1c9e2d6a3
Revises: a3f8c2d91e04
Create Date: 2026-07-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7f1c9e2d6a3"
down_revision: Union[str, Sequence[str], None] = "e8f2a3b4c905"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add acknowledgement and resolution columns to alerts
    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        batch_op.add_column(sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("acknowledged_by_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        batch_op.add_column(sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("resolved_by_id", sa.Integer(), nullable=True))

        batch_op.create_foreign_key(
            "fk_alerts_acknowledged_by_id_users",
            "users",
            ["acknowledged_by_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_alerts_resolved_by_id_users",
            "users",
            ["resolved_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

        batch_op.create_index(batch_op.f("ix_alerts_acknowledged"), ["acknowledged"], unique=False)
        batch_op.create_index(batch_op.f("ix_alerts_resolved"), ["resolved"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_alerts_resolved"))
        batch_op.drop_index(batch_op.f("ix_alerts_acknowledged"))

        batch_op.drop_constraint("fk_alerts_resolved_by_id_users", type_="foreignkey")
        batch_op.drop_constraint("fk_alerts_acknowledged_by_id_users", type_="foreignkey")

        batch_op.drop_column("resolved_by_id")
        batch_op.drop_column("resolved_at")
        batch_op.drop_column("resolved")
        batch_op.drop_column("acknowledged_by_id")
        batch_op.drop_column("acknowledged_at")
        batch_op.drop_column("acknowledged")
