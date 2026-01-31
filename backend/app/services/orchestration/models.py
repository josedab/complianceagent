"""Data models for Cross-Repository Compliance Orchestration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class PolicyType(str, Enum):
    """Types of compliance policies."""
    
    REQUIRED_REGULATION = "required_regulation"
    MINIMUM_SCORE = "minimum_score"
    BLOCKED_DEPENDENCIES = "blocked_dependencies"
    REQUIRED_CONTROLS = "required_controls"
    SCAN_FREQUENCY = "scan_frequency"
    EVIDENCE_REQUIREMENTS = "evidence_requirements"


class PolicyAction(str, Enum):
    """Actions for policy violations."""
    
    BLOCK = "block"
    WARN = "warn"
    NOTIFY = "notify"
    LOG = "log"


class RepositoryStatus(str, Enum):
    """Repository compliance status."""
    
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"
    SCANNING = "scanning"
    UNKNOWN = "unknown"


@dataclass
class CompliancePolicy:
    """A compliance policy for repositories."""
    
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    
    # Identity
    name: str = ""
    description: str = ""
    policy_type: PolicyType = PolicyType.MINIMUM_SCORE
    
    # Configuration
    config: dict[str, Any] = field(default_factory=dict)
    # Examples:
    # MINIMUM_SCORE: {"threshold": 0.8, "regulations": ["GDPR"]}
    # BLOCKED_DEPENDENCIES: {"packages": ["lodash < 4.0.0"]}
    # SCAN_FREQUENCY: {"interval_days": 7}
    
    # Actions
    on_violation: PolicyAction = PolicyAction.WARN
    notification_channels: list[str] = field(default_factory=list)
    
    # Scope
    applies_to: list[str] = field(default_factory=list)  # Repo patterns or "all"
    excludes: list[str] = field(default_factory=list)  # Excluded repos
    
    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""


@dataclass
class ManagedRepository:
    """A repository managed for compliance."""
    
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    
    # Identity
    name: str = ""  # repo name
    full_name: str = ""  # owner/repo
    url: str = ""
    default_branch: str = "main"
    
    # Compliance state
    status: RepositoryStatus = RepositoryStatus.UNKNOWN
    compliance_score: float = 0.0
    last_scan_at: datetime | None = None
    last_scan_id: UUID | None = None
    
    # Issues
    open_issues: int = 0
    critical_issues: int = 0
    
    # Policies
    applied_policies: list[UUID] = field(default_factory=list)
    policy_violations: list[dict[str, Any]] = field(default_factory=list)
    
    # Regulations
    tracked_regulations: list[str] = field(default_factory=list)
    
    # Metadata
    language: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyViolation:
    """A policy violation instance."""
    
    id: UUID = field(default_factory=uuid4)
    policy_id: UUID | None = None
    repository_id: UUID | None = None
    
    # Details
    policy_name: str = ""
    violation_type: str = ""
    message: str = ""
    severity: str = "medium"
    
    # Context
    details: dict[str, Any] = field(default_factory=dict)
    
    # Status
    status: str = "open"  # open, acknowledged, resolved, waived
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    waiver_reason: str | None = None
    
    # Metadata
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OrganizationDashboard:
    """Dashboard data for organization compliance."""
    
    organization_id: UUID
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Repository summary
    total_repositories: int = 0
    compliant_repositories: int = 0
    non_compliant_repositories: int = 0
    
    # Score summary
    average_score: float = 0.0
    lowest_score: float = 0.0
    highest_score: float = 0.0
    
    # Issues summary
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    
    # Policy summary
    active_policies: int = 0
    policy_violations: int = 0
    
    # By regulation
    by_regulation: dict[str, dict[str, Any]] = field(default_factory=dict)
    
    # Trends (last 30 days)
    score_trend: list[dict[str, Any]] = field(default_factory=list)
    issues_trend: list[dict[str, Any]] = field(default_factory=list)
    
    # Top issues
    top_repositories_by_risk: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class BatchScanResult:
    """Result of scanning multiple repositories."""
    
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    
    # Scope
    repositories_scanned: int = 0
    repositories_failed: int = 0
    
    # Results
    results: list[dict[str, Any]] = field(default_factory=list)
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    duration_seconds: float = 0.0


@dataclass
class InheritedPolicy:
    """Policy inheritance configuration."""
    
    parent_org_id: UUID
    child_org_id: UUID
    policies: list[UUID] = field(default_factory=list)  # Inherited policy IDs
    override_allowed: bool = False
    inherit_all: bool = True


# Default policy templates
DEFAULT_POLICY_TEMPLATES: dict[str, dict[str, Any]] = {
    "minimum_compliance_score": {
        "name": "Minimum Compliance Score",
        "description": "Require minimum compliance score for all repositories",
        "policy_type": PolicyType.MINIMUM_SCORE,
        "config": {"threshold": 0.7},
        "on_violation": PolicyAction.WARN,
    },
    "gdpr_required": {
        "name": "GDPR Compliance Required",
        "description": "All repositories must be GDPR compliant",
        "policy_type": PolicyType.REQUIRED_REGULATION,
        "config": {"regulations": ["GDPR"], "minimum_score": 0.8},
        "on_violation": PolicyAction.BLOCK,
    },
    "weekly_scans": {
        "name": "Weekly Compliance Scans",
        "description": "Repositories must be scanned weekly",
        "policy_type": PolicyType.SCAN_FREQUENCY,
        "config": {"interval_days": 7},
        "on_violation": PolicyAction.NOTIFY,
    },
    "no_vulnerable_deps": {
        "name": "No Vulnerable Dependencies",
        "description": "Block merges if critical vulnerabilities exist",
        "policy_type": PolicyType.BLOCKED_DEPENDENCIES,
        "config": {"block_critical": True, "block_high": False},
        "on_violation": PolicyAction.BLOCK,
    },
}
