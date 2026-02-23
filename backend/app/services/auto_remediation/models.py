"""Compliance Auto-Remediation models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class RemediationStatus(str, Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    FIX_GENERATED = "fix_generated"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    PR_CREATED = "pr_created"
    MERGED = "merged"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalPolicy(str, Enum):
    AUTO_MERGE = "auto_merge"
    SINGLE_APPROVAL = "single_approval"
    TEAM_APPROVAL = "team_approval"
    MANUAL_ONLY = "manual_only"


@dataclass
class RemediationPipeline:
    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    branch: str = "main"
    trigger_event: str = ""
    status: RemediationStatus = RemediationStatus.DETECTED
    risk_level: RiskLevel = RiskLevel.LOW
    approval_policy: ApprovalPolicy = ApprovalPolicy.SINGLE_APPROVAL
    violations_detected: int = 0
    fixes_generated: int = 0
    pr_url: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class RemediationFix:
    id: UUID = field(default_factory=uuid4)
    pipeline_id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    original_code: str = ""
    fixed_code: str = ""
    framework: str = ""
    rule_id: str = ""
    explanation: str = ""
    test_status: str = "pending"
    created_at: datetime | None = None


@dataclass
class ApprovalRequest:
    id: UUID = field(default_factory=uuid4)
    pipeline_id: UUID = field(default_factory=uuid4)
    approver: str = ""
    decision: str = "pending"
    comment: str = ""
    decided_at: datetime | None = None


@dataclass
class RemediationConfig:
    enabled: bool = True
    auto_merge_low_risk: bool = True
    approval_policy: ApprovalPolicy = ApprovalPolicy.SINGLE_APPROVAL
    scan_on_push: bool = True
    scan_on_schedule: bool = True
    schedule_cron: str = "0 */6 * * *"
    excluded_paths: list[str] = field(default_factory=list)
    target_frameworks: list[str] = field(default_factory=lambda: ["GDPR", "HIPAA", "PCI-DSS"])
    max_auto_fixes_per_run: int = 10


@dataclass
class RemediationStats:
    total_pipelines: int = 0
    by_status: dict[str, int] = field(default_factory=dict)
    total_fixes_generated: int = 0
    total_fixes_merged: int = 0
    avg_time_to_fix_hours: float = 0.0
    auto_merge_rate: float = 0.0
