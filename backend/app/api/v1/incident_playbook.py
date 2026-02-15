"""API endpoints for Incident Response Compliance Playbook."""

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.v1.deps import DB, CopilotDep
from app.services.incident_playbook import (
    IncidentPlaybookService,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)


logger = structlog.get_logger()
router = APIRouter()


class PlaybookSchema(BaseModel):
    id: str
    name: str
    incident_type: str
    description: str
    steps: list[dict]
    notification_requirements: list[dict]
    evidence_checklist: list[str]
    status: str
    jurisdictions: list[str]
    created_at: str | None


class IncidentSchema(BaseModel):
    id: str
    playbook_id: str
    incident_type: str
    severity: str
    title: str
    description: str
    status: str
    affected_data_subjects: int
    jurisdictions_affected: list[str]
    timeline: list[dict]
    evidence_collected: list[str]
    notifications_sent: list[dict]
    started_at: str | None
    resolved_at: str | None


class CreateIncidentRequest(BaseModel):
    playbook_id: str
    severity: str
    title: str
    description: str
    affected_subjects: int
    jurisdictions: list[str]


class UpdateStatusRequest(BaseModel):
    status: str


class AddEvidenceRequest(BaseModel):
    evidence_item: str


class NotificationSchema(BaseModel):
    jurisdiction: str
    authority: str
    deadline_hours: int
    template: str
    data_required: list[str]


class IncidentReportSchema(BaseModel):
    id: str
    incident_id: str
    incident_type: str
    severity: str
    total_duration_hours: float
    notifications_compliant: bool
    evidence_complete: bool
    timeline: list[dict]
    lessons_learned: list[str]
    generated_at: str | None


def _incident_to_schema(inc) -> IncidentSchema:
    return IncidentSchema(
        id=str(inc.id),
        playbook_id=str(inc.playbook_id),
        incident_type=inc.incident_type.value,
        severity=inc.severity.value,
        title=inc.title,
        description=inc.description,
        status=inc.status.value,
        affected_data_subjects=inc.affected_data_subjects,
        jurisdictions_affected=inc.jurisdictions_affected,
        timeline=inc.timeline,
        evidence_collected=inc.evidence_collected,
        notifications_sent=inc.notifications_sent,
        started_at=inc.started_at.isoformat() if inc.started_at else None,
        resolved_at=inc.resolved_at.isoformat() if inc.resolved_at else None,
    )


def _parse_incident_type(it: str) -> IncidentType:
    try:
        return IncidentType(it)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid incident type: {it}. Use: {[t.value for t in IncidentType]}",
        )


def _parse_severity(s: str) -> IncidentSeverity:
    try:
        return IncidentSeverity(s)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity: {s}. Use: {[v.value for v in IncidentSeverity]}",
        )


def _parse_status(s: str) -> IncidentStatus:
    try:
        return IncidentStatus(s)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid status: {s}. Use: {[v.value for v in IncidentStatus]}"
        )


@router.get("/playbooks", response_model=list[PlaybookSchema], summary="List playbooks")
async def list_playbooks(
    db: DB, copilot: CopilotDep, incident_type: str | None = None
) -> list[PlaybookSchema]:
    service = IncidentPlaybookService(db=db, copilot_client=copilot)
    it = _parse_incident_type(incident_type) if incident_type else None
    playbooks = await service.list_playbooks(it)
    return [
        PlaybookSchema(
            id=str(p.id),
            name=p.name,
            incident_type=p.incident_type.value,
            description=p.description,
            steps=p.steps,
            notification_requirements=p.notification_requirements,
            evidence_checklist=p.evidence_checklist,
            status=p.status.value,
            jurisdictions=p.jurisdictions,
            created_at=p.created_at.isoformat() if p.created_at else None,
        )
        for p in playbooks
    ]


