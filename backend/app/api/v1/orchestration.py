"""API endpoints for Cross-Repository Compliance Orchestration."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.orchestration import (
    OrchestrationManager,
    PolicyAction,
    PolicyType,
    RepositoryStatus,
    get_orchestration_manager,
)


router = APIRouter(prefix="/orchestration", tags=["orchestration"])


# Request/Response Models
class AddRepositoryRequest(BaseModel):
    """Request to add a repository for management."""
    
    organization_id: UUID
    name: str
    full_name: str
    url: str = ""
    default_branch: str = "main"
    tracked_regulations: list[str] = []


class UpdateRepositoryStatusRequest(BaseModel):
    """Request to update repository compliance status."""
    
    compliance_score: float = Field(..., ge=0, le=1)
    open_issues: int = 0
    critical_issues: int = 0


class CreatePolicyRequest(BaseModel):
    """Request to create a compliance policy."""
    
    organization_id: UUID
    name: str
    policy_type: str = Field(..., description="Type: minimum_score, required_regulation, blocked_dependencies, scan_frequency")
    config: dict[str, Any]
    description: str = ""
    on_violation: str = "warn"
    applies_to: list[str] = ["*"]
    created_by: str = ""


class CreatePolicyFromTemplateRequest(BaseModel):
    """Request to create policy from template."""
    
    organization_id: UUID
    template_name: str
    overrides: dict[str, Any] | None = None


class BatchScanRequest(BaseModel):
    """Request to trigger batch scan."""
    
    organization_id: UUID
    repository_ids: list[UUID] | None = None


def _parse_policy_type(value: str) -> PolicyType:
    """Parse policy type string."""
    try:
        return PolicyType(value.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy_type: {value}. Valid: {[t.value for t in PolicyType]}",
        )


def _parse_policy_action(value: str) -> PolicyAction:
    """Parse policy action string."""
    try:
        return PolicyAction(value.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {value}. Valid: {[a.value for a in PolicyAction]}",
        )


# Repository Endpoints
@router.post("/repositories")
async def add_repository(request: AddRepositoryRequest):
    """Add a repository for compliance management.
    
    Once added, the repository will be subject to organization policies
    and included in compliance dashboards.
    """
    manager = get_orchestration_manager()
    
    repo = await manager.add_repository(
        organization_id=request.organization_id,
        name=request.name,
        full_name=request.full_name,
        url=request.url,
        default_branch=request.default_branch,
        tracked_regulations=request.tracked_regulations,
    )
    
    return {
        "id": str(repo.id),
        "name": repo.name,
        "full_name": repo.full_name,
        "status": repo.status.value,
        "applied_policies": len(repo.applied_policies),
        "created_at": repo.created_at.isoformat(),
    }


@router.get("/organizations/{organization_id}/repositories")
async def list_repositories(
    organization_id: UUID,
    status: str | None = None,
):
    """List repositories for an organization."""
    manager = get_orchestration_manager()
    
    status_enum = None
    if status:
        try:
            status_enum = RepositoryStatus(status.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid: {[s.value for s in RepositoryStatus]}",
            )
    
    repos = await manager.list_repositories(organization_id, status=status_enum)
    
    return {
        "organization_id": str(organization_id),
        "count": len(repos),
        "repositories": [
            {
                "id": str(r.id),
                "name": r.name,
                "full_name": r.full_name,
                "status": r.status.value,
                "compliance_score": round(r.compliance_score, 3),
                "open_issues": r.open_issues,
                "critical_issues": r.critical_issues,
                "last_scan_at": r.last_scan_at.isoformat() if r.last_scan_at else None,
                "tracked_regulations": r.tracked_regulations,
            }
            for r in repos
        ],
    }


@router.get("/repositories/{repo_id}")
async def get_repository(repo_id: UUID):
    """Get repository details."""
    manager = get_orchestration_manager()
    repo = await manager.get_repository(repo_id)
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return {
        "id": str(repo.id),
        "name": repo.name,
        "full_name": repo.full_name,
        "url": repo.url,
        "default_branch": repo.default_branch,
        "status": repo.status.value,
        "compliance_score": repo.compliance_score,
        "open_issues": repo.open_issues,
        "critical_issues": repo.critical_issues,
        "last_scan_at": repo.last_scan_at.isoformat() if repo.last_scan_at else None,
        "applied_policies": [str(p) for p in repo.applied_policies],
        "policy_violations": repo.policy_violations,
        "tracked_regulations": repo.tracked_regulations,
    }


@router.patch("/repositories/{repo_id}/status")
async def update_repository_status(
    repo_id: UUID,
    request: UpdateRepositoryStatusRequest,
):
    """Update repository compliance status.
    
    Called after a compliance scan to update the repository's state.
    """
    manager = get_orchestration_manager()
    
    repo = await manager.update_repository_status(
        repo_id=repo_id,
        compliance_score=request.compliance_score,
        open_issues=request.open_issues,
        critical_issues=request.critical_issues,
    )
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return {
        "id": str(repo.id),
        "status": repo.status.value,
        "compliance_score": repo.compliance_score,
        "policy_violations": repo.policy_violations,
    }


# Policy Endpoints
@router.post("/policies")
async def create_policy(request: CreatePolicyRequest):
    """Create a compliance policy for the organization.
    
    Policies automatically apply to matching repositories and
    generate violations when conditions are not met.
    """
    manager = get_orchestration_manager()
    
    policy = await manager.create_policy(
        organization_id=request.organization_id,
        name=request.name,
        policy_type=_parse_policy_type(request.policy_type),
        config=request.config,
        description=request.description,
        on_violation=_parse_policy_action(request.on_violation),
        applies_to=request.applies_to,
        created_by=request.created_by,
    )
    
    return {
        "id": str(policy.id),
        "name": policy.name,
        "policy_type": policy.policy_type.value,
        "on_violation": policy.on_violation.value,
        "applies_to": policy.applies_to,
        "is_active": policy.is_active,
    }


@router.post("/policies/from-template")
async def create_policy_from_template(request: CreatePolicyFromTemplateRequest):
    """Create a policy from a predefined template."""
    manager = get_orchestration_manager()
    
    try:
        policy = await manager.create_policy_from_template(
            organization_id=request.organization_id,
            template_name=request.template_name,
            overrides=request.overrides,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "id": str(policy.id),
        "name": policy.name,
        "policy_type": policy.policy_type.value,
        "config": policy.config,
    }


@router.get("/organizations/{organization_id}/policies")
async def list_policies(
    organization_id: UUID,
    policy_type: str | None = None,
):
    """List policies for an organization."""
    manager = get_orchestration_manager()
    
    type_enum = None
    if policy_type:
        type_enum = _parse_policy_type(policy_type)
    
    policies = await manager.list_policies(organization_id, policy_type=type_enum)
    
    return {
        "organization_id": str(organization_id),
        "count": len(policies),
        "policies": [
            {
                "id": str(p.id),
                "name": p.name,
                "policy_type": p.policy_type.value,
                "config": p.config,
                "on_violation": p.on_violation.value,
                "applies_to": p.applies_to,
                "is_active": p.is_active,
            }
            for p in policies
        ],
    }


@router.get("/policies/templates")
async def list_policy_templates():
    """List available policy templates."""
    manager = get_orchestration_manager()
    templates = manager.list_policy_templates()
    return {"templates": templates}


# Dashboard Endpoints
@router.get("/organizations/{organization_id}/dashboard")
async def get_dashboard(organization_id: UUID):
    """Get organization compliance dashboard.
    
    Returns comprehensive overview of compliance status across all
    managed repositories.
    """
    manager = get_orchestration_manager()
    dashboard = await manager.get_dashboard(organization_id)
    
    return {
        "organization_id": str(dashboard.organization_id),
        "generated_at": dashboard.generated_at.isoformat(),
        "summary": {
            "total_repositories": dashboard.total_repositories,
            "compliant": dashboard.compliant_repositories,
            "non_compliant": dashboard.non_compliant_repositories,
            "compliance_rate": round(
                dashboard.compliant_repositories / dashboard.total_repositories * 100
                if dashboard.total_repositories > 0 else 0,
                1,
            ),
        },
        "scores": {
            "average": round(dashboard.average_score, 3),
            "lowest": round(dashboard.lowest_score, 3),
            "highest": round(dashboard.highest_score, 3),
        },
        "issues": {
            "total": dashboard.total_issues,
            "critical": dashboard.critical_issues,
        },
        "policies": {
            "active": dashboard.active_policies,
            "violations": dashboard.policy_violations,
        },
        "by_regulation": dashboard.by_regulation,
        "top_risk_repositories": dashboard.top_repositories_by_risk,
    }


# Batch Operations
@router.post("/batch-scan")
async def trigger_batch_scan(request: BatchScanRequest):
    """Trigger compliance scans for multiple repositories.
    
    Useful for scheduled organization-wide scans.
    """
    manager = get_orchestration_manager()
    
    result = await manager.batch_scan(
        organization_id=request.organization_id,
        repository_ids=request.repository_ids,
    )
    
    return {
        "scan_id": str(result.id),
        "repositories_scanned": result.repositories_scanned,
        "repositories_failed": result.repositories_failed,
        "duration_seconds": round(result.duration_seconds, 3),
        "results": result.results,
    }


# Status Options
@router.get("/statuses")
async def list_statuses():
    """List possible repository statuses."""
    return {
        "statuses": [
            {"value": s.value, "name": s.value.replace("_", " ").title()}
            for s in RepositoryStatus
        ]
    }


@router.get("/policy-types")
async def list_policy_types():
    """List available policy types."""
    return {
        "policy_types": [
            {"value": t.value, "name": t.value.replace("_", " ").title()}
            for t in PolicyType
        ]
    }


@router.get("/policy-actions")
async def list_policy_actions():
    """List available policy violation actions."""
    return {
        "actions": [
            {"value": a.value, "name": a.value.title()}
            for a in PolicyAction
        ]
    }
