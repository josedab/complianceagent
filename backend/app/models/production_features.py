"""Database models for production feature services.

Provides persistent storage for:
- GitHub Marketplace App (installations, check runs, billing)
- Compliance Knowledge Graph (nodes, edges, embeddings)
- Regulatory Prediction Engine (predictions, signals, activities)
- IaC Policy Engine (scan results, violations, remediation PRs)
- Compliance Digital Twin (scenarios, simulation results, cost estimates)
- Copilot Chat (sessions, messages, RAG chunks)
- Client SDK (API keys, OAuth2 clients, rate limit records)
- Compliance Streaming (webhook integrations, alert policies, alert firings)
- Cross-Org Benchmarking (submissions, peer groups, rankings)
- Certification Autopilot (evidence records, auditor sessions, readiness reports)
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


# ─── GitHub Marketplace App ───────────────────────────────────────────────


class MarketplaceInstallRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent GitHub App installation."""

    __tablename__ = "marketplace_installs"

    github_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    account: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), default="Organization")
    plan: Mapped[str] = mapped_column(String(50), default="free")
    state: Mapped[str] = mapped_column(String(50), default="active")
    features_enabled: Mapped[list] = mapped_column(ArrayType(), default=list)
    repos: Mapped[list] = mapped_column(ArrayType(), default=list)
    repo_limit: Mapped[int] = mapped_column(Integer, default=3)
    checks_run: Mapped[int] = mapped_column(Integer, default=0)
    violations_found: Mapped[int] = mapped_column(Integer, default=0)
    prs_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(100))
    billing_interval: Mapped[str] = mapped_column(String(20), default="monthly")
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MarketplaceCheckRunRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent compliance check run on a PR."""

    __tablename__ = "marketplace_check_runs"

    install_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    repo: Mapped[str] = mapped_column(String(300), nullable=False)
    pr_number: Mapped[int] = mapped_column(Integer, default=0)
    sha: Mapped[str] = mapped_column(String(64), default="")
    conclusion: Mapped[str] = mapped_column(String(20), default="success")
    violations: Mapped[int] = mapped_column(Integer, default=0)
    frameworks: Mapped[list] = mapped_column(ArrayType(), default=list)
    annotations: Mapped[dict] = mapped_column(JSONBType, default=list)
    badge_grade: Mapped[str] = mapped_column(String(5), default="B+")
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)


class WebhookEventRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent webhook event log."""

    __tablename__ = "webhook_events"

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), default="")
    delivery_id: Mapped[str] = mapped_column(String(100), default="")
    payload: Mapped[dict] = mapped_column(JSONBType, default=dict)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text)


# ─── Knowledge Graph ──────────────────────────────────────────────────────


class KnowledgeGraphNodeRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent knowledge graph node with pgvector embedding."""

    __tablename__ = "knowledge_graph_nodes"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    graph_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    external_id: Mapped[str] = mapped_column(String(200), default="")
    source: Mapped[str] = mapped_column(String(100), default="")
    properties: Mapped[dict] = mapped_column(JSONBType, default=dict)
    embedding_text: Mapped[str] = mapped_column(Text, default="")
    # In production: embedding = mapped_column(Vector(384)) with pgvector
    group_name: Mapped[str] = mapped_column(String(100), default="")
    color: Mapped[str] = mapped_column(String(20), default="")
    size: Mapped[float] = mapped_column(Float, default=1.0)


class KnowledgeGraphEdgeRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent knowledge graph edge."""

    __tablename__ = "knowledge_graph_edges"

    graph_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    source_node_id: Mapped[uuid.UUID] = mapped_column(UUIDType, nullable=False)
    target_node_id: Mapped[uuid.UUID] = mapped_column(UUIDType, nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    properties: Mapped[dict] = mapped_column(JSONBType, default=dict)


# ─── Regulatory Prediction Engine ─────────────────────────────────────────


class RegPredictionRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent regulatory prediction."""

    __tablename__ = "reg_predictions"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    jurisdiction: Mapped[str] = mapped_column(String(50), nullable=False)
    affected_frameworks: Mapped[list] = mapped_column(ArrayType(), default=list)
    confidence: Mapped[str] = mapped_column(String(20), default="medium")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    impact_severity: Mapped[str] = mapped_column(String(20), default="moderate")
    predicted_effective_date: Mapped[str] = mapped_column(String(20), default="")
    prediction_horizon_months: Mapped[int] = mapped_column(Integer, default=6)
    supporting_signals: Mapped[list] = mapped_column(ArrayType(), default=list)
    preparation_tasks: Mapped[dict] = mapped_column(JSONBType, default=list)
    status: Mapped[str] = mapped_column(String(30), default="active")
    momentum: Mapped[str] = mapped_column(String(20), default="steady")
    time_series: Mapped[dict] = mapped_column(JSONBType, default=list)
    feature_importance: Mapped[dict] = mapped_column(JSONBType, default=dict)
    model_version: Mapped[str] = mapped_column(String(20), default="v1.0")
    predicted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RegulatorySignalRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent regulatory signal."""

    __tablename__ = "regulatory_signals"

    signal_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str] = mapped_column(String(200), default="")
    jurisdiction: Mapped[str] = mapped_column(String(50), default="")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(1000), default="")
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    entities: Mapped[list] = mapped_column(ArrayType(), default=list)
    topics: Mapped[list] = mapped_column(ArrayType(), default=list)
    sentiment: Mapped[float] = mapped_column(Float, default=0.0)
    momentum: Mapped[str] = mapped_column(String(20), default="steady")
    detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LegislativeActivityRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent legislative committee activity."""

    __tablename__ = "legislative_activities"

    committee: Mapped[str] = mapped_column(String(300), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(50), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(50), default="")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    related_bills: Mapped[list] = mapped_column(ArrayType(), default=list)
    outcome: Mapped[str] = mapped_column(Text, default="")
    signal_strength: Mapped[float] = mapped_column(Float, default=0.0)


# ─── IaC Policy Engine ────────────────────────────────────────────────────


class IaCScanResultRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent IaC scan result."""

    __tablename__ = "iac_scan_results"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    iac_format: Mapped[str] = mapped_column(String(30), default="terraform_hcl")
    files_scanned: Mapped[int] = mapped_column(Integer, default=0)
    resources_parsed: Mapped[int] = mapped_column(Integer, default=0)
    pass_count: Mapped[int] = mapped_column(Integer, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    scan_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    auto_fixes_available: Mapped[int] = mapped_column(Integer, default=0)
    violations: Mapped[dict] = mapped_column(JSONBType, default=list)
    sarif_output: Mapped[dict] = mapped_column(JSONBType, default=dict)


# ─── Copilot Chat ─────────────────────────────────────────────────────────


class ChatSessionRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent chat session."""

    __tablename__ = "chat_sessions"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    user_id: Mapped[str] = mapped_column(String(200), default="")
    persona: Mapped[str] = mapped_column(String(30), default="cco")
    context_regulations: Mapped[list] = mapped_column(ArrayType(), default=list)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChatMessageRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent chat message."""

    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(UUIDType, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")
    content: Mapped[str] = mapped_column(Text, default="")
    citations: Mapped[dict] = mapped_column(JSONBType, default=list)
    guardrail_action: Mapped[str | None] = mapped_column(String(30))
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    message_metadata: Mapped[dict] = mapped_column("metadata", JSONBType, default=dict)


# ─── Client SDK ───────────────────────────────────────────────────────────


class APIKeyRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent API key."""

    __tablename__ = "api_keys"

    key_prefix: Mapped[str] = mapped_column(String(20), default="ca_live_")
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    status: Mapped[str] = mapped_column(String(20), default="active")
    tier: Mapped[str] = mapped_column(String(20), default="free")
    scopes: Mapped[list] = mapped_column(ArrayType(), default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(Integer, default=0)


class OAuth2ClientRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent OAuth2 client registration."""

    __tablename__ = "oauth2_clients"

    client_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    client_secret_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    redirect_uris: Mapped[list] = mapped_column(ArrayType(), default=list)
    scopes: Mapped[list] = mapped_column(ArrayType(), default=list)


# ─── Compliance Streaming ─────────────────────────────────────────────────


class WebhookIntegrationRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent webhook integration for event delivery."""

    __tablename__ = "webhook_integrations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    target: Mapped[str] = mapped_column(String(20), default="generic")
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    channels: Mapped[list] = mapped_column(ArrayType(), default=list)
    event_types: Mapped[list] = mapped_column(ArrayType(), default=list)
    min_severity: Mapped[str] = mapped_column(String(20), default="medium")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    secret: Mapped[str] = mapped_column(String(64), default="")
    headers: Mapped[dict] = mapped_column(JSONBType, default=dict)
    delivery_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AlertPolicyRecord(Base, UUIDMixin, TimestampMixin):
    """Persistent alert policy."""

    __tablename__ = "alert_policies"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel: Mapped[str] = mapped_column(String(100), default="")
    condition_type: Mapped[str] = mapped_column(String(30), default="threshold")
    metric: Mapped[str] = mapped_column(String(100), default="")
    operator: Mapped[str] = mapped_column(String(10), default="lt")
    threshold: Mapped[float] = mapped_column(Float, default=0.0)
    window_seconds: Mapped[int] = mapped_column(Integer, default=300)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    webhook_ids: Mapped[list] = mapped_column(ArrayType(), default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=3600)
    fire_count: Mapped[int] = mapped_column(Integer, default=0)
    last_fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ─── Cross-Org Benchmarking ───────────────────────────────────────────────


class BenchmarkSubmissionRecord(Base, UUIDMixin, TimestampMixin):
    """Anonymized benchmark data submission."""

    __tablename__ = "benchmark_submissions"

    organization_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    industry: Mapped[str] = mapped_column(String(50), nullable=False)
    company_size: Mapped[str] = mapped_column(String(30), nullable=False)
    frameworks: Mapped[list] = mapped_column(ArrayType(), default=list)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    noised_score: Mapped[float] = mapped_column(Float, default=0.0)
    control_area_scores: Mapped[dict] = mapped_column(JSONBType, default=dict)
    epsilon: Mapped[float] = mapped_column(Float, default=1.0)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ─── Certification Autopilot ──────────────────────────────────────────────


class AutoCollectedEvidenceRecord(Base, UUIDMixin, TimestampMixin):
    """Auto-collected evidence for certification."""

    __tablename__ = "auto_collected_evidence"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    control_id: Mapped[str] = mapped_column(String(50), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    source_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="collected")
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditorSessionRecord(Base, UUIDMixin, TimestampMixin):
    """Read-only auditor portal session."""

    __tablename__ = "auditor_sessions"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    auditor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    auditor_email: Mapped[str] = mapped_column(String(300), nullable=False)
    auditor_firm: Mapped[str] = mapped_column(String(200), default="")
    framework: Mapped[str] = mapped_column(String(50), default="SOC2")
    access_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CertificationReadinessRecord(Base, UUIDMixin, TimestampMixin):
    """Generated certification readiness report."""

    __tablename__ = "certification_readiness_reports"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    overall_readiness: Mapped[float] = mapped_column(Float, default=0.0)
    auto_collection_rate: Mapped[float] = mapped_column(Float, default=0.0)
    controls_met: Mapped[int] = mapped_column(Integer, default=0)
    controls_total: Mapped[int] = mapped_column(Integer, default=0)
    gap_summary: Mapped[dict] = mapped_column(JSONBType, default=dict)
    remediation_priorities: Mapped[dict] = mapped_column(JSONBType, default=list)
    report_data: Mapped[dict] = mapped_column(JSONBType, default=dict)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ─── Notification Preferences ─────────────────────────────────────────────


class NotificationPreferenceRecord(Base, UUIDMixin, TimestampMixin):
    """User notification preferences."""

    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, unique=True, nullable=False, index=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_digest: Mapped[str] = mapped_column(String(20), default="daily")
    slack_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    slack_webhook_url: Mapped[str | None] = mapped_column(String(500))
    webhook_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_url: Mapped[str | None] = mapped_column(String(2048))
