"""Data models for Agentic Compliance Autopilot."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RemediationStatus(str, Enum):
    """Status of a remediation action."""
    
    PENDING = "pending"
    ANALYZING = "analyzing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class RemediationPriority(str, Enum):
    """Priority level for remediation."""
    
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Within 24 hours
    MEDIUM = "medium"  # Within 1 week
    LOW = "low"  # Within 30 days


class RemediationType(str, Enum):
    """Type of remediation action."""
    
    CODE_FIX = "code_fix"
    CONFIG_CHANGE = "config_change"
    DOCUMENTATION = "documentation"
    POLICY_UPDATE = "policy_update"
    ACCESS_CONTROL = "access_control"
    ENCRYPTION = "encryption"
    LOGGING = "logging"
    DATA_HANDLING = "data_handling"
    DEPENDENCY_UPDATE = "dependency_update"
    INFRASTRUCTURE = "infrastructure"


class ApprovalStatus(str, Enum):
    """Approval status for remediation."""
    
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ComplianceViolation(BaseModel):
    """A compliance violation that needs remediation."""
    
    id: UUID = Field(default_factory=uuid4)
    
    # Violation details
    rule_id: str
    rule_name: str
    regulation: str
    requirement: str | None = None
    article: str | None = None
    
    # Location
    file_path: str | None = None
    line_number: int | None = None
    code_snippet: str | None = None
    
    # Severity
    severity: str  # critical, high, medium, low
    priority: RemediationPriority
    
    # Description
    description: str
    impact: str | None = None
    
    # Context
    repository_id: UUID | None = None
    scan_id: UUID | None = None
    
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class RemediationAction(BaseModel):
    """A specific remediation action."""
    
    id: UUID = Field(default_factory=uuid4)
    violation_id: UUID
    
    # Action details
    action_type: RemediationType
    title: str
    description: str
    
    # Implementation
    automated: bool = True
    requires_approval: bool = True
    
    # Code changes
    file_path: str | None = None
    original_code: str | None = None
    fixed_code: str | None = None
    diff: str | None = None
    
    # Config changes
    config_path: str | None = None
    config_changes: dict[str, Any] = Field(default_factory=dict)
    
    # Commands to run
    commands: list[str] = Field(default_factory=list)
    
    # Validation
    validation_steps: list[str] = Field(default_factory=list)
    rollback_steps: list[str] = Field(default_factory=list)
    
    # Status
    status: RemediationStatus = RemediationStatus.PENDING
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    
    # PR details
    pr_url: str | None = None
    pr_number: int | None = None
    branch_name: str | None = None
    
    # Execution
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    
    # Approval tracking
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RemediationPlan(BaseModel):
    """A plan containing multiple remediation actions."""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    
    # Plan details
    name: str
    description: str
    
    # Violations and actions
    violations: list[ComplianceViolation] = Field(default_factory=list)
    actions: list[RemediationAction] = Field(default_factory=list)
    
    # Execution mode
    auto_execute: bool = False  # Auto-execute approved actions
    require_all_approvals: bool = True  # Require approval for each action
    
    # Statistics
    total_violations: int = 0
    remediated_count: int = 0
    pending_count: int = 0
    failed_count: int = 0
    
    # Status
    status: RemediationStatus = RemediationStatus.PENDING
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AutopilotConfig(BaseModel):
    """Configuration for the autopilot."""
    
    # Automation settings
    enabled: bool = True
    auto_remediate_low_risk: bool = False  # Auto-fix low severity issues
    auto_create_prs: bool = True
    auto_merge_approved: bool = False
    
    # Approval settings
    require_approval_for_critical: bool = True
    require_approval_for_code_changes: bool = True
    require_approval_for_config_changes: bool = True
    
    # Scope
    allowed_repositories: list[UUID] = Field(default_factory=list)
    excluded_paths: list[str] = Field(default_factory=list)
    
    # PR settings
    pr_branch_prefix: str = "compliance-fix/"
    pr_title_prefix: str = "[Compliance] "
    pr_labels: list[str] = Field(default_factory=lambda: ["compliance", "automated"])
    
    # Notifications
    notify_on_violation: bool = True
    notify_on_remediation: bool = True
    notification_channels: list[str] = Field(default_factory=list)


class RemediationResult(BaseModel):
    """Result of a remediation action."""
    
    action_id: UUID
    success: bool
    
    # Execution details
    execution_time_ms: float | None = None
    
    # Changes made
    files_modified: list[str] = Field(default_factory=list)
    pr_created: bool = False
    pr_url: str | None = None
    
    # Validation
    validation_passed: bool = False
    validation_output: str | None = None
    
    # Error details
    error: str | None = None
    rollback_performed: bool = False
    
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class AutopilotSession(BaseModel):
    """An autopilot remediation session."""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    
    # Session details
    name: str = "Compliance Remediation Session"
    description: str | None = None
    
    # Plans
    plans: list[RemediationPlan] = Field(default_factory=list)
    
    # Configuration
    config: AutopilotConfig = Field(default_factory=AutopilotConfig)
    
    # Execution
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    
    # Statistics
    total_violations: int = 0
    total_actions: int = 0
    completed_actions: int = 0
    failed_actions: int = 0
    pending_approvals: int = 0
    
    # Results
    results: list[RemediationResult] = Field(default_factory=list)
    
    # Status
    status: RemediationStatus = RemediationStatus.PENDING


# ============================================================================
# Remediation Templates
# ============================================================================

REMEDIATION_TEMPLATES: dict[str, dict[str, Any]] = {
    # Encryption fixes
    "missing_encryption": {
        "action_type": RemediationType.ENCRYPTION,
        "title": "Enable encryption for data storage",
        "description": "Add encryption configuration to protect sensitive data at rest",
        "automated": True,
        "requires_approval": True,
        "validation_steps": [
            "Verify encryption is enabled",
            "Test data access still works",
            "Verify no plaintext data exposure",
        ],
        "rollback_steps": [
            "Disable encryption configuration",
            "Restore original configuration",
        ],
    },
    "weak_encryption": {
        "action_type": RemediationType.ENCRYPTION,
        "title": "Upgrade encryption algorithm",
        "description": "Replace weak encryption with AES-256",
        "automated": True,
        "requires_approval": True,
    },
    
    # Logging fixes
    "missing_audit_logging": {
        "action_type": RemediationType.LOGGING,
        "title": "Add audit logging",
        "description": "Implement audit logging for compliance tracking",
        "automated": True,
        "requires_approval": True,
    },
    
    # Access control fixes
    "overly_permissive_access": {
        "action_type": RemediationType.ACCESS_CONTROL,
        "title": "Restrict access permissions",
        "description": "Implement least privilege access control",
        "automated": True,
        "requires_approval": True,
    },
    
    # Data handling fixes
    "pii_exposure": {
        "action_type": RemediationType.DATA_HANDLING,
        "title": "Mask or remove PII exposure",
        "description": "Apply data masking to prevent PII exposure in logs/responses",
        "automated": True,
        "requires_approval": True,
    },
    "missing_consent_check": {
        "action_type": RemediationType.CODE_FIX,
        "title": "Add consent verification",
        "description": "Add consent checking before data processing",
        "automated": True,
        "requires_approval": True,
    },
    
    # Dependency updates
    "vulnerable_dependency": {
        "action_type": RemediationType.DEPENDENCY_UPDATE,
        "title": "Update vulnerable dependency",
        "description": "Update package to patched version",
        "automated": True,
        "requires_approval": False,  # Usually safe to auto-update
    },
    
    # Documentation fixes
    "missing_privacy_policy": {
        "action_type": RemediationType.DOCUMENTATION,
        "title": "Add privacy policy documentation",
        "description": "Create or update privacy policy documentation",
        "automated": False,
        "requires_approval": True,
    },
    
    # Configuration fixes
    "insecure_configuration": {
        "action_type": RemediationType.CONFIG_CHANGE,
        "title": "Fix insecure configuration",
        "description": "Update configuration to secure settings",
        "automated": True,
        "requires_approval": True,
    },
}

# Code fix patterns
CODE_FIX_PATTERNS: dict[str, dict[str, str]] = {
    "python_logging_pii": {
        "pattern": r"logger\.(info|debug|warning|error)\([^)]*\b(email|password|ssn|credit_card)",
        "fix_template": "# PII redacted from logs\nlogger.{level}('Sensitive operation performed')",
    },
    "python_sql_injection": {
        "pattern": r"cursor\.execute\(.*%s.*%.*\)",
        "fix_template": "cursor.execute(query, (params,))  # Parameterized query",
    },
    "js_hardcoded_secret": {
        "pattern": r"(const|let|var)\s+\w*(secret|password|key|token)\w*\s*=\s*['\"][^'\"]+['\"]",
        "fix_template": "const {name} = process.env.{ENV_VAR};",
    },
}
