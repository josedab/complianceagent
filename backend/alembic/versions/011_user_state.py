"""Add user state tables for copilot sessions, marketplace, gamification, trust, workflows.

Revision ID: 011_user_state
Revises: 010_critical_persistence
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


revision: str = "011_user_state"
down_revision: str | None = "010_critical_persistence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Copilot session records
    op.create_table(
        "copilot_session_records",
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
        sa.Column("session_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), server_default="active", nullable=False),
        sa.Column("message_count", sa.Integer, server_default="0"),
        sa.Column("session_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_copilot_session_org_id", "copilot_session_records", ["organization_id"])
    op.create_index("ix_copilot_session_user_id", "copilot_session_records", ["user_id"])

    # Agent marketplace records
    op.create_table(
        "agent_marketplace_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="published", nullable=False),
        sa.Column("capabilities", sa.Text, server_default="[]"),
        sa.Column("agent_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("rating", sa.Float, server_default="0.0"),
        sa.Column("install_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_marketplace_org_id", "agent_marketplace_records", ["organization_id"])

    # Trust attestation records
    op.create_table(
        "trust_attestation_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "attested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attestation_type", sa.String(100), nullable=False),
        sa.Column("regulation", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("evidence_references", sa.Text, server_default="[]"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trust_attestation_org_id", "trust_attestation_records", ["organization_id"])

    # Gamification profile records
    op.create_table(
        "gamification_profile_records",
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
        sa.Column("level", sa.Integer, server_default="1"),
        sa.Column("xp_total", sa.Integer, server_default="0"),
        sa.Column("badges", sa.Text, server_default="[]"),
        sa.Column("streak_days", sa.Integer, server_default="0"),
        sa.Column("profile_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_gamification_profile_org_id", "gamification_profile_records", ["organization_id"])
    op.create_index("ix_gamification_profile_user_id", "gamification_profile_records", ["user_id"])

    # Gamification event records
    op.create_table(
        "gamification_event_records",
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
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("xp_awarded", sa.Integer, server_default="0"),
        sa.Column("badge_awarded", sa.String(100), nullable=True),
        sa.Column("event_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_gamification_event_org_id", "gamification_event_records", ["organization_id"])
    op.create_index("ix_gamification_event_user_id", "gamification_event_records", ["user_id"])

    # Workflow definition records
    op.create_table(
        "workflow_definition_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("trigger_type", sa.String(100), nullable=False),
        sa.Column("steps", sa.Text, server_default="[]"),
        sa.Column("workflow_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workflow_def_org_id", "workflow_definition_records", ["organization_id"])

    # Workflow execution records
    op.create_table(
        "workflow_execution_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_definition_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), server_default="running", nullable=False),
        sa.Column("triggered_by", sa.String(200), nullable=False),
        sa.Column("execution_log", postgresql.JSONB, server_default="{}"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workflow_exec_org_id", "workflow_execution_records", ["organization_id"])
    op.create_index("ix_workflow_exec_def_id", "workflow_execution_records", ["definition_id"])


def downgrade() -> None:
    op.drop_table("workflow_execution_records")
    op.drop_table("workflow_definition_records")
    op.drop_table("gamification_event_records")
    op.drop_table("gamification_profile_records")
    op.drop_table("trust_attestation_records")
    op.drop_table("agent_marketplace_records")
    op.drop_table("copilot_session_records")
