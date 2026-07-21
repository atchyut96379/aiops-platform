"""module07_10_attachments_knowledge_alerts

Revision ID: d5a9b2c1e804
Revises: c4e8f1a2b903
Create Date: 2026-07-21 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5a9b2c1e804"
down_revision: Union[str, Sequence[str], None] = "c4e8f1a2b903"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("incident_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_alerts_incident_id"), ["incident_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_alerts_incident_id_incidents",
            "incidents",
            ["incident_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "incident_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("incident_attachments", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_incident_attachments_incident_id"), ["incident_id"], unique=False
        )

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tags", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("knowledge_documents", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_knowledge_documents_organization_id"), ["organization_id"], unique=False
        )


def downgrade() -> None:
    op.drop_table("knowledge_documents")
    op.drop_table("incident_attachments")
    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.drop_constraint("fk_alerts_incident_id_incidents", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_alerts_incident_id"))
        batch_op.drop_column("incident_id")
