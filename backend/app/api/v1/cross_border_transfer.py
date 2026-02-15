"""API endpoints for Cross-Border Data Transfer Automation."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.cross_border_transfer import (
    CrossBorderTransferService,
    TransferMechanism,
    TransferRisk,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class DiscoverFlowsRequest(BaseModel):
    repo: str = Field(..., description="Repository to scan for data flows")
    source_jurisdiction: str = Field(default="EU")


class DataFlowSchema(BaseModel):
    id: str
    source_jurisdiction: str
    destination_jurisdiction: str
    data_categories: list[str]
    data_subjects: list[str]
    transfer_mechanism: str
    purpose: str
    volume_estimate: str
    risk_level: str
    is_compliant: bool
    services_involved: list[str]
    detected_at: str | None


class GenerateSCCRequest(BaseModel):
    flow_id: str = Field(..., description="Data flow ID")
    exporter: str = Field(default="")
    importer: str = Field(default="")


class SCCSchema(BaseModel):
    id: str
    data_flow_id: str
    module_type: str
    version: str
    parties: dict[str, str]
    annexes: list[dict[str, Any]]
    supplementary_measures: list[str]
    status: str
    generated_at: str | None


class TIASchema(BaseModel):
    id: str
    data_flow_id: str
    risk_level: str
    legal_basis_adequate: bool
    supplementary_measures_needed: list[str]
    government_access_risk: str
    encryption_in_transit: bool
    encryption_at_rest: bool
    pseudonymization_applied: bool
    recommendations: list[str]
    assessed_at: str | None


class AdequacySchema(BaseModel):
    country_code: str
    country_name: str
    status: str
    decision_reference: str
    scope: str


class TransferAlertSchema(BaseModel):
    id: str
    alert_type: str
    severity: str
    jurisdiction: str
    title: str
    description: str
    affected_flows: list[str]
    recommended_action: str
    created_at: str | None
    acknowledged: bool


class TransferReportSchema(BaseModel):
    total_flows: int
    compliant_flows: int
    non_compliant_flows: int
    flows_by_mechanism: dict[str, int]
    flows_by_risk: dict[str, int]
    jurisdictions_involved: list[str]
    active_sccs: int
    pending_tias: int
    active_alerts: int
    generated_at: str | None


class JurisdictionSchema(BaseModel):
    code: str
    name: str
    region: str
    adequacy_status: str
    data_protection_law: str
    supervisory_authority: str


# --- Endpoints ---


@router.post(
    "/discover",
    response_model=list[DataFlowSchema],
    status_code=status.HTTP_201_CREATED,
    summary="Discover cross-border data flows",
)
async def discover_data_flows(
    request: DiscoverFlowsRequest,
    db: DB,
    copilot: CopilotDep,
) -> list[DataFlowSchema]:
    """Scan a repository to discover cross-border data transfers."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    flows = await service.discover_data_flows(
        repo=request.repo,
        source_jurisdiction=request.source_jurisdiction,
    )
    return [
        DataFlowSchema(
            id=str(f.id),
            source_jurisdiction=f.source_jurisdiction,
            destination_jurisdiction=f.destination_jurisdiction,
            data_categories=f.data_categories,
            data_subjects=f.data_subjects,
            transfer_mechanism=f.transfer_mechanism.value,
            purpose=f.purpose,
            volume_estimate=f.volume_estimate,
            risk_level=f.risk_level.value,
            is_compliant=f.is_compliant,
            services_involved=f.services_involved,
            detected_at=f.detected_at.isoformat() if f.detected_at else None,
        )
        for f in flows
    ]


@router.get(
    "/flows",
    response_model=list[DataFlowSchema],
    summary="List data flows",
)
async def list_data_flows(
    db: DB,
    copilot: CopilotDep,
    source: str | None = None,
    destination: str | None = None,
) -> list[DataFlowSchema]:
    """List all cross-border data flows."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    flows = await service.list_data_flows(source=source, destination=destination)
    return [
        DataFlowSchema(
            id=str(f.id),
            source_jurisdiction=f.source_jurisdiction,
            destination_jurisdiction=f.destination_jurisdiction,
            data_categories=f.data_categories,
            data_subjects=f.data_subjects,
            transfer_mechanism=f.transfer_mechanism.value,
            purpose=f.purpose,
            volume_estimate=f.volume_estimate,
            risk_level=f.risk_level.value,
            is_compliant=f.is_compliant,
            services_involved=f.services_involved,
            detected_at=f.detected_at.isoformat() if f.detected_at else None,
        )
        for f in flows
    ]


@router.post(
    "/scc/generate",
    response_model=SCCSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Standard Contractual Clauses",
)
async def generate_scc(
    request: GenerateSCCRequest,
    db: DB,
    copilot: CopilotDep,
) -> SCCSchema:
    """Generate SCCs for a data flow."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    scc = await service.generate_scc(
        flow_id=UUID(request.flow_id),
        exporter=request.exporter,
        importer=request.importer,
    )
    return SCCSchema(
        id=str(scc.id),
        data_flow_id=str(scc.data_flow_id),
        module_type=scc.module_type,
        version=scc.version,
        parties=scc.parties,
        annexes=scc.annexes,
        supplementary_measures=scc.supplementary_measures,
        status=scc.status,
        generated_at=scc.generated_at.isoformat() if scc.generated_at else None,
    )


