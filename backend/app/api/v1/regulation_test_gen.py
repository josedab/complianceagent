"""API endpoints for Regulation-to-Test-Case Generator."""

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.v1.deps import DB, CopilotDep
from app.services.regulation_test_gen import RegulationTestGenService, TestFramework


logger = structlog.get_logger()
router = APIRouter()


class GenerateRequest(BaseModel):
    regulation: str
    framework: str
    target_files: list[str] | None = None


class TestCaseSchema(BaseModel):
    id: str
    regulation: str
    article_ref: str
    requirement_summary: str
    test_name: str
    test_code: str
    framework: str
    assertions: list[str]
    confidence: float
    tags: list[str]


class TestSuiteSchema(BaseModel):
    id: str
    regulation: str
    framework: str
    test_cases: list[TestCaseSchema]
    total_tests: int
    coverage_pct: float
    generated_at: str | None


class CoverageSchema(BaseModel):
    regulation: str
    total_articles: int
    covered_articles: int
    coverage_pct: float
    uncovered_articles: list[str]
    status: str


class TestRunResultSchema(BaseModel):
    id: str
    suite_id: str
    passed: int
    failed: int
    errors: int
    duration_ms: int
    coverage_report: dict
    ran_at: str | None


def _parse_framework(fw: str) -> TestFramework:
    try:
        return TestFramework(fw)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported framework: {fw}. Use: {[f.value for f in TestFramework]}",
        )


def _suite_to_schema(suite) -> TestSuiteSchema:
    return TestSuiteSchema(
        id=str(suite.id),
        regulation=suite.regulation,
        framework=suite.framework.value,
        test_cases=[
            TestCaseSchema(
                id=str(tc.id),
                regulation=tc.regulation,
                article_ref=tc.article_ref,
                requirement_summary=tc.requirement_summary,
                test_name=tc.test_name,
                test_code=tc.test_code,
                framework=tc.framework.value,
                assertions=tc.assertions,
                confidence=tc.confidence,
                tags=tc.tags,
            )
            for tc in suite.test_cases
        ],
        total_tests=suite.total_tests,
        coverage_pct=suite.coverage_pct,
        generated_at=suite.generated_at.isoformat() if suite.generated_at else None,
    )


@router.post(
    "/generate", response_model=TestSuiteSchema, summary="Generate test suite from regulation"
)
async def generate_test_suite(req: GenerateRequest, db: DB, copilot: CopilotDep) -> TestSuiteSchema:
    fw = _parse_framework(req.framework)
    service = RegulationTestGenService(db=db, copilot_client=copilot)
    suite = await service.generate_test_suite(req.regulation, fw, req.target_files)
    return _suite_to_schema(suite)


@router.get("/suites", response_model=list[TestSuiteSchema], summary="List test suites")
async def list_test_suites(
    db: DB, copilot: CopilotDep, regulation: str | None = None
) -> list[TestSuiteSchema]:
    service = RegulationTestGenService(db=db, copilot_client=copilot)
    suites = await service.list_test_suites(regulation)
    return [_suite_to_schema(s) for s in suites]


@router.get("/suites/{suite_id}", response_model=TestSuiteSchema, summary="Get test suite")
async def get_test_suite(suite_id: str, db: DB, copilot: CopilotDep) -> TestSuiteSchema:
    service = RegulationTestGenService(db=db, copilot_client=copilot)
    try:
        from uuid import UUID

        suite = await service.get_test_suite(UUID(suite_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _suite_to_schema(suite)


@router.get(
    "/coverage/{regulation}", response_model=CoverageSchema, summary="Get regulation coverage"
)
async def get_regulation_coverage(regulation: str, db: DB, copilot: CopilotDep) -> CoverageSchema:
    service = RegulationTestGenService(db=db, copilot_client=copilot)
    cov = await service.get_regulation_coverage(regulation)
    return CoverageSchema(
        regulation=cov.regulation,
        total_articles=cov.total_articles,
        covered_articles=cov.covered_articles,
        coverage_pct=cov.coverage_pct,
        uncovered_articles=cov.uncovered_articles,
        status=cov.status.value,
    )


@router.post("/suites/{suite_id}/run", response_model=TestRunResultSchema, summary="Run test suite")
async def run_tests(suite_id: str, db: DB, copilot: CopilotDep) -> TestRunResultSchema:
    service = RegulationTestGenService(db=db, copilot_client=copilot)
    try:
        from uuid import UUID

        result = await service.run_tests(UUID(suite_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return TestRunResultSchema(
        id=str(result.id),
        suite_id=str(result.suite_id),
        passed=result.passed,
        failed=result.failed,
        errors=result.errors,
        duration_ms=result.duration_ms,
        coverage_report=result.coverage_report,
        ran_at=result.ran_at.isoformat() if result.ran_at else None,
    )


@router.get("/coverage", response_model=list[CoverageSchema], summary="List all coverages")
async def list_coverages(db: DB, copilot: CopilotDep) -> list[CoverageSchema]:
    service = RegulationTestGenService(db=db, copilot_client=copilot)
    coverages = await service.list_coverages()
    return [
        CoverageSchema(
            regulation=c.regulation,
            total_articles=c.total_articles,
            covered_articles=c.covered_articles,
            coverage_pct=c.coverage_pct,
            uncovered_articles=c.uncovered_articles,
            status=c.status.value,
        )
        for c in coverages
    ]


@router.get("/uncovered", response_model=list[str], summary="Get uncovered regulations")
async def get_uncovered_regulations(db: DB, copilot: CopilotDep) -> list[str]:
    service = RegulationTestGenService(db=db, copilot_client=copilot)
    return await service.get_uncovered_regulations()
