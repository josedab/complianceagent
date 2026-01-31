"""Data models for Compliance Playbook Generator."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class TechStack(str, Enum):
    """Technology stacks."""
    
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUBY = "ruby"
    DOTNET = "dotnet"
    PHP = "php"
    RUST = "rust"


class Framework(str, Enum):
    """Web frameworks."""
    
    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    EXPRESS = "express"
    NEXTJS = "nextjs"
    NESTJS = "nestjs"
    SPRING = "spring"
    RAILS = "rails"
    ASPNET = "aspnet"


class CloudProvider(str, Enum):
    """Cloud providers."""
    
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    HEROKU = "heroku"
    VERCEL = "vercel"
    DIGITALOCEAN = "digitalocean"


class PlaybookCategory(str, Enum):
    """Playbook categories."""
    
    DATA_PROTECTION = "data_protection"
    ACCESS_CONTROL = "access_control"
    LOGGING_MONITORING = "logging_monitoring"
    INCIDENT_RESPONSE = "incident_response"
    ENCRYPTION = "encryption"
    AUTHENTICATION = "authentication"
    VENDOR_MANAGEMENT = "vendor_management"
    CHANGE_MANAGEMENT = "change_management"
    BACKUP_RECOVERY = "backup_recovery"
    SECURITY_TRAINING = "security_training"


class StepDifficulty(str, Enum):
    """Step difficulty level."""
    
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class PlaybookStep:
    """A step in a compliance playbook."""
    
    step_number: int = 0
    title: str = ""
    description: str = ""
    
    # Implementation
    code_snippet: str = ""
    commands: list[str] = field(default_factory=list)
    file_changes: list[dict[str, str]] = field(default_factory=list)
    
    # Requirements
    prerequisites: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    
    # Metadata
    difficulty: StepDifficulty = StepDifficulty.MEDIUM
    estimated_minutes: int = 15
    responsible_role: str = ""  # developer, devops, security
    
    # Validation
    verification_steps: list[str] = field(default_factory=list)
    expected_outcome: str = ""


@dataclass
class Playbook:
    """A compliance implementation playbook."""
    
    id: UUID = field(default_factory=uuid4)
    
    # Identity
    name: str = ""
    slug: str = ""
    description: str = ""
    category: PlaybookCategory = PlaybookCategory.DATA_PROTECTION
    
    # Target
    regulations: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    
    # Tech context
    tech_stacks: list[TechStack] = field(default_factory=list)
    frameworks: list[Framework] = field(default_factory=list)
    cloud_providers: list[CloudProvider] = field(default_factory=list)
    
    # Content
    overview: str = ""
    prerequisites: list[str] = field(default_factory=list)
    steps: list[PlaybookStep] = field(default_factory=list)
    
    # Summary
    total_steps: int = 0
    estimated_hours: float = 0.0
    difficulty: StepDifficulty = StepDifficulty.MEDIUM
    
    # Evidence
    evidence_generated: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    
    # Metadata
    version: str = "1.0.0"
    author: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: list[str] = field(default_factory=list)


@dataclass
class PlaybookExecution:
    """Execution tracking for a playbook."""
    
    id: UUID = field(default_factory=uuid4)
    playbook_id: UUID | None = None
    organization_id: UUID | None = None
    
    # Progress
    current_step: int = 0
    completed_steps: list[int] = field(default_factory=list)
    skipped_steps: list[int] = field(default_factory=list)
    
    # Status
    status: str = "not_started"  # not_started, in_progress, completed, paused
    started_at: datetime | None = None
    completed_at: datetime | None = None
    
    # Notes
    step_notes: dict[int, str] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    
    # Evidence collected
    evidence_items: list[dict[str, Any]] = field(default_factory=dict)


@dataclass
class StackProfile:
    """Technology stack profile for playbook customization."""
    
    tech_stack: TechStack
    framework: Framework | None = None
    cloud_provider: CloudProvider | None = None
    
    # Additional context
    uses_containers: bool = False
    uses_kubernetes: bool = False
    database_type: str = ""
    ci_cd_platform: str = ""
    
    # Preferences
    prefer_managed_services: bool = True
    security_level: str = "standard"  # basic, standard, high


# Playbook template definitions
PLAYBOOK_TEMPLATES: dict[str, dict[str, Any]] = {
    "encryption_at_rest": {
        "name": "Implement Encryption at Rest",
        "category": PlaybookCategory.ENCRYPTION,
        "regulations": ["GDPR", "HIPAA", "PCI-DSS"],
        "controls": ["CC6.7", "164.312(a)(2)(iv)", "3.4"],
        "difficulty": StepDifficulty.MEDIUM,
        "estimated_hours": 4,
    },
    "mfa_implementation": {
        "name": "Multi-Factor Authentication Setup",
        "category": PlaybookCategory.AUTHENTICATION,
        "regulations": ["SOC2", "PCI-DSS", "NIST"],
        "controls": ["CC6.1", "8.3"],
        "difficulty": StepDifficulty.MEDIUM,
        "estimated_hours": 3,
    },
    "audit_logging": {
        "name": "Comprehensive Audit Logging",
        "category": PlaybookCategory.LOGGING_MONITORING,
        "regulations": ["SOC2", "HIPAA", "PCI-DSS"],
        "controls": ["CC7.2", "164.312(b)", "10.2"],
        "difficulty": StepDifficulty.MEDIUM,
        "estimated_hours": 6,
    },
    "access_control_rbac": {
        "name": "Role-Based Access Control",
        "category": PlaybookCategory.ACCESS_CONTROL,
        "regulations": ["GDPR", "HIPAA", "SOC2"],
        "controls": ["CC6.1", "164.312(a)(1)"],
        "difficulty": StepDifficulty.HARD,
        "estimated_hours": 8,
    },
    "data_backup": {
        "name": "Automated Backup & Recovery",
        "category": PlaybookCategory.BACKUP_RECOVERY,
        "regulations": ["SOC2", "HIPAA"],
        "controls": ["CC9.1", "164.308(a)(7)"],
        "difficulty": StepDifficulty.MEDIUM,
        "estimated_hours": 5,
    },
    "incident_response": {
        "name": "Incident Response Procedure",
        "category": PlaybookCategory.INCIDENT_RESPONSE,
        "regulations": ["GDPR", "HIPAA", "SOC2"],
        "controls": ["CC7.3", "164.308(a)(6)"],
        "difficulty": StepDifficulty.HARD,
        "estimated_hours": 10,
    },
    "vendor_assessment": {
        "name": "Vendor Security Assessment",
        "category": PlaybookCategory.VENDOR_MANAGEMENT,
        "regulations": ["SOC2", "GDPR"],
        "controls": ["CC9.2"],
        "difficulty": StepDifficulty.EASY,
        "estimated_hours": 2,
    },
    "encryption_in_transit": {
        "name": "TLS/HTTPS Configuration",
        "category": PlaybookCategory.ENCRYPTION,
        "regulations": ["HIPAA", "PCI-DSS"],
        "controls": ["164.312(e)(1)", "4.1"],
        "difficulty": StepDifficulty.EASY,
        "estimated_hours": 2,
    },
}
