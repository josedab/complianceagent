"""Self-Service Audit Workspace API endpoints."""

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.audit_workspace import AuditWorkspaceService
from app.services.audit_workspace.service import AuditFramework


logger = structlog.get_logger()
router = APIRouter()


class CreateWorkspaceRequest(BaseModel):
    org_id: str
    framework: str = Field("soc2_type_ii", description="Audit framework")
    target_audit_date: str | None = Field(None, description="ISO date")


@router.post("/workspace")
async def create_workspace(request: CreateWorkspaceRequest, db: DB) -> dict:
    """Create a new audit preparation workspace."""
    svc = AuditWorkspaceService(db)
    target = datetime.fromisoformat(request.target_audit_date) if request.target_audit_date else None
    fw = AuditFramework(request.framework)
    workspace = await svc.create_workspace(request.org_id, fw, target)
    return {
        "id": str(workspace.id),
        "org_id": workspace.org_id,
        "framework": workspace.framework.value,
        "phase": workspace.phase.value,
    }


@router.get("/workspace/{workspace_id}")
async def get_workspace(workspace_id: UUID, db: DB) -> dict:
    """Get an audit workspace."""
    svc = AuditWorkspaceService(db)
    w = await svc.get_workspace(workspace_id)
    if not w:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {
        "id": str(w.id),
        "org_id": w.org_id,
        "framework": w.framework.value,
        "phase": w.phase.value,
        "evidence_coverage_pct": w.evidence_coverage_pct,
        "remediation_progress_pct": w.remediation_progress_pct,
        "gap_analysis": {
            "total_controls": w.gap_analysis.total_controls,
            "readiness_pct": w.gap_analysis.readiness_pct,
            "gaps_found": w.gap_analysis.gaps_found,
        } if w.gap_analysis else None,
    }


@router.post("/workspace/{workspace_id}/gap-analysis")
async def run_gap_analysis(workspace_id: UUID, db: DB) -> dict:
    """Run automated gap analysis for the workspace framework."""
    svc = AuditWorkspaceService(db)
    result = await svc.run_gap_analysis(workspace_id)
    return {
        "framework": result.framework.value,
        "total_controls": result.total_controls,
        "fully_met": result.fully_met,
        "partially_met": result.partially_met,
        "not_met": result.not_met,
        "readiness_pct": result.readiness_pct,
        "estimated_remediation_days": result.estimated_remediation_days,
        "gaps": [
            {
                "control_id": g.control_id,
                "control_name": g.control_name,
                "status": g.status.value,
                "severity": g.severity,
                "evidence_required": g.evidence_required,
                "evidence_collected": g.evidence_collected,
            }
            for g in result.gaps
        ],
    }


@router.post("/workspace/{workspace_id}/advance")
async def advance_phase(workspace_id: UUID, db: DB) -> dict:
    """Advance the workspace to the next preparation phase."""
    svc = AuditWorkspaceService(db)
    w = await svc.advance_phase(workspace_id)
    if not w:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"id": str(w.id), "phase": w.phase.value}


@router.get("/workspaces")
async def list_workspaces(org_id: str = Query("default"), db: DB = None) -> list[dict]:
    """List all audit workspaces for an organization."""
    svc = AuditWorkspaceService(db)
    workspaces = await svc.list_workspaces(org_id)
    return [
        {
            "id": str(w.id),
            "framework": w.framework.value,
            "phase": w.phase.value,
            "readiness_pct": w.gap_analysis.readiness_pct if w.gap_analysis else 0.0,
        }
        for w in workspaces
    ]
