"""Continuous Control Testing models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ControlFramework(str, Enum):
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    NIST_CSF = "nist_csf"


class TestStatus(str, Enum):
    PASSING = "passing"
    FAILING = "failing"
    ERROR = "error"
    SKIPPED = "skipped"
    PENDING = "pending"


class TestFrequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    ON_CHANGE = "on_change"


class EvidenceType(str, Enum):
    API_CHECK = "api_check"
    CONFIG_SCAN = "config_scan"
    LOG_ANALYSIS = "log_analysis"
    ACCESS_REVIEW = "access_review"
    ENCRYPTION_CHECK = "encryption_check"


@dataclass
class ControlTest:
    id: UUID = field(default_factory=uuid4)
    control_id: str = ""
    framework: ControlFramework = ControlFramework.SOC2
    name: str = ""
    description: str = ""
    test_type: EvidenceType = EvidenceType.API_CHECK
    frequency: TestFrequency = TestFrequency.DAILY
    enabled: bool = True
    last_run: datetime | None = None
    last_status: TestStatus = TestStatus.PENDING
    consecutive_failures: int = 0


@dataclass
class TestResult:
    id: UUID = field(default_factory=uuid4)
    test_id: UUID | None = None
    control_id: str = ""
    status: TestStatus = TestStatus.PASSING
    message: str = ""
    evidence_data: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    executed_at: datetime | None = None


@dataclass
class ControlTestSuite:
    framework: ControlFramework = ControlFramework.SOC2
    total_tests: int = 0
    passing: int = 0
    failing: int = 0
    error: int = 0
    skipped: int = 0
    last_full_run: datetime | None = None
    tests: list[ControlTest] = field(default_factory=list)
    coverage_pct: float = 0.0
