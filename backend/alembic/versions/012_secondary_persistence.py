"""Add secondary persistence tables for drift, posture, evidence vault, healing, MCP.

Revision ID: 012_secondary_persistence
Revises: 011_user_state
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


revision: str = "012_secondary_persistence"
down_revision: str | None = "011_user_state"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drift baseline records
    op.create_table(
        "drift_baseline_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("regulation", sa.String(100), nullable=False),
        sa.Column("snapshot", postgresql.JSONB, server_default="{}"),
        sa.Column("hash_value", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_drift_baseline_org_id", "drift_baseline_records", ["organization_id"])

    # Drift event records
    op.create_table(
        "drift_event_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "baseline_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drift_baseline_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("drift_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("affected_controls", sa.Text, server_default="[]"),
        sa.Column("drift_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_drift_event_org_id", "drift_event_records", ["organization_id"])
    op.create_index("ix_drift_event_baseline_id", "drift_event_records", ["baseline_id"])

    # Drift alert records
    op.create_table(
        "drift_alert_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "drift_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drift_event_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), server_default="open", nullable=False),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("alert_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_drift_alert_org_id", "drift_alert_records", ["organization_id"])
    op.create_index("ix_drift_alert_event_id", "drift_alert_records", ["drift_event_id"])

    # Posture score records
    op.create_table(
        "posture_score_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("regulation", sa.String(100), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("grade", sa.String(10), nullable=False),
        sa.Column("controls_passing", sa.Integer, server_default="0"),
        sa.Column("controls_total", sa.Integer, server_default="0"),
        sa.Column("score_breakdown", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_posture_score_org_id", "posture_score_records", ["organization_id"])

    # Evidence vault records
    op.create_table(
        "evidence_vault_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("control_id", sa.String(200), nullable=False),
        sa.Column("regulation", sa.String(100), nullable=False),
        sa.Column("evidence_type", sa.String(100), nullable=False),
        sa.Column("artifact_url", sa.String(2000), nullable=False),
        sa.Column("hash_sha256", sa.String(64), nullable=False),
        sa.Column("collected_by", sa.String(200), nullable=False),
        sa.Column("vault_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evidence_vault_org_id", "evidence_vault_records", ["organization_id"])
    op.create_index("ix_evidence_vault_control_id", "evidence_vault_records", ["control_id"])

    # Self-healing event records
    op.create_table(
        "self_healing_event_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trigger_type", sa.String(100), nullable=False),
        sa.Column("action_taken", sa.String(200), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("healing_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_self_healing_org_id", "self_healing_event_records", ["organization_id"])

    # MCP execution records
    op.create_table(
        "mcp_execution_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tool_name", sa.String(200), nullable=False),
        sa.Column("input_params", postgresql.JSONB, server_default="{}"),
        sa.Column("output_result", postgresql.JSONB, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_mcp_exec_org_id", "mcp_execution_records", ["organization_id"])
    op.create_index("ix_mcp_exec_tool_name", "mcp_execution_records", ["tool_name"])


def downgrade() -> None:
    op.drop_table("mcp_execution_records")
    op.drop_table("self_healing_event_records")
    op.drop_table("evidence_vault_records")
    op.drop_table("posture_score_records")
    op.drop_table("drift_alert_records")
    op.drop_table("drift_event_records")
    op.drop_table("drift_baseline_records")
