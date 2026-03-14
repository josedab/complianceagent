"""Add critical persistence tables for evidence generation, certification, and remediation.

Revision ID: 010_critical_persistence
Revises: 009_notifications
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


revision: str = "010_critical_persistence"
down_revision: str | None = "009_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Evidence generation records
    op.create_table(
        "evidence_generation_records",
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
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("artifact_url", sa.String(2000), nullable=True),
        sa.Column("generation_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evidence_gen_org_id", "evidence_generation_records", ["organization_id"])
    op.create_index("ix_evidence_gen_control_id", "evidence_generation_records", ["control_id"])

    # Certification run records
    op.create_table(
        "certification_run_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("regulation", sa.String(100), nullable=False),
        sa.Column("run_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="running", nullable=False),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("controls_total", sa.Integer, server_default="0"),
        sa.Column("controls_passed", sa.Integer, server_default="0"),
        sa.Column("controls_failed", sa.Integer, server_default="0"),
        sa.Column("run_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cert_run_org_id", "certification_run_records", ["organization_id"])

    # Certification control gap records
    op.create_table(
        "cert_control_gap_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("certification_run_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("control_id", sa.String(200), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("remediation_hint", sa.Text, nullable=True),
        sa.Column("gap_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cert_gap_org_id", "cert_control_gap_records", ["organization_id"])
    op.create_index("ix_cert_gap_run_id", "cert_control_gap_records", ["run_id"])

    # Remediation pipeline records
    op.create_table(
        "remediation_pipeline_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trigger_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("fixes_total", sa.Integer, server_default="0"),
        sa.Column("fixes_applied", sa.Integer, server_default="0"),
        sa.Column("fixes_failed", sa.Integer, server_default="0"),
        sa.Column("pipeline_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_remed_pipeline_org_id", "remediation_pipeline_records", ["organization_id"])

    # Remediation fix records
    op.create_table(
        "remediation_fix_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pipeline_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("remediation_pipeline_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("control_id", sa.String(200), nullable=False),
        sa.Column("fix_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("diff_url", sa.String(2000), nullable=True),
        sa.Column("fix_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_remed_fix_org_id", "remediation_fix_records", ["organization_id"])
    op.create_index("ix_remed_fix_pipeline_id", "remediation_fix_records", ["pipeline_id"])

    # Remediation approval records
    op.create_table(
        "remediation_approval_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fix_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("remediation_fix_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decision", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_remed_approval_org_id", "remediation_approval_records", ["organization_id"])
    op.create_index("ix_remed_approval_fix_id", "remediation_approval_records", ["fix_id"])


def downgrade() -> None:
    op.drop_table("remediation_approval_records")
    op.drop_table("remediation_fix_records")
    op.drop_table("remediation_pipeline_records")
    op.drop_table("cert_control_gap_records")
    op.drop_table("certification_run_records")
    op.drop_table("evidence_generation_records")
