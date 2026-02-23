"""API endpoints for Compliance Testing."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_testing import ComplianceTestingService


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class FuzzPolicyRequest(BaseModel):
    iterations: int = Field(100, ge=1, description="Number of fuzz iterations to run")


# --- Endpoints ---


@router.post("/test/{policy_slug}")
async def run_test_suite(policy_slug: str, db: DB) -> dict:
    """Run the compliance test suite for a policy."""
    svc = ComplianceTestingService()
    return await svc.run_test_suite(db, policy_slug=policy_slug)


@router.post("/fuzz/{policy_slug}")
async def fuzz_policy(policy_slug: str, request: FuzzPolicyRequest, db: DB) -> dict:
    """Fuzz-test a compliance policy."""
    svc = ComplianceTestingService()
    return await svc.fuzz_policy(
        db, policy_slug=policy_slug, iterations=request.iterations,
    )


@router.get("/policies")
async def list_testable_policies(db: DB) -> list[dict]:
    """List policies available for testing."""
    svc = ComplianceTestingService()
    return await svc.list_testable_policies(db)


@router.get("/stats")
async def get_stats(db: DB) -> dict:
    """Get compliance testing statistics."""
    svc = ComplianceTestingService()
    return await svc.get_stats(db)
