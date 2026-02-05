"""API endpoints for Enhanced Digital Twin - Time Travel, Drift, Breach Simulation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.digital_twin.enhanced import (
    EnhancedDigitalTwin,
    BreachScenario,
    get_enhanced_digital_twin,
)


router = APIRouter()


# Request/Response Models
class TimelinePeriodRequest(BaseModel):
    start_date: str
    end_date: str


class BreachSimulationRequest(BaseModel):
    scenario: str  # data_exfiltration, ransomware, etc.
    parameters: dict[str, Any] = Field(default_factory=dict)


class TimelinePointResponse(BaseModel):
    timestamp: str
    snapshot_id: str | None
    score: float
    status: str


class DriftEventResponse(BaseModel):
    id: str
    drift_type: str
    detected_at: str
    severity: str
    description: str
    affected_regulations: list[str]
    score_delta: float


class BreachImpactResponse(BaseModel):
    id: str
    scenario: str
    data_types_affected: list[str]
    records_at_risk: int
    notification_deadline_hours: int
    estimated_fine_min: float
    estimated_fine_max: float
    estimated_downtime_hours: float
    compliance_score_impact: float
    breach_cost_estimate: float
    required_remediation: list[str]


# =====================
# TIME TRAVEL ENDPOINTS
# =====================

@router.get("/timeline")
async def get_compliance_timeline(
    start_date: str | None = None,
    end_date: str | None = None,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Get compliance timeline showing score evolution over time."""
    twin = get_enhanced_digital_twin()
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    timeline = await twin.get_compliance_timeline(
        organization_id=organization.id,
        start_date=start,
        end_date=end,
    )
    
    return {
        "organization_id": str(organization.id),
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "points": [
            TimelinePointResponse(
                timestamp=p.timestamp.isoformat(),
                snapshot_id=str(p.snapshot_id) if p.snapshot_id else None,
                score=p.score,
                status=p.status,
            ).model_dump()
            for p in timeline
        ],
        "total_points": len(timeline),
    }