@router.get(
    "/scc",
    response_model=list[SCCSchema],
    summary="List all SCC documents",
)
async def list_sccs(db: DB, copilot: CopilotDep) -> list[SCCSchema]:
    """List all generated SCC documents."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    sccs = await service.list_sccs()
    return [
        SCCSchema(
            id=str(s.id),
            data_flow_id=str(s.data_flow_id),
            module_type=s.module_type,
            version=s.version,
            parties=s.parties,
            annexes=s.annexes,
            supplementary_measures=s.supplementary_measures,
            status=s.status,
            generated_at=s.generated_at.isoformat() if s.generated_at else None,
        )
        for s in sccs
    ]


@router.post(
    "/tia/{flow_id}",
    response_model=TIASchema,
    status_code=status.HTTP_201_CREATED,
    summary="Run Transfer Impact Assessment",
)
async def run_tia(
    flow_id: UUID,
    db: DB,
    copilot: CopilotDep,
) -> TIASchema:
    """Run a Transfer Impact Assessment for a data flow."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    tia = await service.run_transfer_impact_assessment(flow_id)
    return TIASchema(
        id=str(tia.id),
        data_flow_id=str(tia.data_flow_id),
        risk_level=tia.risk_level.value,
        legal_basis_adequate=tia.legal_basis_adequate,
        supplementary_measures_needed=tia.supplementary_measures_needed,
        government_access_risk=tia.government_access_risk,
        encryption_in_transit=tia.encryption_in_transit,
        encryption_at_rest=tia.encryption_at_rest,
        pseudonymization_applied=tia.pseudonymization_applied,
        recommendations=tia.recommendations,
        assessed_at=tia.assessed_at.isoformat() if tia.assessed_at else None,
    )


@router.get(
    "/adequacy",
    response_model=list[AdequacySchema],
    summary="Get adequacy decisions",
)
async def get_adequacy_decisions(db: DB, copilot: CopilotDep) -> list[AdequacySchema]:
    """Get all known EDPB/EC adequacy decisions."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    decisions = await service.get_adequacy_decisions()
    return [
        AdequacySchema(
            country_code=d.country_code,
            country_name=d.country_name,
            status=d.status.value,
            decision_reference=d.decision_reference,
            scope=d.scope,
        )
        for d in decisions
    ]


@router.get(
    "/adequacy/{country_code}",
    response_model=AdequacySchema,
    summary="Get adequacy decision for country",
)
async def get_adequacy_decision(
    country_code: str,
    db: DB,
    copilot: CopilotDep,
) -> AdequacySchema:
    """Get adequacy decision for a specific country."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    decision = await service.get_adequacy_decision(country_code)
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Country not found")
    return AdequacySchema(
        country_code=decision.country_code,
        country_name=decision.country_name,
        status=decision.status.value,
        decision_reference=decision.decision_reference,
        scope=decision.scope,
    )


@router.get(
    "/alerts",
    response_model=list[TransferAlertSchema],
    summary="Get transfer alerts",
)
async def get_alerts(db: DB, copilot: CopilotDep) -> list[TransferAlertSchema]:
    """Get all active transfer alerts."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    alerts = await service.get_alerts(acknowledged=False)
    return [
        TransferAlertSchema(
            id=str(a.id),
            alert_type=a.alert_type,
            severity=a.severity.value,
            jurisdiction=a.jurisdiction,
            title=a.title,
            description=a.description,
            affected_flows=a.affected_flows,
            recommended_action=a.recommended_action,
            created_at=a.created_at.isoformat() if a.created_at else None,
            acknowledged=a.acknowledged,
        )
        for a in alerts
    ]


@router.post(
    "/alerts/{alert_id}/acknowledge",
    summary="Acknowledge an alert",
)
async def acknowledge_alert(
    alert_id: UUID,
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Acknowledge a transfer alert."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    alert = await service.acknowledge_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return {"status": "acknowledged", "alert_id": str(alert_id)}


@router.get(
    "/report",
    response_model=TransferReportSchema,
    summary="Get transfer compliance report",
)
async def get_report(db: DB, copilot: CopilotDep) -> TransferReportSchema:
    """Generate a summary report of cross-border data transfers."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    report = await service.get_report()
    return TransferReportSchema(
        total_flows=report.total_flows,
        compliant_flows=report.compliant_flows,
        non_compliant_flows=report.non_compliant_flows,
        flows_by_mechanism=report.flows_by_mechanism,
        flows_by_risk=report.flows_by_risk,
        jurisdictions_involved=report.jurisdictions_involved,
        active_sccs=report.active_sccs,
        pending_tias=report.pending_tias,
        active_alerts=report.active_alerts,
        generated_at=report.generated_at.isoformat() if report.generated_at else None,
    )


@router.get(
    "/jurisdictions",
    response_model=list[JurisdictionSchema],
    summary="List jurisdictions",
)
async def list_jurisdictions(db: DB, copilot: CopilotDep) -> list[JurisdictionSchema]:
    """List all jurisdictions with adequacy information."""
    service = CrossBorderTransferService(db=db, copilot_client=copilot)
    jurisdictions = await service.get_jurisdictions()
    return [
        JurisdictionSchema(
            code=j.code,
            name=j.name,
            region=j.region,
            adequacy_status=j.adequacy_status.value,
            data_protection_law=j.data_protection_law,
            supervisory_authority=j.supervisory_authority,
        )
        for j in jurisdictions
    ]
