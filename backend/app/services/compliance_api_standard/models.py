"""Compliance API Standard models."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SpecVersion(str, Enum):
    DRAFT = "draft"
    V0_1 = "v0_1"
    V1_0 = "v1_0"


class EndpointCategory(str, Enum):
    POSTURE = "posture"
    VIOLATIONS = "violations"
    REGULATIONS = "regulations"
    AUDIT = "audit"
    EVIDENCE = "evidence"
    SCANNING = "scanning"
    REMEDIATION = "remediation"


@dataclass
class APIEndpointSpec:
    path: str = ""
    method: str = ""
    category: EndpointCategory = EndpointCategory.POSTURE
    description: str = ""
    request_schema: dict[str, Any] = field(default_factory=dict)
    response_schema: dict[str, Any] = field(default_factory=dict)
    auth_required: bool = True


@dataclass
class APIStandard:
    id: UUID = field(default_factory=uuid4)
    version: SpecVersion = SpecVersion.DRAFT
    title: str = ""
    description: str = ""
    endpoints: list[APIEndpointSpec] = field(default_factory=list)
    total_endpoints: int = 0
    created_at: datetime | None = None


@dataclass
class ConformanceReport:
    id: UUID = field(default_factory=uuid4)
    api_base_url: str = ""
    version: SpecVersion = SpecVersion.V1_0
    endpoints_tested: int = 0
    endpoints_conforming: int = 0
    conformance_pct: float = 0.0
    issues: list[dict[str, Any]] = field(default_factory=list)
    tested_at: datetime | None = None


@dataclass
class StandardStats:
    versions_published: int = 0
    total_endpoints: int = 0
    conformance_tests_run: int = 0
    avg_conformance_pct: float = 0.0
