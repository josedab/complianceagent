"""API endpoints for AI Compliance Testing Suite Generator."""

from uuid import UUID

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.testing import (
    ComplianceTestingService,
    TestFramework,
    TestPatternCategory,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class GenerateRequest(BaseModel):
    """Request to generate a compliance test suite."""

    regulation: str = Field(..., min_length=1, description="Regulation to generate tests for")
    framework: str = Field(default="pytest", description="Test framework to use")
    target_files: list[str] = Field(default_factory=list, description="Target files to test")
    pattern_ids: list[str] = Field(default_factory=list, description="Specific pattern IDs")


class DetectFrameworksRequest(BaseModel):
    """Request to detect test frameworks."""

    repo: str = Field(..., min_length=1, description="Repository name")
    files: list[str] = Field(default_factory=list, description="File paths to analyze")


class GeneratedTestSchema(BaseModel):
    """Single generated test."""

    id: str
    pattern_id: str
    test_name: str
    test_code: str
    framework: str
    regulation: str
    requirement_ref: str
    description: str
    confidence: float
    target_file: str


class TestSuiteSchema(BaseModel):
    """Generated test suite response."""

    id: str
    status: str
    regulation: str
    framework: str
    tests: list[GeneratedTestSchema]
    patterns_used: list[str]
    total_tests: int
    coverage_estimate: float
    generation_time_ms: float


class PatternSchema(BaseModel):
    """Test pattern response."""

    id: str
    name: str
    category: str
    regulation: str
    description: str
    assertions: list[str]
    tags: list[str]


class FrameworkDetectionSchema(BaseModel):
    """Framework detection response."""

    detected_frameworks: list[str]
    primary_language: str
    config_files_found: list[str]
    recommended_framework: str


class ValidationSchema(BaseModel):
    """Test validation response."""

    suite_id: str
    total_tests: int
    valid_tests: int
    invalid_tests: int
    errors: list[str]
    warnings: list[str]


# --- Endpoints ---


@router.post(
    "/generate",
    response_model=TestSuiteSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate compliance test suite",
    description="Generate a compliance test suite for a regulation and framework",
)
async def generate_test_suite(
    request: GenerateRequest,
    db: DB,
    copilot: CopilotDep,
) -> TestSuiteSchema:
    """Generate compliance tests from patterns."""
    service = ComplianceTestingService(db=db, copilot_client=copilot)
    framework = TestFramework(request.framework)
    result = await service.generate_test_suite(
        regulation=request.regulation,
        framework=framework,
        target_files=request.target_files or None,
        pattern_ids=request.pattern_ids or None,
    )

    return TestSuiteSchema(
        id=str(result.id),
        status=result.status.value,
        regulation=result.regulation,
        framework=result.framework.value,
        tests=[
            GeneratedTestSchema(
                id=str(t.id), pattern_id=t.pattern_id, test_name=t.test_name,
                test_code=t.test_code, framework=t.framework.value,
                regulation=t.regulation, requirement_ref=t.requirement_ref,
                description=t.description, confidence=t.confidence,
                target_file=t.target_file,
            )
            for t in result.tests
        ],
        patterns_used=result.patterns_used,
        total_tests=result.total_tests,
        coverage_estimate=result.coverage_estimate,
        generation_time_ms=result.generation_time_ms,
    )


@router.get(
    "/patterns",
    response_model=list[PatternSchema],
    summary="List compliance test patterns",
)
async def list_patterns(
    db: DB,
    copilot: CopilotDep,
    regulation: str | None = None,
    category: str | None = None,
) -> list[PatternSchema]:
    """List available compliance test patterns."""
    service = ComplianceTestingService(db=db, copilot_client=copilot)
    cat = TestPatternCategory(category) if category else None
    patterns = await service.list_patterns(regulation=regulation, category=cat)
    return [
        PatternSchema(
            id=p.id, name=p.name, category=p.category.value,
            regulation=p.regulation, description=p.description,
            assertions=p.assertions, tags=p.tags,
        )
        for p in patterns
    ]


@router.post(
    "/detect-frameworks",
    response_model=FrameworkDetectionSchema,
    summary="Detect test frameworks in repository",
)
async def detect_frameworks(
    request: DetectFrameworksRequest,
    db: DB,
    copilot: CopilotDep,
) -> FrameworkDetectionSchema:
    """Detect test frameworks used in a repository."""
    service = ComplianceTestingService(db=db, copilot_client=copilot)
    result = await service.detect_frameworks(
        repo=request.repo, files=request.files,
    )
    return FrameworkDetectionSchema(
        detected_frameworks=[f.value for f in result.detected_frameworks],
        primary_language=result.primary_language,
        config_files_found=result.config_files_found,
        recommended_framework=result.recommended_framework.value,
    )


@router.post(
    "/validate/{suite_id}",
    response_model=ValidationSchema,
    summary="Validate generated tests",
)
async def validate_tests(
    suite_id: str,
    db: DB,
    copilot: CopilotDep,
) -> ValidationSchema:
    """Validate a generated test suite for syntax and completeness."""
    service = ComplianceTestingService(db=db, copilot_client=copilot)
    result = await service.validate_tests(UUID(suite_id))
    return ValidationSchema(
        suite_id=str(result.suite_id),
        total_tests=result.total_tests,
        valid_tests=result.valid_tests,
        invalid_tests=result.invalid_tests,
        errors=result.errors,
        warnings=result.warnings,
    )
