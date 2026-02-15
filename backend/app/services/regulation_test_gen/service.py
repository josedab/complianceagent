"""Regulation-to-Test-Case Generator Service."""

import random
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.regulation_test_gen.models import (
    CoverageStatus,
    RegulationCoverage,
    RegulationTestCase,
    TestFramework,
    TestRunResult,
    TestSuite,
)


logger = structlog.get_logger()

# Regulation articles for test generation
_REGULATION_ARTICLES: dict[str, list[dict]] = {
    "GDPR": [
        {"ref": "Art. 5", "summary": "Principles relating to processing of personal data"},
        {"ref": "Art. 6", "summary": "Lawfulness of processing"},
        {"ref": "Art. 7", "summary": "Conditions for consent"},
        {"ref": "Art. 12", "summary": "Transparent information and communication"},
        {"ref": "Art. 15", "summary": "Right of access by the data subject"},
        {"ref": "Art. 17", "summary": "Right to erasure"},
        {"ref": "Art. 20", "summary": "Right to data portability"},
        {"ref": "Art. 25", "summary": "Data protection by design and by default"},
        {"ref": "Art. 32", "summary": "Security of processing"},
        {"ref": "Art. 33", "summary": "Notification of personal data breach"},
    ],
    "HIPAA": [
        {"ref": "§164.308(a)(1)", "summary": "Security management process"},
        {"ref": "§164.308(a)(3)", "summary": "Workforce security"},
        {"ref": "§164.308(a)(4)", "summary": "Information access management"},
        {"ref": "§164.310(a)(1)", "summary": "Facility access controls"},
        {"ref": "§164.312(a)(1)", "summary": "Access control"},
        {"ref": "§164.312(b)", "summary": "Audit controls"},
        {"ref": "§164.312(c)(1)", "summary": "Integrity controls"},
        {"ref": "§164.312(e)(1)", "summary": "Transmission security"},
    ],
    "SOX": [
        {"ref": "Sec. 302", "summary": "Corporate responsibility for financial reports"},
        {"ref": "Sec. 404", "summary": "Management assessment of internal controls"},
        {"ref": "Sec. 409", "summary": "Real-time issuer disclosures"},
        {"ref": "Sec. 802", "summary": "Criminal penalties for altering documents"},
        {"ref": "Sec. 906", "summary": "Corporate responsibility for financial reports"},
    ],
    "PCI-DSS": [
        {"ref": "Req 1", "summary": "Install and maintain network security controls"},
        {"ref": "Req 3", "summary": "Protect stored account data"},
        {"ref": "Req 6", "summary": "Develop and maintain secure systems and software"},
        {"ref": "Req 7", "summary": "Restrict access to system components"},
        {"ref": "Req 8", "summary": "Identify users and authenticate access"},
        {"ref": "Req 10", "summary": "Log and monitor all access"},
    ],
}

# Test code templates per framework
_TEST_TEMPLATES: dict[TestFramework, str] = {
    TestFramework.PYTEST: 'def test_{name}():\n    """{summary}"""\n    result = check_compliance("{ref}")\n    assert result.is_compliant\n    assert result.evidence_count > 0',
    TestFramework.JEST: 'describe("{ref}", () => {{\n  it("should {summary}", async () => {{\n    const result = await checkCompliance("{ref}");\n    expect(result.isCompliant).toBe(true);\n  }});\n}});',
    TestFramework.JUNIT: '@Test\npublic void test{name}() {{\n    // {summary}\n    ComplianceResult result = checker.verify("{ref}");\n    assertTrue(result.isCompliant());\n}}',
    TestFramework.MOCHA: 'describe("{ref}", function() {{\n  it("should {summary}", function() {{\n    const result = checkCompliance("{ref}");\n    assert.ok(result.isCompliant);\n  }});\n}});',
    TestFramework.GO_TEST: 'func Test{name}(t *testing.T) {{\n\t// {summary}\n\tresult := CheckCompliance("{ref}")\n\tif !result.IsCompliant {{\n\t\tt.Errorf("compliance check failed for {ref}")\n\t}}\n}}',
    TestFramework.RSPEC: 'describe "{ref}" do\n  it "{summary}" do\n    result = check_compliance("{ref}")\n    expect(result.compliant?).to be true\n  end\nend',
}


