"""Cross-Codebase Compliance Cloning models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class CloningStatus(str, Enum):
    """Status of a cloning operation."""

    ANALYZING = "analyzing"
    MATCHING = "matching"
    PLANNING = "planning"
    MIGRATING = "migrating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class PatternCategory(str, Enum):
    """Categories of compliance patterns."""

    ENCRYPTION = "encryption"
    AUTHENTICATION = "authentication"
    AUDIT_LOGGING = "audit_logging"
    DATA_MASKING = "data_masking"
    CONSENT_MANAGEMENT = "consent_management"
    ACCESS_CONTROL = "access_control"
    DATA_RETENTION = "data_retention"
    BREACH_NOTIFICATION = "breach_notification"


@dataclass
class RepoFingerprint:
    """Fingerprint of a repository's tech stack and compliance patterns."""

    repo_url: str
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    cloud_providers: list[str] = field(default_factory=list)
    compliance_patterns: list[str] = field(default_factory=list)
    compliance_score: float = 0.0
    similarity_score: float = 0.0


@dataclass
class ComplianceGap:
    """A gap between target and reference repo compliance."""

    id: str
    category: PatternCategory
    description: str
    severity: str = "medium"
    reference_implementation: str = ""
    suggested_fix: str = ""
    estimated_effort_hours: float = 2.0
    files_affected: list[str] = field(default_factory=list)


@dataclass
class MigrationPlan:
    """A migration plan for cloning compliance from reference to target."""

    id: UUID
    source_repo: str
    target_repo: str
    status: CloningStatus = CloningStatus.ANALYZING
    total_gaps: int = 0
    gaps_resolved: int = 0
    gaps: list[ComplianceGap] = field(default_factory=list)
    estimated_total_hours: float = 0.0
    compliance_score_before: float = 0.0
    compliance_score_after: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ReferenceRepo:
    """A curated reference repository for compliance cloning."""

    id: str
    name: str
    url: str
    description: str
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    compliance_score: float = 0.0
    patterns_count: int = 0
    industry: str = ""
    verified: bool = False
