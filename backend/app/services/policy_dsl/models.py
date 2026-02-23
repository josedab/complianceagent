"""Compliance-as-Code Policy Language models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class OutputFormat(str, Enum):
    REGO = "rego"
    PYTHON = "python"
    YAML = "yaml"
    TYPESCRIPT = "typescript"


class PolicySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


@dataclass
class PolicyDefinition:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    description: str = ""
    framework: str = ""
    severity: PolicySeverity = PolicySeverity.MEDIUM
    status: PolicyStatus = PolicyStatus.DRAFT
    dsl_source: str = ""
    conditions: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    author: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class CompiledPolicy:
    id: UUID = field(default_factory=uuid4)
    policy_id: UUID = field(default_factory=uuid4)
    output_format: OutputFormat = OutputFormat.REGO
    compiled_code: str = ""
    compiled_at: datetime | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    parsed_conditions: int = 0
    parsed_actions: int = 0


@dataclass
class PolicyDSLStats:
    total_policies: int = 0
    active_policies: int = 0
    by_framework: dict[str, int] = field(default_factory=dict)
    by_severity: dict[str, int] = field(default_factory=dict)
    compilations: dict[str, int] = field(default_factory=dict)
