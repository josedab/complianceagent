"""API endpoints for Compliance Testing."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_testing import (
    ComplianceTestingService,
    FuzzResult,
    PolicyTestSuite,
    TestingStats,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class FuzzPolicyRequest(BaseModel):
    iterations: int = Field(100, ge=1, description="Number of fuzz iterations to run")


# --- Endpoints ---


@router.post("/test/{policy_slug}")
async def run_test_suite(policy_slug: str, db: DB) -> PolicyTestSuite:
    """Run the compliance test suite for a policy."""
    svc = ComplianceTestingService(db)
    return await svc.run_test_suite(policy_slug=policy_slug)


@router.post("/fuzz/{policy_slug}")
async def fuzz_policy(policy_slug: str, request: FuzzPolicyRequest, db: DB) -> FuzzResult:
    """Fuzz-test a compliance policy."""
    svc = ComplianceTestingService(db)
    return await svc.fuzz_policy(
        policy_slug=policy_slug,
        iterations=request.iterations,
    )


@router.get("/policies")
async def list_testable_policies(db: DB) -> list[str]:
    """List policies available for testing."""
    svc = ComplianceTestingService(db)
    return svc.list_testable_policies()


@router.get("/stats")
async def get_stats(db: DB) -> TestingStats:
    """Get compliance testing statistics."""
    svc = ComplianceTestingService(db)
    return svc.get_stats()
