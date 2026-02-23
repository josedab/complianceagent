"""Compliance Testing Framework Service."""

import hashlib
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_testing.models import (
    FuzzResult,
    PolicyTestCase,
    PolicyTestSuite,
    TestingStats,
    TestResult,
    TestType,
)


logger = structlog.get_logger()

_COMPLIANCE_PATTERNS: dict[str, list[str]] = {
    "gdpr-consent-required": ["personal_data", "user_email", "user_name", "ip_address", "tracking"],
    "hipaa-phi-encryption": ["patient", "medical", "diagnosis", "health_record", "clinical"],
    "pci-card-tokenization": ["card_number", "credit_card", "cvv", "pan", "cardholder"],
    "soc2-audit-logging": ["admin_action", "privilege_escalation", "security_event"],
}

_SAFE_CODE_SAMPLES = [
    "result = compute_total(items)",
    "logger.info('Processing request')",
    "config = load_settings()",
    "response = await http_client.get(url)",
    "cache.set(key, value, ttl=3600)",
]

_VIOLATION_CODE_SAMPLES: dict[str, list[str]] = {
    "gdpr-consent-required": ["user_email = form.get('email')", "store_personal_data(user_name)"],
    "hipaa-phi-encryption": ["print(patient.diagnosis)", "log.info(f'Patient: {medical_record}')"],
    "pci-card-tokenization": ["db.save(card_number)", "response.json({'cvv': cvv})"],
    "soc2-audit-logging": ["admin_action_execute(cmd)", "escalate_privilege(user)"],
}


class ComplianceTestingService:
    """Property-based testing for compliance policies."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._suites: list[PolicyTestSuite] = []
        self._fuzz_results: list[FuzzResult] = []

    async def run_test_suite(self, policy_slug: str) -> PolicyTestSuite:
        start = datetime.now(UTC)
        patterns = _COMPLIANCE_PATTERNS.get(policy_slug, [])
        if not patterns:
            return PolicyTestSuite(policy_slug=policy_slug, run_at=datetime.now(UTC))

        test_cases: list[PolicyTestCase] = []

        # Generate positive tests (should detect violations)
        violation_samples = _VIOLATION_CODE_SAMPLES.get(policy_slug, [])
        for i, code in enumerate(violation_samples):
            tc = PolicyTestCase(
                policy_slug=policy_slug,
                name=f"detect_violation_{i + 1}",
                test_type=TestType.UNIT,
                input_code=code,
                expected_result=TestResult.PASS,
                violation_expected=True,
                violation_found=any(p in code.lower() for p in patterns),
            )
            tc.actual_result = TestResult.PASS if tc.violation_found == tc.violation_expected else TestResult.FAIL
            test_cases.append(tc)

        # Generate negative tests (should NOT detect violations)
        for i, code in enumerate(_SAFE_CODE_SAMPLES):
            tc = PolicyTestCase(
                policy_slug=policy_slug,
                name=f"no_false_positive_{i + 1}",
                test_type=TestType.UNIT,
                input_code=code,
                expected_result=TestResult.PASS,
                violation_expected=False,
                violation_found=any(p in code.lower() for p in patterns),
            )
            tc.actual_result = TestResult.PASS if tc.violation_found == tc.violation_expected else TestResult.FAIL
            test_cases.append(tc)

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        passed = sum(1 for tc in test_cases if tc.actual_result == TestResult.PASS)
        failed = sum(1 for tc in test_cases if tc.actual_result == TestResult.FAIL)

        suite = PolicyTestSuite(
            policy_slug=policy_slug,
            test_cases=test_cases,
            total=len(test_cases),
            passed=passed,
            failed=failed,
            coverage_pct=round(passed / len(test_cases) * 100, 1) if test_cases else 0.0,
            duration_ms=round(duration, 2),
            run_at=datetime.now(UTC),
        )
        self._suites.append(suite)
        logger.info("Test suite completed", policy=policy_slug, passed=passed, failed=failed)
        return suite

    async def fuzz_policy(self, policy_slug: str, iterations: int = 100) -> FuzzResult:
        patterns = _COMPLIANCE_PATTERNS.get(policy_slug, [])
        if not patterns:
            return FuzzResult(policy_slug=policy_slug, run_at=datetime.now(UTC))

        violations_found = 0
        false_positives = 0
        false_negatives = 0
        edge_cases: list[dict] = []

        for i in range(iterations):
            # Generate deterministic pseudo-random code from iteration hash
            code_hash = hashlib.sha256(f"{policy_slug}:{i}".encode()).hexdigest()
            has_pattern = int(code_hash[:2], 16) % 3 == 0  # ~33% contain patterns
            if has_pattern:
                pattern = patterns[int(code_hash[2:4], 16) % len(patterns)]
                code = f"data = process_{pattern}(input_value)"
            else:
                code = f"result = compute_value_{i}(data)"

            detected = any(p in code.lower() for p in patterns)

            if has_pattern and detected:
                violations_found += 1
            elif has_pattern and not detected:
                false_negatives += 1
                edge_cases.append({"iteration": i, "type": "false_negative", "code": code})
            elif not has_pattern and detected:
                false_positives += 1
                edge_cases.append({"iteration": i, "type": "false_positive", "code": code})

        total_checks = violations_found + false_positives + false_negatives + (iterations - violations_found - false_negatives)
        accuracy = round((total_checks - false_positives - false_negatives) / total_checks * 100, 1) if total_checks else 0.0

        result = FuzzResult(
            policy_slug=policy_slug,
            iterations=iterations,
            violations_found=violations_found,
            false_positives=false_positives,
            false_negatives=false_negatives,
            accuracy_pct=accuracy,
            edge_cases=edge_cases[:10],
            run_at=datetime.now(UTC),
        )
        self._fuzz_results.append(result)
        logger.info("Fuzz completed", policy=policy_slug, iterations=iterations, accuracy=accuracy)
        return result

    def list_testable_policies(self) -> list[str]:
        return list(_COMPLIANCE_PATTERNS.keys())

    def get_stats(self) -> TestingStats:
        by_result: dict[str, int] = {}
        total_cases = 0
        passed = 0
        for suite in self._suites:
            total_cases += suite.total
            passed += suite.passed
            by_result["pass"] = by_result.get("pass", 0) + suite.passed
            by_result["fail"] = by_result.get("fail", 0) + suite.failed

        return TestingStats(
            total_suites_run=len(self._suites),
            total_test_cases=total_cases,
            overall_pass_rate=round(passed / total_cases * 100, 1) if total_cases else 0.0,
            fuzz_iterations=sum(f.iterations for f in self._fuzz_results),
            policies_tested=len({s.policy_slug for s in self._suites}),
            by_result=by_result,
        )
