"""module04_monitoring_alerts_incidents

Revision ID: e8f2a3b4c905
Revises: a3f8c2d91e04
Create Date: 2026-07-21 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8f2a3b4c905"
down_revision: Union[str, Sequence[str], None] = "a3f8c2d91e04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("incident_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("assignee_user_id", sa.Integer(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["infrastructure_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_incidents_asset_id"), "incidents", ["asset_id"], unique=False)
    op.create_index(op.f("ix_incidents_id"), "incidents", ["id"], unique=False)
    op.create_index(op.f("ix_incidents_incident_type"), "incidents", ["incident_type"], unique=False)
    op.create_index(op.f("ix_incidents_organization_id"), "incidents", ["organization_id"], unique=False)
    op.create_index(op.f("ix_incidents_status"), "incidents", ["status"], unique=False)
    op.create_index(op.f("ix_incidents_assignee_user_id"), "incidents", ["assignee_user_id"], unique=False)

    op.create_table(
        "monitoring_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("metric_type", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["infrastructure_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_monitoring_metrics_asset_id"), "monitoring_metrics", ["asset_id"], unique=False)
    op.create_index(op.f("ix_monitoring_metrics_metric_type"), "monitoring_metrics", ["metric_type"], unique=False)
    op.create_index(op.f("ix_monitoring_metrics_organization_id"), "monitoring_metrics", ["organization_id"], unique=False)
    op.create_index(op.f("ix_monitoring_metrics_recorded_at"), "monitoring_metrics", ["recorded_at"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["infrastructure_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_alert_type"), "alerts", ["alert_type"], unique=False)
    op.create_index(op.f("ix_alerts_asset_id"), "alerts", ["asset_id"], unique=False)
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_index(op.f("ix_alerts_level"), "alerts", ["level"], unique=False)
    op.create_index(op.f("ix_alerts_organization_id"), "alerts", ["organization_id"], unique=False)
    op.create_index(op.f("ix_alerts_status"), "alerts", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("monitoring_metrics")
    op.drop_table("incidents")
