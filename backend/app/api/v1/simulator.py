"""Regulatory scenario simulator API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization, OrgMember
from app.services.simulator import ScenarioSimulatorService
from app.services.simulator.models import (
    ArchitectureChangeScenario,
    CodeChangeScenario,
    ExpansionScenario,
    RiskCategory,
    Scenario,
    ScenarioType,
    VendorChangeScenario,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---

class CodeChangeScenarioSchema(BaseModel):
    """Code change scenario details."""
    file_path: str
    proposed_changes: str
    language: str = "python"
    affected_functions: list[str] = Field(default_factory=list)


class ArchitectureChangeScenarioSchema(BaseModel):
    """Architecture change scenario details."""
    component_name: str
    change_description: str
    affected_services: list[str] = Field(default_factory=list)
    new_data_flows: list[dict] = Field(default_factory=list)


class VendorChangeScenarioSchema(BaseModel):
    """Vendor change scenario details."""
    vendor_name: str
    vendor_type: str
    data_shared: list[str] = Field(default_factory=list)
    jurisdictions: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class ExpansionScenarioSchema(BaseModel):
    """Geographic expansion scenario details."""
    target_regions: list[str]
    data_types_affected: list[str] = Field(default_factory=list)
    user_types: list[str] = Field(default_factory=list)


class SimulateRequest(BaseModel):
    """Request to simulate a scenario."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    scenario_type: str = Field(..., description="code_change, architecture, vendor, expansion")
    repository_id: UUID | None = None
    target_frameworks: list[str] = Field(default_factory=list)
    
    # Scenario-specific details (provide one based on type)
    code_change: CodeChangeScenarioSchema | None = None
    architecture_change: ArchitectureChangeScenarioSchema | None = None
    vendor_change: VendorChangeScenarioSchema | None = None
    expansion: ExpansionScenarioSchema | None = None


class ImpactPredictionSchema(BaseModel):
    """Predicted compliance impact."""
    category: str
    severity: str
    description: str
    affected_requirements: list[str] = Field(default_factory=list)
    mitigation_suggestions: list[str] = Field(default_factory=list)
    confidence: float


class ComplianceDeltaSchema(BaseModel):
    """Change in compliance status."""
    framework: str
    current_score: float
    projected_score: float
    score_change: float
    current_grade: str
    projected_grade: str
    grade_changed: bool
    new_gaps: list[dict] = Field(default_factory=list)
    risk_categories_affected: list[str] = Field(default_factory=list)


class SimulationResultSchema(BaseModel):
    """Simulation result response."""
    scenario_id: UUID
    scenario_name: str
    scenario_type: str
    overall_risk_level: str
    recommendation: str
    summary: str
    compliance_deltas: list[ComplianceDeltaSchema] = Field(default_factory=list)
    impact_predictions: list[ImpactPredictionSchema] = Field(default_factory=list)
    blocking_issues: list[dict] = Field(default_factory=list)
    warnings: list[dict] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    estimated_remediation_hours: float
    estimated_timeline_days: int
    simulated_at: datetime
    confidence: float


# --- Helper Functions ---

def _result_to_schema(result) -> SimulationResultSchema:
    """Convert SimulationResult to response schema."""
    return SimulationResultSchema(
        scenario_id=result.scenario_id,
        scenario_name=result.scenario_name,
        scenario_type=result.scenario_type.value,
        overall_risk_level=result.overall_risk_level,
        recommendation=result.recommendation,
        summary=result.summary,
        compliance_deltas=[
            ComplianceDeltaSchema(
                framework=d.framework,
                current_score=d.current_score,
                projected_score=d.projected_score,
                score_change=d.score_change,
                current_grade=d.current_grade,
                projected_grade=d.projected_grade,
                grade_changed=d.grade_changed,
                new_gaps=d.new_gaps,
                risk_categories_affected=[c.value for c in d.risk_categories_affected],
            ) for d in result.compliance_deltas
        ],
        impact_predictions=[
            ImpactPredictionSchema(
                category=p.category.value,
                severity=p.severity,
                description=p.description,
                affected_requirements=p.affected_requirements,
                mitigation_suggestions=p.mitigation_suggestions,
                confidence=p.confidence,
            ) for p in result.impact_predictions
        ],
        blocking_issues=result.blocking_issues,
        warnings=result.warnings,
        required_actions=[a for a in result.required_actions if a],
        recommended_actions=result.recommended_actions,
        estimated_remediation_hours=result.estimated_remediation_hours,
        estimated_timeline_days=result.estimated_timeline_days,
        simulated_at=result.simulated_at,
        confidence=result.confidence,
    )


