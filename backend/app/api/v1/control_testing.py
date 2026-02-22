"""Continuous Control Testing API endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.v1.deps import DB
from app.services.control_testing import ControlTestingService
from app.services.control_testing.models import ControlFramework


logger = structlog.get_logger()
router = APIRouter()


class TestSuiteResponse(BaseModel):
    framework: str
    total_tests: int
    passing: int
    failing: int
    error: int
    coverage_pct: float
    tests: list[dict]


class TestResultResponse(BaseModel):
    control_id: str
    status: str
    message: str
    evidence_data: dict
    duration_ms: float


@router.get("/suite/{framework}", response_model=TestSuiteResponse)
async def get_test_suite(framework: str, db: DB) -> TestSuiteResponse:
    """Get all control tests for a framework with current status."""
    svc = ControlTestingService(db)
    fw = ControlFramework(framework.lower().replace("-", "_"))
    suite = await svc.get_test_suite(fw)

    return TestSuiteResponse(
        framework=suite.framework.value,
        total_tests=suite.total_tests,
        passing=suite.passing,
        failing=suite.failing,
        error=suite.error,
        coverage_pct=suite.coverage_pct,
        tests=[
            {
                "id": str(t.id),
                "control_id": t.control_id,
                "name": t.name,
                "description": t.description,
                "test_type": t.test_type.value,
                "frequency": t.frequency.value,
                "enabled": t.enabled,
                "last_status": t.last_status.value,
            }
            for t in suite.tests
        ],
    )


@router.post("/run/{framework}", response_model=list[TestResultResponse])
async def run_test_suite(framework: str, db: DB) -> list[TestResultResponse]:
    """Run all enabled control tests for a framework."""
    svc = ControlTestingService(db)
    fw = ControlFramework(framework.lower().replace("-", "_"))
    results = await svc.run_suite(fw)

    return [
        TestResultResponse(
            control_id=r.control_id,
            status=r.status.value,
            message=r.message,
            evidence_data=r.evidence_data,
            duration_ms=round(r.duration_ms, 1),
        )
        for r in results
    ]


@router.post("/run/test/{test_id}", response_model=TestResultResponse)
async def run_single_test(test_id: UUID, db: DB) -> TestResultResponse:
    """Run a single control test."""
    svc = ControlTestingService(db)
    result = await svc.run_test(test_id)

    return TestResultResponse(
        control_id=result.control_id,
        status=result.status.value,
        message=result.message,
        evidence_data=result.evidence_data,
        duration_ms=round(result.duration_ms, 1),
    )


@router.get("/results")
async def get_test_results(
    db: DB,
    control_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    """Get test execution history."""
    svc = ControlTestingService(db)
    results = await svc.get_results(control_id=control_id, limit=limit)
    return [
        {
            "control_id": r.control_id,
            "status": r.status.value,
            "message": r.message,
            "duration_ms": round(r.duration_ms, 1),
            "executed_at": r.executed_at.isoformat() if r.executed_at else None,
        }
        for r in results
    ]
