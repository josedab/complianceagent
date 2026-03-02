"""Add production features tables.

Revision ID: 004_production_features
Revises: 003_nextgen_features
Create Date: 2026-02-28

Tables for:
- GitHub Marketplace App (installs, check runs, webhook events)
- Knowledge Graph (nodes, edges)
- Regulatory Prediction (predictions, signals, activities)
- IaC Policy (scan results)
- Copilot Chat (sessions, messages)
- Client SDK (API keys, OAuth2 clients)
- Compliance Streaming (webhook integrations, alert policies)
- Cross-Org Benchmarking (submissions)
- Certification Autopilot (evidence, auditor sessions, readiness reports)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004_production_features'
down_revision: Union[str, None] = '003_nextgen_features'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── GitHub Marketplace App ───────────────────────────────────────

    op.create_table(
        'marketplace_installs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('github_id', sa.Integer(), unique=True, nullable=False),
        sa.Column('account', sa.String(200), nullable=False),
        sa.Column('account_type', sa.String(50), server_default='Organization'),
        sa.Column('plan', sa.String(50), server_default='free'),
        sa.Column('state', sa.String(50), server_default='active'),
        sa.Column('features_enabled', postgresql.JSONB(), server_default='[]'),
        sa.Column('repos', postgresql.JSONB(), server_default='[]'),
        sa.Column('repo_limit', sa.Integer(), server_default='3'),
        sa.Column('checks_run', sa.Integer(), server_default='0'),
        sa.Column('violations_found', sa.Integer(), server_default='0'),
        sa.Column('prs_analyzed', sa.Integer(), server_default='0'),
        sa.Column('stripe_customer_id', sa.String(100)),
        sa.Column('stripe_subscription_id', sa.String(100)),
        sa.Column('billing_interval', sa.String(20), server_default='monthly'),
        sa.Column('installed_at', sa.DateTime(timezone=True)),
        sa.Column('last_active_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_marketplace_installs_account', 'marketplace_installs', ['account'])

    op.create_table(
        'marketplace_check_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('install_id', postgresql.UUID(as_uuid=True)),
        sa.Column('repo', sa.String(300), nullable=False),
        sa.Column('pr_number', sa.Integer(), server_default='0'),
        sa.Column('sha', sa.String(64)),
        sa.Column('conclusion', sa.String(20), server_default='success'),
        sa.Column('violations', sa.Integer(), server_default='0'),
        sa.Column('frameworks', postgresql.JSONB(), server_default='[]'),
        sa.Column('annotations', postgresql.JSONB(), server_default='[]'),
        sa.Column('badge_grade', sa.String(5), server_default='B+'),
        sa.Column('duration_ms', sa.Float(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_check_runs_repo', 'marketplace_check_runs', ['repo'])

    op.create_table(
        'webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50)),
        sa.Column('delivery_id', sa.String(100)),
        sa.Column('payload', postgresql.JSONB(), server_default='{}'),
        sa.Column('processed', sa.Boolean(), server_default='false'),
        sa.Column('error', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Knowledge Graph ──────────────────────────────────────────────

    op.create_table(
        'knowledge_graph_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('graph_id', postgresql.UUID(as_uuid=True)),
        sa.Column('node_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), server_default=''),
        sa.Column('external_id', sa.String(200)),
        sa.Column('source', sa.String(100)),
        sa.Column('properties', postgresql.JSONB(), server_default='{}'),
        sa.Column('embedding_text', sa.Text(), server_default=''),
        sa.Column('group_name', sa.String(100)),
        sa.Column('color', sa.String(20)),
        sa.Column('size', sa.Float(), server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_kg_nodes_type', 'knowledge_graph_nodes', ['node_type'])
    op.create_index('ix_kg_nodes_graph', 'knowledge_graph_nodes', ['graph_id'])

    op.create_table(
        'knowledge_graph_edges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('graph_id', postgresql.UUID(as_uuid=True)),
        sa.Column('source_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relation_type', sa.String(50), nullable=False),
        sa.Column('weight', sa.Float(), server_default='1.0'),
        sa.Column('properties', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_kg_edges_source', 'knowledge_graph_edges', ['source_node_id'])
    op.create_index('ix_kg_edges_target', 'knowledge_graph_edges', ['target_node_id'])

    # ─── Regulatory Prediction ────────────────────────────────────────

    op.create_table(
        'reg_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('jurisdiction', sa.String(50), nullable=False),
        sa.Column('affected_frameworks', postgresql.JSONB(), server_default='[]'),
        sa.Column('confidence', sa.String(20), server_default='medium'),
        sa.Column('confidence_score', sa.Float(), server_default='0'),
        sa.Column('impact_severity', sa.String(20), server_default='moderate'),
        sa.Column('predicted_effective_date', sa.String(20)),
        sa.Column('prediction_horizon_months', sa.Integer(), server_default='6'),
        sa.Column('supporting_signals', postgresql.JSONB(), server_default='[]'),
        sa.Column('preparation_tasks', postgresql.JSONB(), server_default='[]'),
        sa.Column('status', sa.String(30), server_default='active'),
        sa.Column('momentum', sa.String(20), server_default='steady'),
        sa.Column('time_series', postgresql.JSONB(), server_default='[]'),
        sa.Column('feature_importance', postgresql.JSONB(), server_default='{}'),
        sa.Column('model_version', sa.String(20), server_default='v1.0'),
        sa.Column('predicted_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_reg_pred_jurisdiction', 'reg_predictions', ['jurisdiction'])

    op.create_table(
        'regulatory_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('signal_type', sa.String(30), nullable=False),
        sa.Column('source', sa.String(200)),
        sa.Column('jurisdiction', sa.String(50)),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text()),
        sa.Column('url', sa.String(1000)),
        sa.Column('relevance_score', sa.Float(), server_default='0'),
        sa.Column('entities', postgresql.JSONB(), server_default='[]'),
        sa.Column('topics', postgresql.JSONB(), server_default='[]'),
        sa.Column('sentiment', sa.Float(), server_default='0'),
        sa.Column('momentum', sa.String(20), server_default='steady'),
        sa.Column('detected_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'legislative_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('committee', sa.String(300), nullable=False),
        sa.Column('jurisdiction', sa.String(50), nullable=False),
        sa.Column('activity_type', sa.String(50)),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True)),
        sa.Column('related_bills', postgresql.JSONB(), server_default='[]'),
        sa.Column('outcome', sa.Text()),
        sa.Column('signal_strength', sa.Float(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── IaC Policy ───────────────────────────────────────────────────

    op.create_table(
        'iac_scan_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('iac_format', sa.String(30), server_default='terraform_hcl'),
        sa.Column('files_scanned', sa.Integer(), server_default='0'),
        sa.Column('resources_parsed', sa.Integer(), server_default='0'),
        sa.Column('pass_count', sa.Integer(), server_default='0'),
        sa.Column('fail_count', sa.Integer(), server_default='0'),
        sa.Column('scan_duration_ms', sa.Integer(), server_default='0'),
        sa.Column('auto_fixes_available', sa.Integer(), server_default='0'),
        sa.Column('violations', postgresql.JSONB(), server_default='[]'),
        sa.Column('sarif_output', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Copilot Chat ─────────────────────────────────────────────────

    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('user_id', sa.String(200)),
        sa.Column('persona', sa.String(30), server_default='cco'),
        sa.Column('context_regulations', postgresql.JSONB(), server_default='[]'),
        sa.Column('message_count', sa.Integer(), server_default='0'),
        sa.Column('last_active', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), server_default='user'),
        sa.Column('content', sa.Text()),
        sa.Column('citations', postgresql.JSONB(), server_default='[]'),
        sa.Column('guardrail_action', sa.String(30)),
        sa.Column('confidence_score', sa.Float(), server_default='1.0'),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_chat_messages_session', 'chat_messages', ['session_id'])

    # ─── Client SDK ───────────────────────────────────────────────────

    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key_prefix', sa.String(20), server_default='ca_live_'),
        sa.Column('key_hash', sa.String(64), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('tier', sa.String(20), server_default='free'),
        sa.Column('scopes', postgresql.JSONB(), server_default='["read"]'),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
        sa.Column('usage_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_api_keys_org', 'api_keys', ['organization_id'])

    op.create_table(
        'oauth2_clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', sa.String(100), unique=True, nullable=False),
        sa.Column('client_secret_hash', sa.String(64), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('redirect_uris', postgresql.JSONB(), server_default='[]'),
        sa.Column('scopes', postgresql.JSONB(), server_default='["read","write"]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Compliance Streaming ─────────────────────────────────────────

    op.create_table(
        'webhook_integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('target', sa.String(20), server_default='generic'),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('channels', postgresql.JSONB(), server_default='[]'),
        sa.Column('event_types', postgresql.JSONB(), server_default='[]'),
        sa.Column('min_severity', sa.String(20), server_default='medium'),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('secret', sa.String(64)),
        sa.Column('headers', postgresql.JSONB(), server_default='{}'),
        sa.Column('delivery_count', sa.Integer(), server_default='0'),
        sa.Column('failure_count', sa.Integer(), server_default='0'),
        sa.Column('last_delivery_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'alert_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('channel', sa.String(100)),
        sa.Column('condition_type', sa.String(30), server_default='threshold'),
        sa.Column('metric', sa.String(100)),
        sa.Column('operator', sa.String(10), server_default='lt'),
        sa.Column('threshold', sa.Float(), server_default='0'),
        sa.Column('window_seconds', sa.Integer(), server_default='300'),
        sa.Column('severity', sa.String(20), server_default='medium'),
        sa.Column('webhook_ids', postgresql.JSONB(), server_default='[]'),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('cooldown_seconds', sa.Integer(), server_default='3600'),
        sa.Column('fire_count', sa.Integer(), server_default='0'),
        sa.Column('last_fired_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ─── Cross-Org Benchmarking ───────────────────────────────────────

    op.create_table(
        'benchmark_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_hash', sa.String(64), nullable=False),
        sa.Column('industry', sa.String(50), nullable=False),
        sa.Column('company_size', sa.String(30), nullable=False),
        sa.Column('frameworks', postgresql.JSONB(), server_default='[]'),
        sa.Column('overall_score', sa.Float(), server_default='0'),
        sa.Column('noised_score', sa.Float(), server_default='0'),
        sa.Column('control_area_scores', postgresql.JSONB(), server_default='{}'),
        sa.Column('epsilon', sa.Float(), server_default='1.0'),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_bench_sub_industry', 'benchmark_submissions', ['industry'])

    # ─── Certification Autopilot ──────────────────────────────────────

    op.create_table(
        'auto_collected_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('control_id', sa.String(50), nullable=False),
        sa.Column('source_type', sa.String(30), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('content_hash', sa.String(64)),
        sa.Column('source_metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('status', sa.String(20), server_default='collected'),
        sa.Column('collected_at', sa.DateTime(timezone=True)),
        sa.Column('verified_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_evidence_framework', 'auto_collected_evidence', ['framework', 'control_id'])

    op.create_table(
        'auditor_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('auditor_name', sa.String(200), nullable=False),
        sa.Column('auditor_email', sa.String(300), nullable=False),
        sa.Column('auditor_firm', sa.String(200)),
        sa.Column('framework', sa.String(50), server_default='SOC2'),
        sa.Column('access_token_hash', sa.String(64), nullable=False),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('access_count', sa.Integer(), server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'certification_readiness_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('overall_readiness', sa.Float(), server_default='0'),
        sa.Column('auto_collection_rate', sa.Float(), server_default='0'),
        sa.Column('controls_met', sa.Integer(), server_default='0'),
        sa.Column('controls_total', sa.Integer(), server_default='0'),
        sa.Column('gap_summary', postgresql.JSONB(), server_default='{}'),
        sa.Column('remediation_priorities', postgresql.JSONB(), server_default='[]'),
        sa.Column('report_data', postgresql.JSONB(), server_default='{}'),
        sa.Column('generated_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    tables = [
        'certification_readiness_reports', 'auditor_sessions', 'auto_collected_evidence',
        'benchmark_submissions', 'alert_policies', 'webhook_integrations',
        'oauth2_clients', 'api_keys', 'chat_messages', 'chat_sessions',
        'iac_scan_results', 'legislative_activities', 'regulatory_signals',
        'reg_predictions', 'knowledge_graph_edges', 'knowledge_graph_nodes',
        'webhook_events', 'marketplace_check_runs', 'marketplace_installs',
    ]
    for table in tables:
        op.drop_table(table)
