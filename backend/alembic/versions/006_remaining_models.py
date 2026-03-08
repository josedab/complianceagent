"""Add remaining model tables.

Revision ID: 006_remaining_models
Revises: 005_notification_preferences
Create Date: 2026-03-15

Tables for:
- Architecture advisor (reviews, risk records)
- Regulatory horizon scanner (pending legislation, impact predictions)
- Continuous control testing (control tests, control test results)
- Multi-entity rollup (entity nodes)
- Board reports
- Audit workspace (workspaces, gap analyses)
- Dependency scanner (scans)
- Compliance testing (test suite runs, generated test records)
- SaaS multi-tenancy (tenants, usage records)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '006_remaining_models'
down_revision: Union[str, None] = '005_notification_preferences'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Architecture Reviews ────────────────────────────────────────

    op.create_table(
        'architecture_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('repository', sa.String(500), nullable=False, index=True),
        sa.Column('overall_score', sa.Float(), server_default='0'),
        sa.Column('grade', sa.String(5), server_default='F'),
        sa.Column('max_score', sa.Float(), server_default='100'),
        sa.Column('total_patterns_detected', sa.Integer(), server_default='0'),
        sa.Column('anti_patterns_count', sa.Integer(), server_default='0'),
        sa.Column('recommended_patterns_count', sa.Integer(), server_default='0'),
        sa.Column('total_risks', sa.Integer(), server_default='0'),
        sa.Column('detected_patterns', postgresql.JSONB(), server_default='{}'),
        sa.Column('risks', postgresql.JSONB(), server_default='{}'),
        sa.Column('recommendations', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('regulations_analyzed', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('status', sa.String(50), server_default='completed', index=True),
        sa.Column('ai_enhanced', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'architecture_risk_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('review_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('repository', sa.String(500), nullable=False, index=True),
        sa.Column('risk_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('affected_files', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('remediation', sa.Text(), nullable=True),
        sa.Column('regulations', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('is_resolved', sa.Boolean(), server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Pending Legislation / Horizon Scanner ───────────────────────

    op.create_table(
        'pending_legislation',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text(), server_default=''),
        sa.Column('source', sa.String(50), server_default='custom'),
        sa.Column('source_url', sa.String(1000), server_default=''),
        sa.Column('jurisdiction', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('confidence', sa.String(20), server_default='medium'),
        sa.Column('expected_effective_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('frameworks_affected', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('tags', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'impact_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('legislation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pending_legislation.id'), nullable=False),
        sa.Column('affected_files', sa.Integer(), server_default='0'),
        sa.Column('affected_modules', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('estimated_effort_days', sa.Float(), server_default='0'),
        sa.Column('impact_severity', sa.String(20), server_default='medium'),
        sa.Column('recommendations', postgresql.JSONB(), server_default='[]'),
        sa.Column('confidence_score', sa.Float(), server_default='0'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Control Testing ─────────────────────────────────────────────

    op.create_table(
        'control_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('control_id', sa.String(50), nullable=False),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), server_default=''),
        sa.Column('test_type', sa.String(50), server_default='api_check'),
        sa.Column('frequency', sa.String(20), server_default='daily'),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        sa.Column('last_status', sa.String(20), server_default='pending'),
        sa.Column('consecutive_failures', sa.Integer(), server_default='0'),
        sa.Column('last_run', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'control_test_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('test_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('control_tests.id'), nullable=False),
        sa.Column('control_id', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), server_default=''),
        sa.Column('evidence_data', postgresql.JSONB(), server_default='{}'),
        sa.Column('duration_ms', sa.Float(), server_default='0'),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Entity Nodes ────────────────────────────────────────────────

    op.create_table(
        'entity_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entity_nodes.id'), nullable=True),
        sa.Column('level', sa.Integer(), server_default='0'),
        sa.Column('policy_mode', sa.String(20), server_default='inherit'),
        sa.Column('compliance_score', sa.Float(), server_default='0'),
        sa.Column('frameworks', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('member_count', sa.Integer(), server_default='0'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Board Reports ───────────────────────────────────────────────

    op.create_table(
        'board_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('period', sa.String(50), server_default=''),
        sa.Column('overall_score', sa.Float(), server_default='0'),
        sa.Column('overall_status', sa.String(20), server_default='yellow'),
        sa.Column('narrative', sa.Text(), server_default=''),
        sa.Column('framework_scores', postgresql.JSONB(), server_default='{}'),
        sa.Column('highlights', postgresql.JSONB(), server_default='[]'),
        sa.Column('top_risks', postgresql.JSONB(), server_default='[]'),
        sa.Column('action_items', postgresql.JSONB(), server_default='[]'),
        sa.Column('report_format', sa.String(20), server_default='html'),
        sa.Column('content', sa.Text(), server_default=''),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Audit Workspace ─────────────────────────────────────────────

    op.create_table(
        'audit_workspaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', sa.String(100), nullable=False),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('phase', sa.String(30), server_default='gap_analysis'),
        sa.Column('evidence_coverage_pct', sa.Float(), server_default='0'),
        sa.Column('remediation_progress_pct', sa.Float(), server_default='0'),
        sa.Column('target_audit_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'gap_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_workspaces.id'), nullable=False),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('total_controls', sa.Integer(), server_default='0'),
        sa.Column('fully_met', sa.Integer(), server_default='0'),
        sa.Column('partially_met', sa.Integer(), server_default='0'),
        sa.Column('not_met', sa.Integer(), server_default='0'),
        sa.Column('readiness_pct', sa.Float(), server_default='0'),
        sa.Column('estimated_remediation_days', sa.Float(), server_default='0'),
        sa.Column('gaps', postgresql.JSONB(), server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Dependency Scans ────────────────────────────────────────────

    op.create_table(
        'dependency_scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ecosystem', sa.String(20), nullable=False),
        sa.Column('total_dependencies', sa.Integer(), server_default='0'),
        sa.Column('critical_risks', sa.Integer(), server_default='0'),
        sa.Column('high_risks', sa.Integer(), server_default='0'),
        sa.Column('license_violations', sa.Integer(), server_default='0'),
        sa.Column('deprecated_crypto_count', sa.Integer(), server_default='0'),
        sa.Column('data_sharing_count', sa.Integer(), server_default='0'),
        sa.Column('risks', postgresql.JSONB(), server_default='[]'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Test Suite Runs / Generated Tests ───────────────────────────

    op.create_table(
        'test_suite_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('regulation', sa.String(100), nullable=False, index=True),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('repository', sa.String(500), nullable=True),
        sa.Column('total_tests', sa.Integer(), server_default='0'),
        sa.Column('passed', sa.Integer(), server_default='0'),
        sa.Column('failed', sa.Integer(), server_default='0'),
        sa.Column('skipped', sa.Integer(), server_default='0'),
        sa.Column('coverage_score', sa.Float(), server_default='0'),
        sa.Column('pattern_ids', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('generated_tests', postgresql.JSONB(), server_default='{}'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), server_default='completed', index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'generated_test_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('suite_run_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('regulation', sa.String(100), nullable=False, index=True),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('pattern_id', sa.String(200), nullable=False),
        sa.Column('test_name', sa.String(500), nullable=False),
        sa.Column('test_code', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.Column('validation_errors', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('ai_generated', sa.Boolean(), server_default='false'),
        sa.Column('ai_model', sa.String(100), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── SaaS Multi-Tenancy ──────────────────────────────────────────

    op.create_table(
        'saas_tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('plan', sa.String(50), server_default='free', index=True),
        sa.Column('status', sa.String(50), server_default='trial', index=True),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('domain', sa.String(255), nullable=True, unique=True),
        sa.Column('settings', postgresql.JSONB(), server_default='{}'),
        sa.Column('resource_limits', postgresql.JSONB(), server_default='{}'),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('github_installation_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'tenant_usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('saas_tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('metric', sa.String(100), nullable=False, index=True),
        sa.Column('value', sa.Float(), server_default='0'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('record_metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    tables = [
        'tenant_usage_records', 'saas_tenants',
        'generated_test_records', 'test_suite_runs',
        'dependency_scans',
        'gap_analyses', 'audit_workspaces',
        'board_reports',
        'entity_nodes',
        'control_test_results', 'control_tests',
        'impact_predictions', 'pending_legislation',
        'architecture_risk_records', 'architecture_reviews',
    ]
    for table in tables:
        op.drop_table(table)
