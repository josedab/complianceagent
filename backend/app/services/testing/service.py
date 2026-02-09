"""AI Compliance Testing Suite Generator Service."""

import time
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.testing import GeneratedTestRecord, TestSuiteRun
from app.services.testing.models import (
    ComplianceTestPattern,
    FrameworkDetectionResult,
    GeneratedTest,
    TestFramework,
    TestPatternCategory,
    TestStatus,
    TestSuiteResult,
    TestValidationResult,
)


logger = structlog.get_logger()

# Pre-built compliance test patterns
_PATTERNS: list[ComplianceTestPattern] = [
    ComplianceTestPattern(
        id="gdpr-consent-001",
        name="GDPR Consent Collection Verification",
        category=TestPatternCategory.CONSENT,
        regulation="GDPR",
        description="Verify that user consent is collected before processing personal data",
        test_template="assert consent_record is not None\nassert consent_record.purpose != ''\nassert consent_record.timestamp is not None",
        assertions=["consent_exists", "purpose_specified", "timestamp_recorded", "revocable"],
        tags=["gdpr", "consent", "art-6", "art-7"],
    ),
    ComplianceTestPattern(
        id="gdpr-deletion-002",
        name="GDPR Right to Erasure",
        category=TestPatternCategory.DATA_DELETION,
        regulation="GDPR",
        description="Verify that user data can be completely deleted upon request",
        test_template="await delete_user_data(user_id)\nassert await get_user_data(user_id) is None\nassert await get_audit_log(user_id) is not None",
        assertions=["data_deleted", "backups_queued", "audit_preserved", "third_parties_notified"],
        tags=["gdpr", "deletion", "art-17", "right-to-erasure"],
    ),
    ComplianceTestPattern(
        id="gdpr-access-003",
        name="GDPR Data Subject Access Request",
        category=TestPatternCategory.DATA_PRIVACY,
        regulation="GDPR",
        description="Verify DSAR endpoint returns complete user data in portable format",
        test_template="response = await export_user_data(user_id)\nassert response.format in ['json', 'csv']\nassert 'personal_data' in response.content",
        assertions=["export_complete", "portable_format", "timely_response", "includes_all_categories"],
        tags=["gdpr", "dsar", "art-15", "data-portability"],
    ),
    ComplianceTestPattern(
        id="hipaa-encryption-001",
        name="HIPAA PHI Encryption at Rest",
        category=TestPatternCategory.ENCRYPTION,
        regulation="HIPAA",
        description="Verify that Protected Health Information is encrypted at rest",
        test_template="stored_data = get_raw_storage(phi_record_id)\nassert is_encrypted(stored_data)\nassert encryption_algorithm in APPROVED_ALGORITHMS",
        assertions=["data_encrypted", "approved_algorithm", "key_management", "no_plaintext_leaks"],
        tags=["hipaa", "encryption", "phi", "security-rule"],
    ),
    ComplianceTestPattern(
        id="hipaa-audit-002",
        name="HIPAA Audit Trail for PHI Access",
        category=TestPatternCategory.AUDIT_LOGGING,
        regulation="HIPAA",
        description="Verify that all PHI access events are logged with required fields",
        test_template="access_phi(user_id, record_id)\nlogs = get_audit_logs(record_id)\nassert len(logs) > 0\nassert logs[-1].user_id == user_id",
        assertions=["access_logged", "user_identified", "timestamp_recorded", "action_type_logged"],
        tags=["hipaa", "audit", "phi-access", "security-rule"],
    ),
    ComplianceTestPattern(
        id="hipaa-breach-003",
        name="HIPAA Breach Notification Timing",
        category=TestPatternCategory.BREACH_NOTIFICATION,
        regulation="HIPAA",
        description="Verify breach notification is triggered within 60-day requirement",
        test_template="report_breach(breach_event)\nnotification = get_pending_notifications()\nassert notification.deadline_days <= 60",
        assertions=["notification_created", "within_60_days", "affected_individuals_counted", "hhs_notified"],
        tags=["hipaa", "breach", "notification", "60-day-rule"],
    ),
    ComplianceTestPattern(
        id="pci-tokenization-001",
        name="PCI-DSS Card Data Tokenization",
        category=TestPatternCategory.TOKENIZATION,
        regulation="PCI-DSS",
        description="Verify that card numbers are tokenized before storage",
        test_template="token = tokenize_card(card_number)\nassert not contains_pan(token)\nassert detokenize(token) == card_number",
        assertions=["pan_not_stored", "token_irreversible_without_key", "token_format_valid", "no_plaintext_in_logs"],
        tags=["pci-dss", "tokenization", "card-data", "req-3"],
    ),
    ComplianceTestPattern(
        id="pci-no-plaintext-002",
        name="PCI-DSS No Plaintext Card Storage",
        category=TestPatternCategory.ENCRYPTION,
        regulation="PCI-DSS",
        description="Verify that no plaintext card data exists in storage or logs",
        test_template="process_payment(card_data)\nassert not search_logs_for_pan(card_data.number)\nassert not search_db_for_pan(card_data.number)",
        assertions=["no_pan_in_logs", "no_pan_in_db", "no_pan_in_cache", "no_pan_in_temp_files"],
        tags=["pci-dss", "storage", "plaintext", "req-3"],
    ),
    ComplianceTestPattern(
        id="ai-act-transparency-001",
        name="EU AI Act Transparency Disclosure",
        category=TestPatternCategory.AI_TRANSPARENCY,
        regulation="EU_AI_ACT",
        description="Verify AI system provides transparency information to users",
        test_template="info = get_ai_system_info(model_id)\nassert info.risk_level is not None\nassert info.intended_purpose != ''\nassert info.limitations != ''",
        assertions=["risk_level_classified", "purpose_documented", "limitations_disclosed", "human_oversight_described"],
        tags=["eu-ai-act", "transparency", "art-13", "high-risk"],
    ),
    ComplianceTestPattern(
        id="ai-act-risk-001",
        name="EU AI Act Risk Assessment",
        category=TestPatternCategory.AI_TRANSPARENCY,
        regulation="EU_AI_ACT",
        description="Verify AI system has completed risk assessment with required elements",
        test_template="assessment = get_risk_assessment(system_id)\nassert assessment.risk_category in VALID_CATEGORIES\nassert len(assessment.mitigation_measures) > 0",
        assertions=["risk_categorized", "mitigations_identified", "testing_documented", "monitoring_planned"],
        tags=["eu-ai-act", "risk-assessment", "art-9", "conformity"],
    ),
    ComplianceTestPattern(
        id="gdpr-retention-001",
        name="GDPR Data Retention Policy Enforcement",
        category=TestPatternCategory.DATA_RETENTION,
        regulation="GDPR",
        description="Verify data is automatically purged after retention period expires",
        test_template="create_record_with_date(past_retention_date)\nrun_retention_job()\nassert get_record(record_id) is None",
        assertions=["expired_data_purged", "retention_schedule_enforced", "audit_trail_kept", "exceptions_documented"],
        tags=["gdpr", "retention", "art-5", "storage-limitation"],
    ),
    ComplianceTestPattern(
        id="hipaa-access-control-001",
        name="HIPAA Minimum Necessary Access Control",
        category=TestPatternCategory.ACCESS_CONTROL,
        regulation="HIPAA",
        description="Verify role-based access enforces minimum necessary principle for PHI",
        test_template="result = access_phi_as_role('receptionist', full_medical_record)\nassert result.access_denied or result.fields_redacted",
        assertions=["role_enforced", "minimum_necessary", "unauthorized_denied", "access_scope_limited"],
        tags=["hipaa", "access-control", "minimum-necessary", "privacy-rule"],
    ),
]

