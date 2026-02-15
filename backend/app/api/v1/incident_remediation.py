"""API endpoints for Incident-to-Compliance Auto-Remediation."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.incident_remediation import (
    IncidentRemediationService,
    IncidentSeverity,
    IncidentSource,
    RemediationStatus,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Request/Response Models ---

class IngestIncidentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Incident title")
    description: str = Field(..., min_length=1, max_length=5000, description="Incident description")
    source: str = Field(..., min_length=1, description="Source: splunk, datadog, elastic, pagerduty, sentry, manual")
    severity: str = Field(..., min_length=1, description="Severity: critical, high, medium, low, info")


class IncidentSchema(BaseModel):
    id: str
    title: str
    description: str
    source: str
    severity: str
    status: str
    affected_frameworks: list[str]
    affected_controls: list[str]
    affected_files: list[str]
    cvss_score: float
    compliance_impact_score: float
    remediation_pr_url: str
    breach_notification_required: bool
    detected_at: str


class RemediationActionSchema(BaseModel):
    id: str
    action_type: str
    description: str
    file_path: str
    code_patch: str
    priority: int
    estimated_effort_minutes: int
    automated: bool


class BreachNotificationSchema(BaseModel):
    id: str
    regulation: str
    authority: str
    deadline: str
    draft_text: str
    affected_individuals_count: int
    data_categories: list[str]


# --- Endpoints ---

@router.get("/incidents", response_model=list[IncidentSchema])
async def list_incidents(
    severity: str | None = Query(None),
    incident_status: str | None = Query(None, alias="status"),
) -> list[dict]:
    svc = IncidentRemediationService()
    try:
        sev = IncidentSeverity(severity) if severity else None
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid severity: {severity}")
    try:
        st = RemediationStatus(incident_status) if incident_status else None
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {incident_status}")
    incidents = await svc.list_incidents(severity=sev, status=st)
    return [
        {"id": str(i.id), "title": i.title, "description": i.description,
         "source": i.source.value, "severity": i.severity.value, "status": i.status.value,
         "affected_frameworks": i.affected_frameworks, "affected_controls": i.affected_controls,
         "affected_files": i.affected_files, "cvss_score": i.cvss_score,
         "compliance_impact_score": i.compliance_impact_score,
         "remediation_pr_url": i.remediation_pr_url,
         "breach_notification_required": i.breach_notification_required,
         "detected_at": i.detected_at.isoformat()}
        for i in incidents
    ]


@router.post("/incidents", response_model=IncidentSchema, status_code=status.HTTP_201_CREATED)
async def ingest_incident(req: IngestIncidentRequest) -> dict:
    svc = IncidentRemediationService()
    try:
        source = IncidentSource(req.source)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid source: {req.source}")
    try:
        severity = IncidentSeverity(req.severity)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid severity: {req.severity}")
    i = await svc.ingest_incident(
        title=req.title, description=req.description,
        source=source, severity=severity,
    )
    return {
        "id": str(i.id), "title": i.title, "description": i.description,
        "source": i.source.value, "severity": i.severity.value, "status": i.status.value,
        "affected_frameworks": i.affected_frameworks, "affected_controls": i.affected_controls,
        "affected_files": i.affected_files, "cvss_score": i.cvss_score,
        "compliance_impact_score": i.compliance_impact_score,
        "remediation_pr_url": i.remediation_pr_url,
        "breach_notification_required": i.breach_notification_required,
        "detected_at": i.detected_at.isoformat(),
    }


@router.get("/incidents/{incident_id}/remediation", response_model=list[RemediationActionSchema])
async def get_remediation_actions(incident_id: UUID) -> list[dict]:
    svc = IncidentRemediationService()
    actions = await svc.get_remediation_actions(incident_id)
    return [
        {"id": str(a.id), "action_type": a.action_type, "description": a.description,
         "file_path": a.file_path, "code_patch": a.code_patch, "priority": a.priority,
         "estimated_effort_minutes": a.estimated_effort_minutes, "automated": a.automated}
        for a in actions
    ]


@router.get("/incidents/{incident_id}/breach-notification", response_model=BreachNotificationSchema)
async def get_breach_notification(incident_id: UUID) -> dict:
    svc = IncidentRemediationService()
    n = await svc.generate_breach_notification(incident_id)
    if not n:
        raise HTTPException(status_code=404, detail="Breach notification not found")
    return {
        "id": str(n.id), "regulation": n.regulation, "authority": n.authority,
        "deadline": n.deadline.isoformat(), "draft_text": n.draft_text,
        "affected_individuals_count": n.affected_individuals_count,
        "data_categories": n.data_categories,
    }