class RegulationTestGenService:
    """Generate test cases from regulatory requirements."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._suites: dict[UUID, TestSuite] = {}
        self._coverages: dict[str, RegulationCoverage] = {}

    async def generate_test_suite(
        self,
        regulation: str,
        framework: TestFramework,
        target_files: list[str] | None = None,
    ) -> TestSuite:
        """Generate a test suite for a regulation."""
        articles = _REGULATION_ARTICLES.get(regulation, [])
        if not articles:
            articles = [
                {"ref": f"{regulation}-{i}", "summary": f"Requirement {i} for {regulation}"}
                for i in range(1, 6)
            ]

        template = _TEST_TEMPLATES.get(framework, _TEST_TEMPLATES[TestFramework.PYTEST])
        test_cases: list[RegulationTestCase] = []

        for article in articles:
            safe_name = (
                article["ref"]
                .replace(".", "_")
                .replace(" ", "_")
                .replace("§", "s")
                .replace("(", "")
                .replace(")", "")
            )
            test_code = template.format(
                name=safe_name,
                summary=article["summary"].lower(),
                ref=article["ref"],
            )
            test_cases.append(
                RegulationTestCase(
                    regulation=regulation,
                    article_ref=article["ref"],
                    requirement_summary=article["summary"],
                    test_name=f"test_{safe_name}",
                    test_code=test_code,
                    framework=framework,
                    assertions=[
                        f"assert compliance with {article['ref']}",
                        "assert evidence exists",
                    ],
                    confidence=round(random.uniform(0.75, 0.98), 2),
                    tags=[regulation.lower(), article["ref"].lower().replace(" ", "_")],
                )
            )

        suite = TestSuite(
            regulation=regulation,
            framework=framework,
            test_cases=test_cases,
            total_tests=len(test_cases),
            coverage_pct=round((len(test_cases) / max(len(articles), 1)) * 100, 1),
            generated_at=datetime.now(UTC),
        )
        self._suites[suite.id] = suite

        # Update coverage
        self._coverages[regulation] = RegulationCoverage(
            regulation=regulation,
            total_articles=len(articles),
            covered_articles=len(test_cases),
            coverage_pct=suite.coverage_pct,
            uncovered_articles=[],
            status=CoverageStatus.FULLY_COVERED
            if suite.coverage_pct >= 100
            else CoverageStatus.PARTIALLY_COVERED,
        )

        logger.info(
            "Test suite generated",
            regulation=regulation,
            framework=framework.value,
            tests=len(test_cases),
        )
        return suite

    async def list_test_suites(self, regulation: str | None = None) -> list[TestSuite]:
        """List all generated test suites."""
        suites = list(self._suites.values())
        if regulation:
            suites = [s for s in suites if s.regulation == regulation]
        return suites

    async def get_test_suite(self, suite_id: UUID) -> TestSuite:
        """Get a specific test suite."""
        suite = self._suites.get(suite_id)
        if not suite:
            raise ValueError(f"Test suite not found: {suite_id}")
        return suite

    async def get_regulation_coverage(self, regulation: str) -> RegulationCoverage:
        """Get coverage analysis for a regulation."""
        if regulation in self._coverages:
            return self._coverages[regulation]

        articles = _REGULATION_ARTICLES.get(regulation, [])
        return RegulationCoverage(
            regulation=regulation,
            total_articles=len(articles),
            covered_articles=0,
            coverage_pct=0.0,
            uncovered_articles=[a["ref"] for a in articles],
            status=CoverageStatus.NOT_COVERED,
        )

    async def run_tests(self, suite_id: UUID) -> TestRunResult:
        """Simulate running a test suite."""
        suite = self._suites.get(suite_id)
        if not suite:
            raise ValueError(f"Test suite not found: {suite_id}")

        total = suite.total_tests
        passed = int(total * random.uniform(0.7, 1.0))
        failed = total - passed
        errors = random.randint(0, max(1, failed // 2))

        result = TestRunResult(
            suite_id=suite_id,
            passed=passed,
            failed=failed,
            errors=errors,
            duration_ms=random.randint(500, 5000),
            coverage_report={
                "line_coverage": round(random.uniform(70, 95), 1),
                "branch_coverage": round(random.uniform(60, 90), 1),
                "articles_covered": passed,
                "articles_total": total,
            },
            ran_at=datetime.now(UTC),
        )
        logger.info("Test run completed", suite_id=str(suite_id), passed=passed, failed=failed)
        return result

    async def list_coverages(self) -> list[RegulationCoverage]:
        """List coverage for all known regulations."""
        coverages: list[RegulationCoverage] = []
        for reg in _REGULATION_ARTICLES:
            if reg in self._coverages:
                coverages.append(self._coverages[reg])
            else:
                articles = _REGULATION_ARTICLES[reg]
                coverages.append(
                    RegulationCoverage(
                        regulation=reg,
                        total_articles=len(articles),
                        covered_articles=0,
                        coverage_pct=0.0,
                        uncovered_articles=[a["ref"] for a in articles],
                        status=CoverageStatus.NOT_COVERED,
                    )
                )
        return coverages

    async def get_uncovered_regulations(self) -> list[str]:
        """Get list of regulations with no test coverage."""
        uncovered = []
        for reg in _REGULATION_ARTICLES:
            cov = self._coverages.get(reg)
            if not cov or cov.coverage_pct == 0:
                uncovered.append(reg)
        return uncovered