def _request_to_scenario(
    request: SimulateRequest,
    organization_id: UUID,
    user_id: UUID,
) -> Scenario:
    """Convert request to Scenario model."""
    scenario_type_map = {
        "code_change": ScenarioType.CODE_CHANGE,
        "architecture": ScenarioType.ARCHITECTURE_CHANGE,
        "vendor": ScenarioType.VENDOR_CHANGE,
        "expansion": ScenarioType.EXPANSION,
    }
    
    scenario = Scenario(
        organization_id=organization_id,
        repository_id=request.repository_id,
        name=request.name,
        description=request.description,
        scenario_type=scenario_type_map.get(request.scenario_type, ScenarioType.CODE_CHANGE),
        target_frameworks=request.target_frameworks,
        created_by=user_id,
    )
    
    if request.code_change:
        scenario.code_change = CodeChangeScenario(
            file_path=request.code_change.file_path,
            proposed_changes=request.code_change.proposed_changes,
            language=request.code_change.language,
            affected_functions=request.code_change.affected_functions,
        )
    
    if request.architecture_change:
        scenario.architecture_change = ArchitectureChangeScenario(
            component_name=request.architecture_change.component_name,
            change_description=request.architecture_change.change_description,
            affected_services=request.architecture_change.affected_services,
            new_data_flows=request.architecture_change.new_data_flows,
        )
    
    if request.vendor_change:
        scenario.vendor_change = VendorChangeScenario(
            vendor_name=request.vendor_change.vendor_name,
            vendor_type=request.vendor_change.vendor_type,
            data_shared=request.vendor_change.data_shared,
            jurisdictions=request.vendor_change.jurisdictions,
            certifications=request.vendor_change.certifications,
        )
    
    if request.expansion:
        scenario.expansion = ExpansionScenario(
            target_regions=request.expansion.target_regions,
            data_types_affected=request.expansion.data_types_affected,
            user_types=request.expansion.user_types,
        )
    
    return scenario


# --- Endpoints ---

@router.post(
    "/simulate",
    response_model=SimulationResultSchema,
    summary="Run compliance simulation",
    description="Simulate the compliance impact of a proposed change",
)
async def simulate_scenario(
    request: SimulateRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> SimulationResultSchema:
    """
    Run a what-if simulation for proposed changes.
    
    Supports several scenario types:
    - **code_change**: Analyze proposed code modifications
    - **architecture**: Evaluate architecture/system changes
    - **vendor**: Assess adding or changing vendors
    - **expansion**: Plan geographic or market expansion
    
    Returns predicted compliance impact, risks, and recommendations.
    """
    # Validate scenario type has matching details
    type_to_field = {
        "code_change": request.code_change,
        "architecture": request.architecture_change,
        "vendor": request.vendor_change,
        "expansion": request.expansion,
    }
    
    if request.scenario_type not in type_to_field:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario type: {request.scenario_type}",
        )
    
    if type_to_field.get(request.scenario_type) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing {request.scenario_type} details for scenario type",
        )
    
    # Convert to scenario model
    scenario = _request_to_scenario(request, organization.id, member.user_id)
    
    # Run simulation
    service = ScenarioSimulatorService(db=db, copilot=copilot)
    result = await service.simulate(scenario)
    
    return _result_to_schema(result)


