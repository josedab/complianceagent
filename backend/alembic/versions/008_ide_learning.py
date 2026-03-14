"""Add durable IDE learning and team suppression tables.

Revision ID: 008_ide_learning
Revises: 007_health_scores
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


revision: str = "008_ide_learning"
down_revision: str | None = "007_health_scores"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ide_team_suppressions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rule_id", sa.String(200), nullable=False),
        sa.Column("pattern", sa.String(500), nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("approved", sa.Boolean, server_default="false"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_count", sa.Integer, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ide_team_suppressions_organization_id",
        "ide_team_suppressions",
        ["organization_id"],
    )
    op.create_index(
        "ix_ide_team_suppressions_rule_id",
        "ide_team_suppressions",
        ["rule_id"],
    )

    op.create_table(
        "ide_rule_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rule_id", sa.String(200), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("event_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ide_rule_events_organization_id",
        "ide_rule_events",
        ["organization_id"],
    )
    op.create_index(
        "ix_ide_rule_events_user_id",
        "ide_rule_events",
        ["user_id"],
    )
    op.create_index(
        "ix_ide_rule_events_rule_id",
        "ide_rule_events",
        ["rule_id"],
    )


def downgrade() -> None:
    op.drop_table("ide_rule_events")
    op.drop_table("ide_team_suppressions")