@router.get("/point-in-time")
async def get_compliance_at_time(
    target_time: str,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Get compliance state at a specific point in time (time travel)."""
    twin = get_enhanced_digital_twin()
    
    target = datetime.fromisoformat(target_time)
    snapshot = await twin.get_compliance_at_point_in_time(
        organization_id=organization.id,
        target_time=target,
    )
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="No snapshot found for target time")
    
    return {
        "target_time": target.isoformat(),
        "snapshot_time": snapshot.created_at.isoformat(),
        "snapshot_id": str(snapshot.id),
        "score": snapshot.overall_score,
        "status": snapshot.overall_status.value if snapshot.overall_status else "unknown",
        "issues_count": len(snapshot.issues),
        "regulations": [
            {
                "regulation": r.regulation,
                "score": r.score,
                "status": r.status.value,
            }
            for r in snapshot.regulations
        ],
    }


@router.post("/compare-periods")
async def compare_time_periods(
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Compare compliance between two time periods."""
    twin = get_enhanced_digital_twin()
    
    comparison = await twin.compare_time_periods(
        organization_id=organization.id,
        period1_start=datetime.fromisoformat(period1_start),
        period1_end=datetime.fromisoformat(period1_end),
        period2_start=datetime.fromisoformat(period2_start),
        period2_end=datetime.fromisoformat(period2_end),
    )
    
    return comparison


# =====================
# DRIFT DETECTION ENDPOINTS
# =====================

@router.post("/drift/detect")
async def detect_compliance_drift(
    threshold: float = 0.05,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Detect compliance drift by comparing recent snapshots."""
    twin = get_enhanced_digital_twin()
    
    drift_events = await twin.detect_drift(
        organization_id=organization.id,
        threshold=threshold,
    )
    
    return {
        "organization_id": str(organization.id),
        "drift_detected": len(drift_events) > 0,
        "drift_count": len(drift_events),
        "events": [
            DriftEventResponse(
                id=str(e.id),
                drift_type=e.drift_type.value,
                detected_at=e.detected_at.isoformat(),
                severity=e.severity,
                description=e.description,
                affected_regulations=e.affected_regulations,
                score_delta=e.score_delta,
            ).model_dump()
            for e in drift_events
        ],
    }


@router.get("/drift/history")
async def get_drift_history(
    limit: int = 50,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Get drift event history."""
    twin = get_enhanced_digital_twin()
    
    events = await twin.get_drift_history(
        organization_id=organization.id,
        limit=limit,
    )
    
    return {
        "organization_id": str(organization.id),
        "total_events": len(events),
        "events": [
            DriftEventResponse(
                id=str(e.id),
                drift_type=e.drift_type.value,
                detected_at=e.detected_at.isoformat(),
                severity=e.severity,
                description=e.description,
                affected_regulations=e.affected_regulations,
                score_delta=e.score_delta,
            ).model_dump()
            for e in events
        ],
    }


@router.post("/drift/auto-remediation")
async def configure_auto_remediation(
    enabled: bool = True,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Enable or disable automatic drift remediation."""
    twin = get_enhanced_digital_twin()
    
    result = await twin.enable_auto_remediation(
        organization_id=organization.id,
        enabled=enabled,
    )
    
    return {
        "organization_id": str(organization.id),
        "auto_remediation_enabled": result,
    }


# =====================
# BREACH SIMULATION ENDPOINTS
# =====================

@router.post("/breach/simulate", response_model=BreachImpactResponse)
async def simulate_breach(
    request: BreachSimulationRequest,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> BreachImpactResponse:
    """Simulate a breach scenario and assess compliance impact."""
    twin = get_enhanced_digital_twin()
    
    try:
        scenario = BreachScenario(request.scenario)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Valid options: {[s.value for s in BreachScenario]}",
        )
    
    impact = await twin.simulate_breach(
        organization_id=organization.id,
        scenario=scenario,
        parameters=request.parameters,
    )
    
    return BreachImpactResponse(
        id=str(impact.id),
        scenario=impact.scenario.value,
        data_types_affected=impact.data_types_affected,
        records_at_risk=impact.records_at_risk,
        notification_deadline_hours=impact.notification_deadline_hours,
        estimated_fine_min=impact.estimated_fine_range[0],
        estimated_fine_max=impact.estimated_fine_range[1],
        estimated_downtime_hours=impact.estimated_downtime_hours,
        compliance_score_impact=impact.compliance_score_impact,
        breach_cost_estimate=impact.breach_cost_estimate,
        required_remediation=impact.required_remediation,
    )


@router.get("/breach/scenarios")
async def list_breach_scenarios(
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """List available breach scenarios for simulation."""
    scenarios = [
        {
            "id": BreachScenario.DATA_EXFILTRATION.value,
            "name": "Data Exfiltration",
            "description": "Unauthorized extraction of sensitive data",
            "parameters": ["records_affected", "data_types", "systems"],
        },
        {
            "id": BreachScenario.RANSOMWARE.value,
            "name": "Ransomware Attack",
            "description": "Encryption of systems with ransom demand",
            "parameters": ["systems", "ransom_demand", "records"],
        },
        {
            "id": BreachScenario.INSIDER_THREAT.value,
            "name": "Insider Threat",
            "description": "Malicious or negligent insider activity",
            "parameters": ["data_types", "records"],
        },
        {
            "id": BreachScenario.API_BREACH.value,
            "name": "API Security Breach",
            "description": "Exploitation of API vulnerabilities",
            "parameters": ["records"],
        },
        {
            "id": BreachScenario.THIRD_PARTY_COMPROMISE.value,
            "name": "Third-Party Compromise",
            "description": "Breach through vendor/partner systems",
            "parameters": ["vendor", "records"],
        },
        {
            "id": BreachScenario.SUPPLY_CHAIN_ATTACK.value,
            "name": "Supply Chain Attack",
            "description": "Compromised software dependency",
            "parameters": ["records"],
        },
    ]
    
    return {"scenarios": scenarios}


@router.get("/breach/simulations")
async def list_breach_simulations(
    limit: int = 20,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """List recent breach simulations."""
    twin = get_enhanced_digital_twin()
    
    simulations = await twin.list_breach_simulations(limit=limit)
    
    return {
        "total": len(simulations),
        "simulations": [
            {
                "id": str(s.id),
                "scenario": s.scenario.value,
                "simulated_at": s.simulated_at.isoformat(),
                "records_at_risk": s.records_at_risk,
                "breach_cost_estimate": s.breach_cost_estimate,
            }
            for s in simulations
        ],
    }
