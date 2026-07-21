"""enterprise_phase2_agents_rules_logs

Revision ID: f1a2b3c4d567
Revises: d5a9b2c1e804
Create Date: 2026-07-21 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d567"
down_revision: Union[str, Sequence[str], None] = "d5a9b2c1e804"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monitoring_agents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("api_key_hash", sa.String(length=128), nullable=False),
        sa.Column("api_key_prefix", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("agent_version", sa.String(length=50), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["infrastructure_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_monitoring_agents_api_key_hash"), "monitoring_agents", ["api_key_hash"], unique=True)
    op.create_index(op.f("ix_monitoring_agents_asset_id"), "monitoring_agents", ["asset_id"], unique=False)
    op.create_index(op.f("ix_monitoring_agents_id"), "monitoring_agents", ["id"], unique=False)
    op.create_index(op.f("ix_monitoring_agents_organization_id"), "monitoring_agents", ["organization_id"], unique=False)

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("metric_type", sa.String(length=100), nullable=False),
        sa.Column("operator", sa.String(length=10), server_default="gte", nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("cooldown_minutes", sa.Integer(), server_default="15", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["infrastructure_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alert_rules_asset_id"), "alert_rules", ["asset_id"], unique=False)
    op.create_index(op.f("ix_alert_rules_id"), "alert_rules", ["id"], unique=False)
    op.create_index(op.f("ix_alert_rules_metric_type"), "alert_rules", ["metric_type"], unique=False)
    op.create_index(op.f("ix_alert_rules_organization_id"), "alert_rules", ["organization_id"], unique=False)

    op.create_table(
        "log_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=100), server_default="agent", nullable=False),
        sa.Column("level", sa.String(length=20), server_default="info", nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["infrastructure_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_log_entries_asset_id"), "log_entries", ["asset_id"], unique=False)
    op.create_index(op.f("ix_log_entries_id"), "log_entries", ["id"], unique=False)
    op.create_index(op.f("ix_log_entries_level"), "log_entries", ["level"], unique=False)
    op.create_index(op.f("ix_log_entries_logged_at"), "log_entries", ["logged_at"], unique=False)
    op.create_index(op.f("ix_log_entries_organization_id"), "log_entries", ["organization_id"], unique=False)
    op.create_index(op.f("ix_log_entries_source"), "log_entries", ["source"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_log_entries_source"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_organization_id"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_logged_at"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_level"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_id"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_asset_id"), table_name="log_entries")
    op.drop_table("log_entries")

    op.drop_index(op.f("ix_alert_rules_organization_id"), table_name="alert_rules")
    op.drop_index(op.f("ix_alert_rules_metric_type"), table_name="alert_rules")
    op.drop_index(op.f("ix_alert_rules_id"), table_name="alert_rules")
    op.drop_index(op.f("ix_alert_rules_asset_id"), table_name="alert_rules")
    op.drop_table("alert_rules")

    op.drop_index(op.f("ix_monitoring_agents_organization_id"), table_name="monitoring_agents")
    op.drop_index(op.f("ix_monitoring_agents_id"), table_name="monitoring_agents")
    op.drop_index(op.f("ix_monitoring_agents_asset_id"), table_name="monitoring_agents")
    op.drop_index(op.f("ix_monitoring_agents_api_key_hash"), table_name="monitoring_agents")
    op.drop_table("monitoring_agents")
