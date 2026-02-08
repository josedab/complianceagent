"""Compliance-as-Code Policy SDK models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class PolicyLanguage(str, Enum):
    REGO = "rego"
    PYTHON = "python"
    YAML = "yaml"
    JSON = "json"
    TYPESCRIPT = "typescript"


class PolicySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PolicyCategory(str, Enum):
    DATA_PRIVACY = "data_privacy"
    SECURITY = "security"
    ACCESS_CONTROL = "access_control"
    ENCRYPTION = "encryption"
    LOGGING = "logging"
    INCIDENT_RESPONSE = "incident_response"
    AI_GOVERNANCE = "ai_governance"
    CUSTOM = "custom"


@dataclass
class PolicyDefinition:
    """A compliance policy defined as code."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    language: PolicyLanguage = PolicyLanguage.YAML
    category: PolicyCategory = PolicyCategory.CUSTOM
    severity: PolicySeverity = PolicySeverity.MEDIUM
    frameworks: list[str] = field(default_factory=list)
    source_code: str = ""
    test_cases: list[dict] = field(default_factory=list)
    author: str = ""
    downloads: int = 0
    rating: float = 0.0
    is_community: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class PolicyValidationResult:
    """Result of validating a policy."""
    policy_id: UUID = field(default_factory=uuid4)
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    test_results: list[dict] = field(default_factory=list)
    coverage: float = 0.0


@dataclass
class PolicyMarketplaceEntry:
    """A policy in the community marketplace."""
    id: UUID = field(default_factory=uuid4)
    policy: PolicyDefinition = field(default_factory=PolicyDefinition)
    publisher: str = ""
    installs: int = 0
    stars: int = 0
    verified: bool = False
    tags: list[str] = field(default_factory=list)
    published_at: datetime | None = None
