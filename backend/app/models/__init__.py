"""Database models."""

# Critical Persistence models
# Architecture Review models
from app.models.architecture_review import (
    ArchitectureReview,
    ArchitectureRiskRecord,
)
from app.models.audit import AuditTrail, ComplianceAction
from app.models.base import TimestampMixin, UUIDMixin
from app.models.codebase import CodebaseMapping, Repository
from app.models.critical_persistence import (
    CertControlGapRecord,
    CertificationRunRecord,
    EvidenceGenerationRecord,
    RemediationApprovalRecord,
    RemediationFixRecord,
    RemediationPipelineRecord,
)
from app.models.customer_profile import CustomerProfile

# IDE Agent models
from app.models.ide_agent import (
    IDEAgentAction,
    IDEAgentConfig,
    IDEAgentFix,
    IDEAgentSession,
    IDEAgentViolation,
)
from app.models.ide_learning import IDERuleEventRecord, TeamSuppressionRecord

# Notification models
from app.models.notification import NotificationRecord
from app.models.organization import Organization, OrganizationMember

# Pattern Marketplace models
from app.models.pattern_marketplace import (
    CompliancePattern,
    PatternInstallation,
    PatternPurchase,
    PatternRating,
    PatternVersion,
    PublisherProfile,
)

# Production Features models
from app.models.production_features import (
    AlertPolicyRecord,
    APIKeyRecord,
    AuditorSessionRecord,
    AutoCollectedEvidenceRecord,
    BenchmarkSubmissionRecord,
    CertificationReadinessRecord,
    ChatMessageRecord,
    ChatSessionRecord,
    IaCScanResultRecord,
    KnowledgeGraphEdgeRecord,
    KnowledgeGraphNodeRecord,
    LegislativeActivityRecord,
    MarketplaceCheckRunRecord,
    MarketplaceInstallRecord,
    NotificationPreferenceRecord,
    OAuth2ClientRecord,
    RegPredictionRecord,
    RegulatorySignalRecord,
    WebhookEventRecord,
    WebhookIntegrationRecord,
)
from app.models.regulation import Regulation, RegulatorySource
from app.models.requirement import Requirement

# Risk Quantification models
from app.models.risk_quantification import (
    OrganizationRiskSnapshot,
    RepositoryRiskProfile,
    RiskReport,
    ViolationRisk,
    WhatIfScenario,
)

# SaaS Tenant models
from app.models.saas_tenant import (
    SaasTenant,
    TenantUsageRecord,
)

# Secondary Persistence models
from app.models.secondary_persistence import (
    DriftAlertRecord,
    DriftBaselineRecord,
    DriftEventRecord,
    EvidenceVaultRecord,
    MCPExecutionRecord,
    PostureScoreRecord,
    SelfHealingEventRecord,
)

# Strategic Features models
from app.models.strategic_features import (
    AuditWorkspaceRecord,
    BoardReportRecord,
    ControlTestRecord,
    ControlTestResultRecord,
    DependencyScanRecord,
    EntityNodeRecord,
    GapAnalysisRecord,
    ImpactPredictionRecord,
    PendingLegislationRecord,
)

# Testing models
from app.models.testing import (
    GeneratedTestRecord,
    TestSuiteRun,
)
from app.models.user import User

# User State models
from app.models.user_state import (
    AgentMarketplaceRecord,
    CopilotSessionRecord,
    GamificationEventRecord,
    GamificationProfileRecord,
    TrustAttestationRecord,
    WorkflowDefinitionRecord,
    WorkflowExecutionRecord,
)


__all__ = [  # noqa: RUF022 - grouped by domain for discoverability
    # Critical Persistence
    "CertControlGapRecord",
    "CertificationRunRecord",
    "EvidenceGenerationRecord",
    "RemediationApprovalRecord",
    "RemediationFixRecord",
    "RemediationPipelineRecord",
    # Notification
    "NotificationRecord",
    # Secondary Persistence
    "DriftAlertRecord",
    "DriftBaselineRecord",
    "DriftEventRecord",
    "EvidenceVaultRecord",
    "MCPExecutionRecord",
    "PostureScoreRecord",
    "SelfHealingEventRecord",
    # User State
    "AgentMarketplaceRecord",
    "CopilotSessionRecord",
    "GamificationEventRecord",
    "GamificationProfileRecord",
    "TrustAttestationRecord",
    "WorkflowDefinitionRecord",
    "WorkflowExecutionRecord",
    # Architecture Review
    "ArchitectureReview",
    "ArchitectureRiskRecord",
    # Core models
    "AuditTrail",
    # Strategic Features
    "AuditWorkspaceRecord",
    "BoardReportRecord",
    "CodebaseMapping",
    "ComplianceAction",
    # Pattern Marketplace
    "CompliancePattern",
    "ControlTestRecord",
    "ControlTestResultRecord",
    "CustomerProfile",
    "DependencyScanRecord",
    "EntityNodeRecord",
    "GapAnalysisRecord",
    # Testing
    "GeneratedTestRecord",
    "IDEAgentAction",
    "IDEAgentConfig",
    "IDEAgentFix",
    # IDE Agent
    "IDEAgentSession",
    "IDEAgentViolation",
    "IDERuleEventRecord",
    "ImpactPredictionRecord",
    "Organization",
    "OrganizationMember",
    "OrganizationRiskSnapshot",
    "PatternInstallation",
    "PatternPurchase",
    "PatternRating",
    "PatternVersion",
    "PendingLegislationRecord",
    "PublisherProfile",
    "Regulation",
    "RegulatorySource",
    "Repository",
    "RepositoryRiskProfile",
    "Requirement",
    "RiskReport",
    # SaaS Tenant
    "SaasTenant",
    "TenantUsageRecord",
    "TeamSuppressionRecord",
    "TestSuiteRun",
    # Base
    "TimestampMixin",
    "UUIDMixin",
    "User",
    # Risk Quantification
    "ViolationRisk",
    "WhatIfScenario",
    # Production Features
    "AlertPolicyRecord",
    "APIKeyRecord",
    "AuditorSessionRecord",
    "AutoCollectedEvidenceRecord",
    "BenchmarkSubmissionRecord",
    "CertificationReadinessRecord",
    "ChatMessageRecord",
    "ChatSessionRecord",
    "IaCScanResultRecord",
    "KnowledgeGraphEdgeRecord",
    "KnowledgeGraphNodeRecord",
    "LegislativeActivityRecord",
    "MarketplaceCheckRunRecord",
    "MarketplaceInstallRecord",
    "NotificationPreferenceRecord",
    "OAuth2ClientRecord",
    "RegPredictionRecord",
    "RegulatorySignalRecord",
    "WebhookEventRecord",
    "WebhookIntegrationRecord",
]
