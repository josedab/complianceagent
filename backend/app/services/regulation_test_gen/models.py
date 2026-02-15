"""Regulation-to-Test-Case Generator models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class TestFramework(str, Enum):
    PYTEST = "pytest"
    JEST = "jest"
    JUNIT = "junit"
    MOCHA = "mocha"
    GO_TEST = "go_test"
    RSPEC = "rspec"


class CoverageStatus(str, Enum):
    FULLY_COVERED = "fully_covered"
    PARTIALLY_COVERED = "partially_covered"
    NOT_COVERED = "not_covered"
    NEEDS_UPDATE = "needs_update"


@dataclass
class RegulationTestCase:
    """A test case generated from a regulation requirement."""

    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    article_ref: str = ""
    requirement_summary: str = ""
    test_name: str = ""
    test_code: str = ""
    framework: TestFramework = TestFramework.PYTEST
    assertions: list[str] = field(default_factory=list)
    confidence: float = 0.0
    tags: list[str] = field(default_factory=list)


@dataclass
class TestSuite:
    """A suite of test cases for a regulation."""

    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    framework: TestFramework = TestFramework.PYTEST
    test_cases: list[RegulationTestCase] = field(default_factory=list)
    total_tests: int = 0
    coverage_pct: float = 0.0
    generated_at: datetime | None = None


@dataclass
class RegulationCoverage:
    """Coverage analysis for a regulation."""

    regulation: str = ""
    total_articles: int = 0
    covered_articles: int = 0
    coverage_pct: float = 0.0
    uncovered_articles: list[str] = field(default_factory=list)
    status: CoverageStatus = CoverageStatus.NOT_COVERED


@dataclass
class TestRunResult:
    """Result from running a test suite."""

    id: UUID = field(default_factory=uuid4)
    suite_id: UUID = field(default_factory=uuid4)
    passed: int = 0
    failed: int = 0
    errors: int = 0
    duration_ms: int = 0
    coverage_report: dict = field(default_factory=dict)
    ran_at: datetime | None = None
