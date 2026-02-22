"""GitOps Compliance Pipeline API endpoints."""

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.gitops_pipeline import GitOpsPipelineService


logger = structlog.get_logger()
router = APIRouter()


class GateRequest(BaseModel):
    repo: str
    branch: str = "main"
    commit_sha: str = ""
    changed_files: list[dict] = Field(default_factory=list)
    baseline_score: float = 100.0


class RemediationRequest(BaseModel):
    repo: str
    violations: list[dict]
    source_branch: str = "main"


@router.post("/evaluate-gate")
async def evaluate_gate(request: GateRequest, db: DB) -> dict:
    """Evaluate compliance gate for a commit or PR."""
    svc = GitOpsPipelineService(db)
    result = await svc.evaluate_gate(
        repo=request.repo, branch=request.branch, commit_sha=request.commit_sha,
        changed_files=request.changed_files, baseline_score=request.baseline_score,
    )
    return {
        "decision": result.decision.value,
        "score_before": result.score_before,
        "score_after": result.score_after,
        "score_delta": result.score_delta,
        "violations": result.violations,
        "blocking_rules": result.blocking_rules,
    }


@router.post("/remediation-branch")
async def create_remediation(request: RemediationRequest, db: DB, copilot: CopilotDep) -> dict:
    """Create a remediation branch with auto-generated fixes."""
    svc = GitOpsPipelineService(db, copilot_client=copilot)
    branch = await svc.create_remediation_branch(
        repo=request.repo, violations=request.violations, source_branch=request.source_branch,
    )
    return {
        "id": str(branch.id),
        "branch": branch.remediation_branch,
        "status": branch.status.value,
        "violations_addressed": branch.violation_ids,
    }


@router.get("/precommit-config")
async def get_precommit_config(db: DB) -> dict:
    """Get pre-commit hook configuration."""
    svc = GitOpsPipelineService(db)
    config = await svc.get_precommit_config()
    return {
        "enabled_rules": config.enabled_rules,
        "severity_threshold": config.severity_threshold,
        "max_scan_time_ms": config.max_scan_time_ms,
        "scan_changed_only": config.scan_changed_only,
    }


@router.get("/evaluations")
async def list_evaluations(
    db: DB,
    repo: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict]:
    """Get gate evaluation history."""
    svc = GitOpsPipelineService(db)
    evals = await svc.get_evaluations(repo=repo, limit=limit)
    return [
        {
            "repo": e.repo,
            "branch": e.branch,
            "decision": e.decision.value,
            "score_delta": e.score_delta,
            "violations": len(e.violations),
            "evaluated_at": e.evaluated_at.isoformat() if e.evaluated_at else None,
        }
        for e in evals
    ]