@router.post(
    "/simulate/code",
    response_model=SimulationResultSchema,
    summary="Simulate code change",
    description="Quick simulation for code changes",
)
async def simulate_code_change(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
    code: str = Body(..., description="Proposed code to analyze"),
    language: str = Body("python", description="Programming language"),
    file_path: str = Body("unknown", description="File path"),
    frameworks: list[str] = Body(default=["GDPR", "SOC2"]),
) -> SimulationResultSchema:
    """Quick simulation endpoint for code changes."""
    request = SimulateRequest(
        name="Code Change Analysis",
        scenario_type="code_change",
        target_frameworks=frameworks,
        code_change=CodeChangeScenarioSchema(
            file_path=file_path,
            proposed_changes=code,
            language=language,
        ),
    )
    
    scenario = _request_to_scenario(request, organization.id, member.user_id)
    service = ScenarioSimulatorService(db=db, copilot=copilot)
    result = await service.simulate(scenario)
    
    return _result_to_schema(result)


@router.post(
    "/simulate/vendor",
    response_model=SimulationResultSchema,
    summary="Simulate vendor addition",
    description="Quick simulation for adding a vendor",
)
async def simulate_vendor(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
    vendor_name: str = Body(...),
    vendor_type: str = Body("saas"),
    data_shared: list[str] = Body(default=[]),
    jurisdictions: list[str] = Body(default=[]),
    certifications: list[str] = Body(default=[]),
) -> SimulationResultSchema:
    """Quick simulation endpoint for vendor changes."""
    request = SimulateRequest(
        name=f"Vendor Analysis: {vendor_name}",
        scenario_type="vendor",
        vendor_change=VendorChangeScenarioSchema(
            vendor_name=vendor_name,
            vendor_type=vendor_type,
            data_shared=data_shared,
            jurisdictions=jurisdictions,
            certifications=certifications,
        ),
    )
    
    scenario = _request_to_scenario(request, organization.id, member.user_id)
    service = ScenarioSimulatorService(db=db, copilot=copilot)
    result = await service.simulate(scenario)
    
    return _result_to_schema(result)


@router.post(
    "/simulate/expansion",
    response_model=SimulationResultSchema,
    summary="Simulate geographic expansion",
    description="Analyze compliance requirements for new regions",
)
async def simulate_expansion(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
    target_regions: list[str] = Body(...),
    data_types: list[str] = Body(default=["PII"]),
) -> SimulationResultSchema:
    """Quick simulation endpoint for geographic expansion."""
    request = SimulateRequest(
        name=f"Expansion to {', '.join(target_regions)}",
        scenario_type="expansion",
        expansion=ExpansionScenarioSchema(
            target_regions=target_regions,
            data_types_affected=data_types,
        ),
    )
    
    scenario = _request_to_scenario(request, organization.id, member.user_id)
    service = ScenarioSimulatorService(db=db, copilot=copilot)
    result = await service.simulate(scenario)
    
    return _result_to_schema(result)


@router.get(
    "/regions",
    summary="Get available regions",
    description="Get list of regions with regulatory requirements",
)
async def get_regions() -> dict:
    """Get list of supported regions and their regulations."""
    return {
        "regions": [
            {"code": "EU", "name": "European Union", "regulations": ["GDPR", "NIS2", "EU_AI_ACT"]},
            {"code": "UK", "name": "United Kingdom", "regulations": ["UK_GDPR", "DPA_2018"]},
            {"code": "US", "name": "United States", "regulations": ["HIPAA", "SOX", "FTC_ACT"]},
            {"code": "US-CA", "name": "California, US", "regulations": ["CCPA", "CPRA"]},
            {"code": "China", "name": "China", "regulations": ["PIPL", "CSL", "DSL"]},
            {"code": "India", "name": "India", "regulations": ["DPDP"]},
            {"code": "Singapore", "name": "Singapore", "regulations": ["PDPA"]},
            {"code": "Brazil", "name": "Brazil", "regulations": ["LGPD"]},
            {"code": "Japan", "name": "Japan", "regulations": ["APPI"]},
            {"code": "Australia", "name": "Australia", "regulations": ["Privacy_Act"]},
        ]
    }
