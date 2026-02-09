"""AI Compliance Testing Suite Generator models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class TestFramework(str, Enum):
    """Supported test frameworks."""

    PYTEST = "pytest"
    JEST = "jest"
    JUNIT = "junit"
    MOCHA = "mocha"
    RSPEC = "rspec"
    GO_TEST = "go_test"


class TestPatternCategory(str, Enum):
    """Categories of compliance test patterns."""

    DATA_PRIVACY = "data_privacy"
    CONSENT = "consent"
    ENCRYPTION = "encryption"
    ACCESS_CONTROL = "access_control"
    AUDIT_LOGGING = "audit_logging"
    DATA_RETENTION = "data_retention"
    DATA_DELETION = "data_deletion"
    BREACH_NOTIFICATION = "breach_notification"
    TOKENIZATION = "tokenization"
    AI_TRANSPARENCY = "ai_transparency"


class TestStatus(str, Enum):
    """Status of a generated test suite."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATING = "validating"


@dataclass
class ComplianceTestPattern:
    """A reusable compliance test pattern template."""

    id: str = ""
    name: str = ""
    category: TestPatternCategory = TestPatternCategory.DATA_PRIVACY
    regulation: str = ""
    description: str = ""
    test_template: str = ""
    assertions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class GeneratedTest:
    """A single generated compliance test."""

    id: UUID = field(default_factory=uuid4)
    pattern_id: str = ""
    test_name: str = ""
    test_code: str = ""
    framework: TestFramework = TestFramework.PYTEST
    regulation: str = ""
    requirement_ref: str = ""
    description: str = ""
    confidence: float = 0.0
    target_file: str = ""


@dataclass
class TestSuiteResult:
    """Result of generating a compliance test suite."""

    id: UUID = field(default_factory=uuid4)
    status: TestStatus = TestStatus.PENDING
    regulation: str = ""
    framework: TestFramework = TestFramework.PYTEST
    tests: list[GeneratedTest] = field(default_factory=list)
    patterns_used: list[str] = field(default_factory=list)
    total_tests: int = 0
    coverage_estimate: float = 0.0
    generated_at: datetime | None = None
    generation_time_ms: float = 0.0


@dataclass
class TestValidationResult:
    """Result of validating generated tests."""

    suite_id: UUID = field(default_factory=uuid4)
    total_tests: int = 0
    valid_tests: int = 0
    invalid_tests: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class FrameworkDetectionResult:
    """Result of detecting test frameworks in a repository."""

    detected_frameworks: list[TestFramework] = field(default_factory=list)
    primary_language: str = ""
    config_files_found: list[str] = field(default_factory=list)
    recommended_framework: TestFramework = TestFramework.PYTEST
