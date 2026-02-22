"""Database models."""

# Architecture Review models
from app.models.architecture_review import (
    ArchitectureReview,
    ArchitectureRiskRecord,
)
from app.models.audit import AuditTrail, ComplianceAction
from app.models.base import TimestampMixin, UUIDMixin
from app.models.codebase import CodebaseMapping, Repository
from app.models.customer_profile import CustomerProfile

# IDE Agent models
from app.models.ide_agent import (
    IDEAgentAction,
    IDEAgentConfig,
    IDEAgentFix,
    IDEAgentSession,
    IDEAgentViolation,
)
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


__all__ = [
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
    "TestSuiteRun",
    # Base
    "TimestampMixin",
    "UUIDMixin",
    "User",
    # Risk Quantification
    "ViolationRisk",
    "WhatIfScenario",
]
