"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('oauth_provider', sa.String(50), nullable=True),
        sa.Column('oauth_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verification_token', sa.String(255), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('plan', sa.String(50), default='trial'),
        sa.Column('settings', postgresql.JSONB(), default={}),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('max_repositories', sa.Integer(), default=1),
        sa.Column('max_frameworks', sa.Integer(), default=3),
        sa.Column('max_users', sa.Integer(), default=5),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Organization members table
    op.create_table(
        'organization_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), default='member'),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Regulatory sources table
    op.create_table(
        'regulatory_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('jurisdiction', sa.String(50), nullable=False),
        sa.Column('framework', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('check_interval_hours', sa.Integer(), default=24),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_change_detected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_content_hash', sa.String(64), nullable=True),
        sa.Column('last_etag', sa.String(255), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), default=0),
        sa.Column('total_checks', sa.Integer(), default=0),
        sa.Column('successful_checks', sa.Integer(), default=0),
        sa.Column('parser_type', sa.String(50), default='html'),
        sa.Column('parser_config', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Regulations table
    op.create_table(
        'regulations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('regulatory_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('short_name', sa.String(100), nullable=True),
        sa.Column('official_reference', sa.String(255), nullable=True),
        sa.Column('jurisdiction', sa.String(50), nullable=False, index=True),
        sa.Column('framework', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(50), default='effective'),
        sa.Column('published_date', sa.Date(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True, index=True),
        sa.Column('enforcement_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('content_summary', sa.Text(), nullable=True),
        sa.Column('full_text_s3_key', sa.String(500), nullable=True),
        sa.Column('change_type', sa.String(50), nullable=True),
        sa.Column('parent_regulation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('regulations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('is_parsed', sa.Boolean(), default=False),
        sa.Column('parsed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parsing_confidence', sa.Float(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Requirements table
    op.create_table(
        'requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('regulation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('regulations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('reference_id', sa.String(100), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('obligation_type', sa.String(20), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('object', sa.Text(), nullable=True),
        sa.Column('data_types', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('processes', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('systems', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('roles', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('timeframe', sa.String(255), nullable=True),
        sa.Column('deadline_days', sa.Integer(), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('citations', postgresql.JSONB(), default=[]),
        sa.Column('penalty_description', sa.Text(), nullable=True),
        sa.Column('max_penalty_amount', sa.Float(), nullable=True),
        sa.Column('penalty_currency', sa.String(3), nullable=True),
        sa.Column('extraction_confidence', sa.Float(), default=0.0),
        sa.Column('extracted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('human_reviewed', sa.Boolean(), default=False),
        sa.Column('reviewed_by', sa.String(255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('related_requirement_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('tags', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Customer profiles table
    op.create_table(
        'customer_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('industry', sa.String(100), nullable=False),
        sa.Column('sub_industry', sa.String(100), nullable=True),
        sa.Column('company_size', sa.String(50), nullable=True),
        sa.Column('is_publicly_traded', sa.Boolean(), default=False),
        sa.Column('headquarters_jurisdiction', sa.String(50), nullable=True),
        sa.Column('operating_jurisdictions', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('customer_jurisdictions', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('data_types_processed', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('sensitive_data_categories', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('processes_pii', sa.Boolean(), default=False),
        sa.Column('processes_health_data', sa.Boolean(), default=False),
        sa.Column('processes_financial_data', sa.Boolean(), default=False),
        sa.Column('processes_children_data', sa.Boolean(), default=False),
        sa.Column('uses_ai_ml', sa.Boolean(), default=False),
        sa.Column('ai_use_cases', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('ai_risk_level', sa.String(50), nullable=True),
        sa.Column('applicable_frameworks', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('excluded_frameworks', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('current_certifications', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('target_certifications', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('business_processes', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('third_party_vendors', postgresql.JSONB(), default=[]),
        sa.Column('custom_requirements', postgresql.JSONB(), default=[]),
        sa.Column('settings', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Repositories table
    op.create_table(
        'repositories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customer_profiles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('owner', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(512), nullable=False, index=True),
        sa.Column('default_branch', sa.String(255), default='main'),
        sa.Column('clone_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('access_token_encrypted', sa.Text(), nullable=True),
        sa.Column('installation_id', sa.String(255), nullable=True),
        sa.Column('last_analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_analyzed_commit', sa.String(40), nullable=True),
        sa.Column('analysis_status', sa.String(50), default='pending'),
        sa.Column('primary_language', sa.String(50), nullable=True),
        sa.Column('languages', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('file_count', sa.Integer(), nullable=True),
        sa.Column('line_count', sa.Integer(), nullable=True),
        sa.Column('structure_cache', postgresql.JSONB(), default={}),
        sa.Column('structure_cached_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('compliance_score', sa.Float(), nullable=True),
        sa.Column('total_requirements', sa.Integer(), default=0),
        sa.Column('compliant_requirements', sa.Integer(), default=0),
        sa.Column('gaps_critical', sa.Integer(), default=0),
        sa.Column('gaps_major', sa.Integer(), default=0),
        sa.Column('gaps_minor', sa.Integer(), default=0),
        sa.Column('settings', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Codebase mappings table
    op.create_table(
        'codebase_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requirements.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('compliance_status', sa.String(50), default='pending_review'),
        sa.Column('compliance_notes', sa.Text(), nullable=True),
        sa.Column('affected_files', postgresql.JSONB(), default=[]),
        sa.Column('affected_functions', postgresql.JSONB(), default=[]),
        sa.Column('affected_classes', postgresql.JSONB(), default=[]),
        sa.Column('data_flows', postgresql.JSONB(), default=[]),
        sa.Column('existing_implementations', postgresql.JSONB(), default=[]),
        sa.Column('gaps', postgresql.JSONB(), default=[]),
        sa.Column('gap_count', sa.Integer(), default=0),
        sa.Column('critical_gaps', sa.Integer(), default=0),
        sa.Column('major_gaps', sa.Integer(), default=0),
        sa.Column('minor_gaps', sa.Integer(), default=0),
        sa.Column('estimated_effort_hours', sa.Float(), nullable=True),
        sa.Column('estimated_effort_description', sa.Text(), nullable=True),
        sa.Column('risk_level', sa.String(50), nullable=True),
        sa.Column('mapping_confidence', sa.Float(), default=0.0),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('analyzed_commit', sa.String(40), nullable=True),
        sa.Column('human_reviewed', sa.Boolean(), default=False),
        sa.Column('reviewed_by', sa.String(255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('implementation_pr_url', sa.Text(), nullable=True),
        sa.Column('implementation_pr_status', sa.String(50), nullable=True),
        sa.Column('implemented_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Compliance actions table
    op.create_table(
        'compliance_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('regulation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('regulations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requirements.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mapping_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('codebase_mappings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), default='pending', index=True),
        sa.Column('priority', sa.String(50), default='medium'),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('impact_summary', sa.Text(), nullable=True),
        sa.Column('affected_files_count', sa.Integer(), default=0),
        sa.Column('estimated_effort_hours', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.String(50), nullable=True),
        sa.Column('generated_code', postgresql.JSONB(), nullable=True),
        sa.Column('generated_tests', postgresql.JSONB(), nullable=True),
        sa.Column('pr_url', sa.Text(), nullable=True),
        sa.Column('pr_number', sa.Integer(), nullable=True),
        sa.Column('pr_status', sa.String(50), nullable=True),
        sa.Column('pr_created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pr_merged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_status', sa.String(50), nullable=True),
        sa.Column('verification_results', postgresql.JSONB(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Audit trails table
    op.create_table(
        'audit_trails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('regulation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('regulations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requirements.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('repositories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('mapping_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('codebase_mappings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('compliance_action_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('compliance_actions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False, index=True),
        sa.Column('event_description', sa.Text(), nullable=False),
        sa.Column('event_data', postgresql.JSONB(), default={}),
        sa.Column('actor_type', sa.String(50), nullable=False),
        sa.Column('actor_id', sa.String(255), nullable=True),
        sa.Column('actor_email', sa.String(255), nullable=True),
        sa.Column('ai_model', sa.String(100), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('previous_hash', sa.String(64), nullable=True),
        sa.Column('entry_hash', sa.String(64), nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('audit_trails')
    op.drop_table('compliance_actions')
    op.drop_table('codebase_mappings')
    op.drop_table('repositories')
    op.drop_table('customer_profiles')
    op.drop_table('requirements')
    op.drop_table('regulations')
    op.drop_table('regulatory_sources')
    op.drop_table('organization_members')
    op.drop_table('organizations')
    op.drop_table('users')
