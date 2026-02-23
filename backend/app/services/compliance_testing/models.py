"""Compliance Testing Framework models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class TestResult(str, Enum):
    PASS = "pass"  # noqa: S105
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


class TestType(str, Enum):
    UNIT = "unit"
    PROPERTY = "property"
    FUZZ = "fuzz"
    INTEGRATION = "integration"


@dataclass
class PolicyTestCase:
    id: UUID = field(default_factory=uuid4)
    policy_slug: str = ""
    name: str = ""
    test_type: TestType = TestType.UNIT
    input_code: str = ""
    expected_result: TestResult = TestResult.PASS
    actual_result: TestResult = TestResult.PASS
    violation_expected: bool = False
    violation_found: bool = False
    error_message: str = ""
    execution_time_ms: float = 0.0


@dataclass
class PolicyTestSuite:
    id: UUID = field(default_factory=uuid4)
    policy_slug: str = ""
    test_cases: list[PolicyTestCase] = field(default_factory=list)
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    coverage_pct: float = 0.0
    duration_ms: float = 0.0
    run_at: datetime | None = None


@dataclass
class FuzzResult:
    id: UUID = field(default_factory=uuid4)
    policy_slug: str = ""
    iterations: int = 0
    violations_found: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    accuracy_pct: float = 0.0
    edge_cases: list[dict[str, Any]] = field(default_factory=list)
    run_at: datetime | None = None


@dataclass
class TestingStats:
    total_suites_run: int = 0
    total_test_cases: int = 0
    overall_pass_rate: float = 0.0
    fuzz_iterations: int = 0
    policies_tested: int = 0
    by_result: dict[str, int] = field(default_factory=dict)
