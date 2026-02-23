"""API endpoints for CI/CD Runtime compliance."""

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.cicd_runtime import CICDRuntimeService


logger = structlog.get_logger()
router = APIRouter()


class DeploymentCheckRequest(BaseModel):
    deployment_id: str = Field(...)
    repo: str = Field(...)
    commit_sha: str = Field(...)
    phase: str = Field(default="pre_deploy")


class AttestationCreateRequest(BaseModel):
    deployment_id: str = Field(...)
    repo: str = Field(...)
    commit_sha: str = Field(...)
    score: float = Field(...)
    frameworks: list[str] | None = Field(default=None)


class RollbackRequest(BaseModel):
    deployment_id: str = Field(...)
    reason: str = Field(...)
    original_score: float = Field(...)
    new_score: float = Field(...)


@router.post("/check", status_code=status.HTTP_201_CREATED, summary="Check deployment compliance")
async def check_deployment(request: DeploymentCheckRequest, db: DB) -> dict:
    """Run compliance checks against a deployment."""
    service = CICDRuntimeService(db=db)
    result = await service.check_deployment(
        deployment_id=request.deployment_id,
        repo=request.repo,
        commit_sha=request.commit_sha,
        phase=request.phase,
    )
    return {
        "id": str(result.id),
        "deployment_id": result.deployment_id,
        "repo": result.repo,
        "phase": result.phase.value,
        "checks_passed": result.checks_passed,
        "checks_failed": result.checks_failed,
        "gate_decision": result.gate_decision.value,
        "violations": result.violations,
        "duration_ms": result.duration_ms,
        "checked_at": result.checked_at.isoformat() if result.checked_at else None,
    }


@router.post("/attest", status_code=status.HTTP_201_CREATED, summary="Create attestation")
async def create_attestation(request: AttestationCreateRequest, db: DB) -> dict:
    """Create a deployment attestation."""
    service = CICDRuntimeService(db=db)
    result = await service.create_attestation(
        deployment_id=request.deployment_id,
        repo=request.repo,
        commit_sha=request.commit_sha,
        score=request.score,
        frameworks=request.frameworks,
    )
    return {
        "id": str(result.id),
        "deployment_id": result.deployment_id,
        "repo": result.repo,
        "commit_sha": result.commit_sha,
        "level": result.level.value,
        "compliance_score": result.compliance_score,
        "frameworks_checked": result.frameworks_checked,
        "signature": result.signature,
        "attested_at": result.attested_at.isoformat() if result.attested_at else None,
    }


@router.post("/rollback", summary="Trigger rollback")
async def trigger_rollback(request: RollbackRequest, db: DB) -> dict:
    """Trigger a rollback for a deployment."""
    service = CICDRuntimeService(db=db)
    result = await service.trigger_rollback(
        deployment_id=request.deployment_id,
        reason=request.reason,
        scores=(request.original_score, request.new_score),
    )
    return {
        "id": str(result.id),
        "deployment_id": result.deployment_id,
        "reason": result.reason,
        "original_score": result.original_score,
        "new_score": result.new_score,
        "rolled_back_at": result.rolled_back_at.isoformat() if result.rolled_back_at else None,
    }


@router.get("/checks", summary="List checks")
async def list_checks(db: DB, deployment_id: str | None = None) -> list[dict]:
    """List runtime checks, optionally filtered by deployment."""
    service = CICDRuntimeService(db=db)
    checks = await service.list_checks(deployment_id=deployment_id)
    return [
        {
            "id": str(c.id),
            "deployment_id": c.deployment_id,
            "repo": c.repo,
            "phase": c.phase.value,
            "checks_passed": c.checks_passed,
            "checks_failed": c.checks_failed,
            "gate_decision": c.gate_decision.value,
            "violations": c.violations,
            "duration_ms": c.duration_ms,
            "checked_at": c.checked_at.isoformat() if c.checked_at else None,
        }
        for c in checks
    ]


@router.get("/attestations", summary="List attestations")
async def list_attestations(db: DB, deployment_id: str | None = None) -> list[dict]:
    """List attestations, optionally filtered by deployment."""
    service = CICDRuntimeService(db=db)
    attestations = await service.list_attestations(deployment_id=deployment_id)
    return [
        {
            "id": str(a.id),
            "deployment_id": a.deployment_id,
            "repo": a.repo,
            "commit_sha": a.commit_sha,
            "level": a.level.value,
            "compliance_score": a.compliance_score,
            "frameworks_checked": a.frameworks_checked,
            "signature": a.signature,
            "attested_at": a.attested_at.isoformat() if a.attested_at else None,
        }
        for a in attestations
    ]


@router.get("/stats", summary="Get stats")
async def get_stats(db: DB) -> dict:
    """Get CI/CD runtime statistics."""
    service = CICDRuntimeService(db=db)
    stats = await service.get_stats()
    return {
        "total_checks": stats.total_checks,
        "deployments_gated": stats.deployments_gated,
        "rollbacks": stats.rollbacks,
        "attestations_issued": stats.attestations_issued,
        "avg_check_duration_ms": stats.avg_check_duration_ms,
        "pass_rate": stats.pass_rate,
    }
