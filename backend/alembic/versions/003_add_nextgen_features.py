"""Add next-gen features tables (Pattern Marketplace, Risk Quantification, IDE Agent)

Revision ID: 003_nextgen_features
Revises: 002_add_apac_esg_ai_frameworks
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_nextgen_features'
down_revision: Union[str, None] = '002_add_apac_esg_ai_frameworks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================================================
    # Pattern Marketplace Tables
    # ==========================================================================

    # Compliance patterns table
    op.create_table(
        'compliance_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('slug', sa.String(200), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('long_description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('pattern_type', sa.String(50), nullable=False, index=True),
        sa.Column('regulations', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('languages', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('tags', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('content', postgresql.JSONB(), default={}),
        sa.Column('current_version', sa.String(50), default='1.0.0'),
        sa.Column('publisher_org_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('publisher_name', sa.String(200), default=''),
        sa.Column('publisher_verified', sa.Boolean(), default=False),
        sa.Column('license_type', sa.String(50), default='free'),
        sa.Column('price', sa.Float(), default=0.0),
        sa.Column('price_type', sa.String(50), default='one_time'),
        sa.Column('status', sa.String(50), default='draft', index=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('downloads', sa.Integer(), default=0),
        sa.Column('active_users', sa.Integer(), default=0),
        sa.Column('avg_rating', sa.Float(), default=0.0),
        sa.Column('rating_count', sa.Integer(), default=0),
        sa.Column('fork_count', sa.Integer(), default=0),
        sa.Column('forked_from_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('compliance_patterns.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Pattern versions table
    op.create_table(
        'pattern_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pattern_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('compliance_patterns.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('content', postgresql.JSONB(), default={}),
        sa.Column('deprecated', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Pattern installations table
    op.create_table(
        'pattern_installations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pattern_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('compliance_patterns.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('installed_version', sa.String(50), nullable=False),
        sa.Column('auto_update', sa.Boolean(), default=True),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('custom_config', postgresql.JSONB(), default={}),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Pattern ratings table
    op.create_table(
        'pattern_ratings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pattern_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('compliance_patterns.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('review', sa.Text(), nullable=True),
        sa.Column('helpful_votes', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Pattern purchases table
    op.create_table(
        'pattern_purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pattern_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('compliance_patterns.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('price_paid', sa.Float(), nullable=False),
        sa.Column('license_type', sa.String(50), nullable=False),
        sa.Column('stripe_payment_id', sa.String(255), nullable=True),
        sa.Column('stripe_checkout_session_id', sa.String(255), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refunded', sa.Boolean(), default=False),
        sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Publisher profiles table
    op.create_table(
        'publisher_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('support_email', sa.String(255), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('verified', sa.Boolean(), default=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revenue_share_percent', sa.Float(), default=70.0),
        sa.Column('total_earnings', sa.Float(), default=0.0),
        sa.Column('pending_payout', sa.Float(), default=0.0),
        sa.Column('payout_method', sa.String(50), nullable=True),
        sa.Column('stripe_connect_account_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ==========================================================================
    # Risk Quantification Tables
    # ==========================================================================

    # Violation risks table
    op.create_table(
        'violation_risks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('violation_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('rule_id', sa.String(100), nullable=False, index=True),
        sa.Column('regulation', sa.String(100), nullable=False, index=True),
        sa.Column('severity', sa.String(50), default='medium', index=True),
        sa.Column('category', sa.String(50), default='regulatory_fine'),
        sa.Column('min_exposure', sa.Float(), default=0.0),
        sa.Column('max_exposure', sa.Float(), default=0.0),
        sa.Column('expected_exposure', sa.Float(), default=0.0, index=True),
        sa.Column('confidence', sa.Float(), default=0.5),
        sa.Column('likelihood', sa.Float(), default=0.5),
        sa.Column('impact_multiplier', sa.Float(), default=1.0),
        sa.Column('aggravating_factors', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('mitigating_factors', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('repositories.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('code_location', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('remediated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Repository risk profiles table
    op.create_table(
        'repository_risk_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('repository_name', sa.String(255), nullable=False),
        sa.Column('total_violations', sa.Integer(), default=0),
        sa.Column('critical_violations', sa.Integer(), default=0),
        sa.Column('high_violations', sa.Integer(), default=0),
        sa.Column('medium_violations', sa.Integer(), default=0),
        sa.Column('low_violations', sa.Integer(), default=0),
        sa.Column('total_min_exposure', sa.Float(), default=0.0),
        sa.Column('total_max_exposure', sa.Float(), default=0.0),
        sa.Column('total_expected_exposure', sa.Float(), default=0.0, index=True),
        sa.Column('exposure_by_regulation', postgresql.JSONB(), default={}),
        sa.Column('exposure_by_category', postgresql.JSONB(), default={}),
        sa.Column('overall_risk_score', sa.Float(), default=0.0, index=True),
        sa.Column('data_privacy_score', sa.Float(), default=100.0),
        sa.Column('security_score', sa.Float(), default=100.0),
        sa.Column('compliance_score', sa.Float(), default=100.0),
        sa.Column('assessment_version', sa.String(50), default='1.0'),
        sa.Column('last_full_scan_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Organization risk snapshots table
    op.create_table(
        'organization_risk_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('annual_revenue', sa.Float(), default=0.0),
        sa.Column('employee_count', sa.Integer(), default=0),
        sa.Column('data_subject_count', sa.Integer(), default=0),
        sa.Column('jurisdictions', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('total_min_exposure', sa.Float(), default=0.0),
        sa.Column('total_max_exposure', sa.Float(), default=0.0),
        sa.Column('total_expected_exposure', sa.Float(), default=0.0),
        sa.Column('exposure_by_regulation', postgresql.JSONB(), default={}),
        sa.Column('exposure_by_repository', postgresql.JSONB(), default={}),
        sa.Column('exposure_by_severity', postgresql.JSONB(), default={}),
        sa.Column('overall_risk_score', sa.Float(), default=0.0),
        sa.Column('risk_grade', sa.String(2), default='C'),
        sa.Column('risk_trend', sa.String(50), default='stable'),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Risk reports table
    op.create_table(
        'risk_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('report_type', sa.String(50), default='monthly'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('key_findings', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('key_recommendations', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('total_exposure', sa.Float(), default=0.0),
        sa.Column('exposure_change', sa.Float(), default=0.0),
        sa.Column('risk_score', sa.Float(), default=0.0),
        sa.Column('risk_grade', sa.String(2), default='C'),
        sa.Column('report_data', postgresql.JSONB(), default={}),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # What-if scenarios table
    op.create_table(
        'what_if_scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scenario_type', sa.String(50), nullable=False),
        sa.Column('parameters', postgresql.JSONB(), default={}),
        sa.Column('baseline_exposure', sa.Float(), default=0.0),
        sa.Column('scenario_exposure', sa.Float(), default=0.0),
        sa.Column('exposure_delta', sa.Float(), default=0.0),
        sa.Column('exposure_delta_percent', sa.Float(), default=0.0),
        sa.Column('affected_violations', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('affected_regulations', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(50), default='medium'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ==========================================================================
    # IDE Agent Tables
    # ==========================================================================

    # IDE agent sessions table
    op.create_table(
        'ide_agent_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('repositories.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('trigger_type', sa.String(50), default='manual', index=True),
        sa.Column('trigger_context', postgresql.JSONB(), default={}),
        sa.Column('status', sa.String(50), default='idle', index=True),
        sa.Column('current_step', sa.String(255), default=''),
        sa.Column('progress', sa.Float(), default=0.0),
        sa.Column('pending_approval_count', sa.Integer(), default=0),
        sa.Column('violations_found', sa.Integer(), default=0),
        sa.Column('fixes_applied', sa.Integer(), default=0),
        sa.Column('issues_created', sa.Integer(), default=0),
        sa.Column('prs_created', sa.Integer(), default=0),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # IDE agent actions table
    op.create_table(
        'ide_agent_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('ide_agent_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('action_type', sa.String(50), default='analyze'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('target_files', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('requires_approval', sa.Boolean(), default=True),
        sa.Column('approved', sa.Boolean(), default=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('executed', sa.Boolean(), default=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # IDE agent violations table
    op.create_table(
        'ide_agent_violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('ide_agent_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('rule_id', sa.String(100), nullable=False, index=True),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('regulation', sa.String(100), nullable=False, index=True),
        sa.Column('article_reference', sa.String(255), nullable=True),
        sa.Column('severity', sa.String(50), default='warning'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('start_line', sa.Integer(), nullable=False),
        sa.Column('end_line', sa.Integer(), nullable=False),
        sa.Column('start_column', sa.Integer(), default=0),
        sa.Column('end_column', sa.Integer(), default=0),
        sa.Column('original_code', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), default=0.5),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # IDE agent fixes table
    op.create_table(
        'ide_agent_fixes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('ide_agent_actions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('violation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('ide_agent_violations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('fixed_code', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('confidence', sa.String(50), default='medium'),
        sa.Column('confidence_score', sa.Float(), default=0.5),
        sa.Column('imports_to_add', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('files_affected', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('breaking_changes', sa.Boolean(), default=False),
        sa.Column('test_suggestions', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('applied', sa.Boolean(), default=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rollback_available', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # IDE agent configs table
    op.create_table(
        'ide_agent_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('enabled_triggers', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('auto_fix_enabled', sa.Boolean(), default=False),
        sa.Column('auto_fix_confidence_threshold', sa.Float(), default=0.9),
        sa.Column('auto_fix_max_files', sa.Integer(), default=5),
        sa.Column('require_approval_for_refactor', sa.Boolean(), default=True),
        sa.Column('require_approval_for_issues', sa.Boolean(), default=True),
        sa.Column('require_approval_for_prs', sa.Boolean(), default=True),
        sa.Column('enabled_regulations', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('excluded_paths', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('included_languages', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('notify_on_violations', sa.Boolean(), default=True),
        sa.Column('notify_on_auto_fix', sa.Boolean(), default=True),
        sa.Column('notification_channels', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    # Drop IDE Agent tables
    op.drop_table('ide_agent_configs')
    op.drop_table('ide_agent_fixes')
    op.drop_table('ide_agent_violations')
    op.drop_table('ide_agent_actions')
    op.drop_table('ide_agent_sessions')

    # Drop Risk Quantification tables
    op.drop_table('what_if_scenarios')
    op.drop_table('risk_reports')
    op.drop_table('organization_risk_snapshots')
    op.drop_table('repository_risk_profiles')
    op.drop_table('violation_risks')

    # Drop Pattern Marketplace tables
    op.drop_table('publisher_profiles')
    op.drop_table('pattern_purchases')
    op.drop_table('pattern_ratings')
    op.drop_table('pattern_installations')
    op.drop_table('pattern_versions')
    op.drop_table('compliance_patterns')