@router.get("/playbooks/{playbook_id}", response_model=PlaybookSchema, summary="Get playbook")
async def get_playbook(playbook_id: str, db: DB, copilot: CopilotDep) -> PlaybookSchema:
    service = IncidentPlaybookService(db=db, copilot_client=copilot)
    try:
        from uuid import UUID

        p = await service.get_playbook(UUID(playbook_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PlaybookSchema(
        id=str(p.id),
        name=p.name,
        incident_type=p.incident_type.value,
        description=p.description,
        steps=p.steps,
        notification_requirements=p.notification_requirements,
        evidence_checklist=p.evidence_checklist,
        status=p.status.value,
        jurisdictions=p.jurisdictions,
        created_at=p.created_at.isoformat() if p.created_at else None,
    )


@router.post("/incidents", response_model=IncidentSchema, summary="Create incident")
async def create_incident(
    req: CreateIncidentRequest, db: DB, copilot: CopilotDep
) -> IncidentSchema:
    severity = _parse_severity(req.severity)
    service = IncidentPlaybookService(db=db, copilot_client=copilot)
    try:
        from uuid import UUID

        incident = await service.create_incident(
            UUID(req.playbook_id),
            severity,
            req.title,
            req.description,
            req.affected_subjects,
            req.jurisdictions,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _incident_to_schema(incident)


@router.patch(
    "/incidents/{incident_id}/status",
    response_model=IncidentSchema,
    summary="Update incident status",
)
async def update_incident_status(
    incident_id: str,
    req: UpdateStatusRequest,
    db: DB,
    copilot: CopilotDep,
) -> IncidentSchema:
    status = _parse_status(req.status)
    service = IncidentPlaybookService(db=db, copilot_client=copilot)
    try:
        from uuid import UUID

        incident = await service.update_incident_status(UUID(incident_id), status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _incident_to_schema(incident)


@router.post(
    "/incidents/{incident_id}/evidence", response_model=IncidentSchema, summary="Add evidence"
)
async def add_evidence(
    incident_id: str,
    req: AddEvidenceRequest,
    db: DB,
    copilot: CopilotDep,
) -> IncidentSchema:
    service = IncidentPlaybookService(db=db, copilot_client=copilot)
    try:
        from uuid import UUID

        incident = await service.add_evidence(UUID(incident_id), req.evidence_item)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _incident_to_schema(incident)


@router.get(
    "/incidents/{incident_id}/notifications",
    response_model=list[NotificationSchema],
    summary="Get notification requirements",
)
async def get_notification_requirements(
    incident_id: str, db: DB, copilot: CopilotDep
) -> list[NotificationSchema]:
    service = IncidentPlaybookService(db=db, copilot_client=copilot)
    try:
        from uuid import UUID

        reqs = await service.get_notification_requirements(UUID(incident_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [
        NotificationSchema(
            jurisdiction=r.jurisdiction,
            authority=r.authority,
            deadline_hours=r.deadline_hours,
            template=r.template,
            data_required=r.data_required,
        )
        for r in reqs
    ]


@router.post(
    "/incidents/{incident_id}/report",
    response_model=IncidentReportSchema,
    summary="Generate incident report",
)
async def generate_incident_report(
    incident_id: str, db: DB, copilot: CopilotDep
) -> IncidentReportSchema:
    service = IncidentPlaybookService(db=db, copilot_client=copilot)
    try:
        from uuid import UUID

        report = await service.generate_incident_report(UUID(incident_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return IncidentReportSchema(
        id=str(report.id),
        incident_id=str(report.incident_id),
        incident_type=report.incident_type,
        severity=report.severity,
        total_duration_hours=report.total_duration_hours,
        notifications_compliant=report.notifications_compliant,
        evidence_complete=report.evidence_complete,
        timeline=report.timeline,
        lessons_learned=report.lessons_learned,
        generated_at=report.generated_at.isoformat() if report.generated_at else None,
    )


@router.get("/incidents", response_model=list[IncidentSchema], summary="List incidents")
async def list_incidents(
    db: DB, copilot: CopilotDep, status: str | None = None
) -> list[IncidentSchema]:
    service = IncidentPlaybookService(db=db, copilot_client=copilot)
    st = _parse_status(status) if status else None
    incidents = await service.list_incidents(st)
    return [_incident_to_schema(i) for i in incidents]