# Framework-specific test templates
_FRAMEWORK_TEMPLATES: dict[TestFramework, str] = {
    TestFramework.PYTEST: '''"""Compliance test: {description}"""

import pytest

@pytest.mark.compliance
@pytest.mark.{regulation_lower}
class Test{class_name}:
    """Tests for {regulation} - {pattern_name}."""

    async def test_{test_slug}(self):
        """{description}"""
        {test_body}
        {assertions}
''',
    TestFramework.JEST: """/**
 * Compliance test: {description}
 * @regulation {regulation}
 */
describe('{pattern_name}', () => {{
  it('should {test_slug_readable}', async () => {{
    {test_body}
    {assertions}
  }});
}});
""",
    TestFramework.JUNIT: """/**
 * Compliance test: {description}
 * @regulation {regulation}
 */
@Tag("compliance")
@Tag("{regulation_lower}")
class {class_name}Test {{
    @Test
    @DisplayName("{description}")
    void test{class_name}() {{
        {test_body}
        {assertions}
    }}
}}
""",
}


class ComplianceTestingService:
    """Service for generating compliance test suites."""

    def __init__(
        self,
        db: AsyncSession,
        copilot_client: object | None = None,
    ):
        self.db = db
        self.copilot = copilot_client

    async def list_patterns(
        self,
        regulation: str | None = None,
        category: TestPatternCategory | None = None,
    ) -> list[ComplianceTestPattern]:
        """List available compliance test patterns with optional filters."""
        patterns = _PATTERNS
        if regulation:
            patterns = [p for p in patterns if p.regulation.lower() == regulation.lower()]
        if category:
            patterns = [p for p in patterns if p.category == category]
        return patterns

    async def get_pattern(self, pattern_id: str) -> ComplianceTestPattern | None:
        """Get a specific test pattern by ID."""
        for p in _PATTERNS:
            if p.id == pattern_id:
                return p
        return None

    async def detect_frameworks(
        self,
        repo: str,
        files: list[str] | None = None,
    ) -> FrameworkDetectionResult:
        """Detect test frameworks used in a repository."""
        result = FrameworkDetectionResult()
        file_list = files or []

        detection_map = {
            "pytest.ini": TestFramework.PYTEST,
            "pyproject.toml": TestFramework.PYTEST,
            "conftest.py": TestFramework.PYTEST,
            "setup.cfg": TestFramework.PYTEST,
            "jest.config.js": TestFramework.JEST,
            "jest.config.ts": TestFramework.JEST,
            "package.json": TestFramework.JEST,
            "pom.xml": TestFramework.JUNIT,
            "build.gradle": TestFramework.JUNIT,
            ".mocharc.yml": TestFramework.MOCHA,
            "Gemfile": TestFramework.RSPEC,
            "go.mod": TestFramework.GO_TEST,
        }

        language_map = {
            TestFramework.PYTEST: "python",
            TestFramework.JEST: "typescript",
            TestFramework.JUNIT: "java",
            TestFramework.MOCHA: "javascript",
            TestFramework.RSPEC: "ruby",
            TestFramework.GO_TEST: "go",
        }

        for file_path in file_list:
            filename = file_path.rsplit("/", maxsplit=1)[-1] if "/" in file_path else file_path
            if filename in detection_map:
                fw = detection_map[filename]
                if fw not in result.detected_frameworks:
                    result.detected_frameworks.append(fw)
                result.config_files_found.append(file_path)

        if result.detected_frameworks:
            result.recommended_framework = result.detected_frameworks[0]
            result.primary_language = language_map.get(result.recommended_framework, "unknown")
        else:
            result.recommended_framework = TestFramework.PYTEST
            result.primary_language = "python"

        logger.info("Framework detection complete", repo=repo, frameworks=len(result.detected_frameworks))
        return result

    async def generate_test_suite(
        self,
        regulation: str,
        framework: TestFramework = TestFramework.PYTEST,
        target_files: list[str] | None = None,
        pattern_ids: list[str] | None = None,
    ) -> TestSuiteResult:
        """Generate a compliance test suite for a regulation."""
        start = time.monotonic()

        result = TestSuiteResult(
            status=TestStatus.GENERATING,
            regulation=regulation,
            framework=framework,
        )

        # Select applicable patterns
        if pattern_ids:
            patterns = [p for p in _PATTERNS if p.id in pattern_ids]
        else:
            patterns = [p for p in _PATTERNS if p.regulation.lower() == regulation.lower()]

        if not patterns:
            result.status = TestStatus.FAILED
            return result

        template = _FRAMEWORK_TEMPLATES.get(framework, _FRAMEWORK_TEMPLATES[TestFramework.PYTEST])

        for pattern in patterns:
            test = await self._generate_test_from_pattern(pattern, template, framework, target_files)
            result.tests.append(test)
            result.patterns_used.append(pattern.id)

        result.total_tests = len(result.tests)
        result.coverage_estimate = min(len(result.tests) * 8.5, 100.0)
        result.status = TestStatus.COMPLETED
        result.generated_at = datetime.now(UTC)
        result.generation_time_ms = (time.monotonic() - start) * 1000

        # Persist to database
        await self._persist_suite(result)

        logger.info(
            "Test suite generated",
            regulation=regulation,
            framework=framework.value,
            tests=result.total_tests,
        )
        return result

    async def _persist_suite(self, result: TestSuiteResult) -> None:
        """Persist a test suite run and its generated tests to the database."""
        try:
            run = TestSuiteRun(
                id=result.id,
                regulation=result.regulation,
                framework=result.framework.value,
                total_tests=result.total_tests,
                coverage_score=result.coverage_estimate,
                pattern_ids=result.patterns_used,
                generated_tests={
                    "tests": [
                        {"id": str(t.id), "name": t.test_name, "pattern_id": t.pattern_id}
                        for t in result.tests
                    ]
                },
                execution_time_ms=int(result.generation_time_ms) if result.generation_time_ms else None,
                status=result.status.value,
            )
            self.db.add(run)

            for test in result.tests:
                record = GeneratedTestRecord(
                    suite_run_id=result.id,
                    regulation=test.regulation,
                    framework=test.framework.value,
                    pattern_id=test.pattern_id,
                    test_name=test.test_name,
                    test_code=test.test_code,
                    description=test.description,
                    ai_generated=False,
                )
                self.db.add(record)

            await self.db.commit()
        except Exception:
            await self.db.rollback()
            logger.warning("Failed to persist test suite, continuing with in-memory result")

    async def get_result(self, suite_id: UUID) -> TestSuiteResult | None:
        """Get a test suite result from the database."""
        stmt = select(TestSuiteRun).where(TestSuiteRun.id == suite_id)
        result = await self.db.execute(stmt)
        run = result.scalar_one_or_none()
        if not run:
            return None

        # Reconstruct the result from DB
        return TestSuiteResult(
            id=run.id,
            status=TestStatus(run.status),
            regulation=run.regulation,
            framework=TestFramework(run.framework),
            total_tests=run.total_tests,
            coverage_estimate=run.coverage_score,
            patterns_used=run.pattern_ids or [],
            generated_at=run.created_at,
        )

    async def validate_tests(self, suite_id: UUID) -> TestValidationResult:
        """Validate generated tests for syntax and completeness."""
        validation = TestValidationResult(suite_id=suite_id)

        # Try DB first
        stmt = select(GeneratedTestRecord).where(GeneratedTestRecord.suite_run_id == suite_id)
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        if not records:
            validation.errors.append("Suite not found")
            return validation

        validation.total_tests = len(records)
        valid = 0
        for record in records:
            if record.test_code and record.test_name:
                valid += 1
            else:
                validation.errors.append(f"Test {record.id} has empty code or name")

        validation.valid_tests = valid
        validation.invalid_tests = validation.total_tests - valid
        return validation

    async def _generate_test_from_pattern(
        self,
        pattern: ComplianceTestPattern,
        template: str,
        framework: TestFramework,
        target_files: list[str] | None,
    ) -> GeneratedTest:
        """Generate a single test from a pattern, optionally enhanced by Copilot."""
        # Try AI-enhanced generation first
        if self.copilot:
            try:
                return await self._generate_test_with_copilot(pattern, framework, target_files)
            except Exception:
                logger.debug("Copilot unavailable, falling back to template", pattern=pattern.id)

        # Fallback to template-based generation
        return self._generate_test_from_template(pattern, template, framework, target_files)

    async def _generate_test_with_copilot(
        self,
        pattern: ComplianceTestPattern,
        framework: TestFramework,
        target_files: list[str] | None,
    ) -> GeneratedTest:
        """Use Copilot to generate an AI-enhanced compliance test."""
        from app.agents.copilot import CopilotMessage

        prompt = (
            f"Generate a {framework.value} compliance test for: {pattern.name}\n"
            f"Regulation: {pattern.regulation}\n"
            f"Description: {pattern.description}\n"
            f"Required assertions: {', '.join(pattern.assertions)}\n"
            f"Tags: {', '.join(pattern.tags)}\n"
            f"Target files: {', '.join(target_files or ['N/A'])}\n\n"
            f"Return ONLY the test code, no explanation. Make it production-ready "
            f"with proper imports, assertions, and docstrings."
        )

        response = await self.copilot.chat(
            messages=[CopilotMessage(role="user", content=prompt)],
            system_message=(
                f"You are a compliance testing expert. Generate {framework.value} tests "
                f"that verify {pattern.regulation} regulatory requirements. "
                f"Output only valid test code."
            ),
            temperature=0.3,
            max_tokens=2048,
        )

        test_slug = pattern.id.replace("-", "_")
        target = target_files[0] if target_files else ""

        return GeneratedTest(
            pattern_id=pattern.id,
            test_name=f"test_{test_slug}",
            test_code=response.content,
            framework=framework,
            regulation=pattern.regulation,
            requirement_ref=", ".join(pattern.tags[:2]),
            description=pattern.description,
            confidence=0.92,
            target_file=target,
        )

    def _generate_test_from_template(
        self,
        pattern: ComplianceTestPattern,
        template: str,
        framework: TestFramework,
        target_files: list[str] | None,
    ) -> GeneratedTest:
        """Generate a single test from a pattern template (fallback)."""
        class_name = pattern.name.replace(" ", "").replace("-", "")
        test_slug = pattern.id.replace("-", "_")
        test_slug_readable = pattern.description.lower()
        regulation_lower = pattern.regulation.lower().replace("-", "_")

        assertions_code = "\n        ".join(
            f"# Assert: {a}" for a in pattern.assertions
        )

        test_code = template.format(
            description=pattern.description,
            regulation=pattern.regulation,
            regulation_lower=regulation_lower,
            class_name=class_name,
            pattern_name=pattern.name,
            test_slug=test_slug,
            test_slug_readable=test_slug_readable,
            test_body=pattern.test_template,
            assertions=assertions_code,
        )

        target = target_files[0] if target_files else ""

        return GeneratedTest(
            pattern_id=pattern.id,
            test_name=f"test_{test_slug}",
            test_code=test_code,
            framework=framework,
            regulation=pattern.regulation,
            requirement_ref=", ".join(pattern.tags[:2]),
            description=pattern.description,
            confidence=0.85,
            target_file=target,
        )
