"""API endpoints for Cross-Border Data Flow Mapper."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.data_flow import (
    DataClassification,
    DataFlowMapper,
    CrossBorderAnalyzer,
    get_data_flow_mapper,
    get_cross_border_analyzer,
)


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class DataLocationRequest(BaseModel):
    """Request model for adding a data location."""
    
    name: str
    description: str | None = None
    country: str
    country_code: str = Field(description="ISO 3166-1 alpha-2 country code")
    provider: str | None = None
    service: str | None = None
    data_types: list[str] = Field(default_factory=list)


class DiscoverFlowsRequest(BaseModel):
    """Request to discover data flows."""
    
    code_files: dict[str, str] | None = Field(
        default=None,
        description="Dictionary of filepath -> file content for code analysis"
    )
    infrastructure_config: dict[str, Any] | None = Field(
        default=None,
        description="Terraform, Kubernetes, or other infrastructure config"
    )
    manual_locations: list[DataLocationRequest] | None = Field(
        default=None,
        description="Manually specified data locations"
    )


class AddFlowRequest(BaseModel):
    """Request to add a manual data flow."""
    
    source_id: str
    destination_id: str
    data_types: list[str]
    purpose: str | None = None


class DataLocationResponse(BaseModel):
    """Response model for a data location."""
    
    id: str
    name: str
    description: str | None
    country: str
    country_code: str
    region: str | None
    provider: str | None
    service: str | None
    data_types: list[str]
    certifications: list[str]


class DataFlowResponse(BaseModel):
    """Response model for a data flow."""
    
    id: str
    name: str
    description: str | None
    source_name: str
    source_country: str
    destination_name: str
    destination_country: str
    data_types: list[str]
    data_categories: list[str]
    purpose: str | None
    transfer_mechanism: str
    compliance_status: str
    risk_level: str
    regulations: list[str]
    actions_required: list[str]
    detected_from: str | None


class JurisdictionConflictResponse(BaseModel):
    """Response model for a jurisdiction conflict."""
    
    id: str
    flow_id: str
    source_jurisdiction: str
    destination_jurisdiction: str
    source_regulation: str
    destination_regulation: str
    conflict_type: str
    description: str
    severity: str
    resolution_options: list[str]
    recommended_resolution: str | None


class FlowMapSummaryResponse(BaseModel):
    """Summary response for a data flow map."""
    
    id: str
    total_locations: int
    total_flows: int
    cross_border_flows: int
    compliant_flows: int
    action_required_flows: int
    critical_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int
    regions_involved: list[str]
    countries_involved: list[str]
    created_at: str
    updated_at: str


class FlowMapDetailResponse(FlowMapSummaryResponse):
    """Detailed response including locations and flows."""
    
    locations: list[DataLocationResponse]
    flows: list[DataFlowResponse]
    conflicts: list[JurisdictionConflictResponse]


class TIAResponse(BaseModel):
    """Response model for Transfer Impact Assessment."""
    
    id: str
    flow_id: str
    assessment_date: str
    source_country: str
    source_legal_framework: str
    destination_country: str
    destination_legal_framework: str
    destination_adequacy_status: str
    destination_government_access_risk: str
    overall_risk: str
    risk_factors: list[str]
    mitigating_factors: list[str]
    supplementary_measures_required: bool
    recommended_measures: list[str]
    recommended_mechanism: str
    mechanism_justification: str | None
    additional_clauses: list[str]
    approved: bool
    approver: str | None
    approval_date: str | None
    next_review_date: str | None


class AnalysisResultResponse(BaseModel):
    """Response for flow map analysis."""
    
    total_flows: int
    cross_border_flows: int
    conflicts_detected: int
    tias_required: int
    critical_issues: int
    recommendations: list[str]
    compliance_summary: dict[str, Any]


# ============================================================================
# Discovery Endpoints
# ============================================================================


@router.post("/discover", response_model=FlowMapDetailResponse)
async def discover_data_flows(
    request: DiscoverFlowsRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> FlowMapDetailResponse:
    """Discover data flows from code, infrastructure, and manual entries.
    
    Analyzes:
    - Code files for database connections, API calls, cloud services
    - Infrastructure config (Terraform, Kubernetes)
    - Manual location entries
    
    Returns a complete data flow map with compliance analysis.
    """
    mapper = get_data_flow_mapper()
    
    manual_locs = None
    if request.manual_locations:
        manual_locs = [loc.model_dump() for loc in request.manual_locations]
    
    flow_map = await mapper.discover_data_flows(
        organization_id=organization.id,
        code_files=request.code_files,
        infrastructure_config=request.infrastructure_config,
        manual_locations=manual_locs,
    )
    
    return FlowMapDetailResponse(
        id=str(flow_map.id),
        total_locations=flow_map.total_locations,
        total_flows=flow_map.total_flows,
        cross_border_flows=flow_map.cross_border_flows,
        compliant_flows=flow_map.compliant_flows,
        action_required_flows=flow_map.action_required_flows,
        critical_risks=flow_map.critical_risks,
        high_risks=flow_map.high_risks,
        medium_risks=flow_map.medium_risks,
        low_risks=flow_map.low_risks,
        regions_involved=flow_map.regions_involved,
        countries_involved=flow_map.countries_involved,
        created_at=flow_map.created_at.isoformat(),
        updated_at=flow_map.updated_at.isoformat(),
        locations=[
            DataLocationResponse(
                id=str(loc.id),
                name=loc.name,
                description=loc.description,
                country=loc.country,
                country_code=loc.country_code,
                region=loc.region,
                provider=loc.provider,
                service=loc.service,
                data_types=[dt.value for dt in loc.data_types],
                certifications=loc.certifications,
            )
            for loc in flow_map.locations
        ],
        flows=[
            DataFlowResponse(
                id=str(f.id),
                name=f.name,
                description=f.description,
                source_name=f.source_name,
                source_country=f.source_country,
                destination_name=f.destination_name,
                destination_country=f.destination_country,
                data_types=[dt.value for dt in f.data_types],
                data_categories=f.data_categories,
                purpose=f.purpose,
                transfer_mechanism=f.transfer_mechanism.value,
                compliance_status=f.compliance_status.value,
                risk_level=f.risk_level.value,
                regulations=f.regulations,
                actions_required=f.actions_required,
                detected_from=f.detected_from,
            )
            for f in flow_map.flows
        ],
        conflicts=[
            JurisdictionConflictResponse(
                id=str(c.id),
                flow_id=str(c.flow_id),
                source_jurisdiction=c.source_jurisdiction,
                destination_jurisdiction=c.destination_jurisdiction,
                source_regulation=c.source_regulation,
                destination_regulation=c.destination_regulation,
                conflict_type=c.conflict_type,
                description=c.description,
                severity=c.severity.value,
                resolution_options=c.resolution_options,
                recommended_resolution=c.recommended_resolution,
            )
            for c in flow_map.conflicts
        ],
    )


@router.get("/maps/{map_id}", response_model=FlowMapDetailResponse)
async def get_flow_map(
    map_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> FlowMapDetailResponse:
    """Get a data flow map by ID."""
    mapper = get_data_flow_mapper()
    
    try:
        map_uuid = UUID(map_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid map ID format",
        )
    
    flow_map = await mapper.get_flow_map(map_uuid)
    if not flow_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow map not found",
        )
    
    return FlowMapDetailResponse(
        id=str(flow_map.id),
        total_locations=flow_map.total_locations,
        total_flows=flow_map.total_flows,
        cross_border_flows=flow_map.cross_border_flows,
        compliant_flows=flow_map.compliant_flows,
        action_required_flows=flow_map.action_required_flows,
        critical_risks=flow_map.critical_risks,
        high_risks=flow_map.high_risks,
        medium_risks=flow_map.medium_risks,
        low_risks=flow_map.low_risks,
        regions_involved=flow_map.regions_involved,
        countries_involved=flow_map.countries_involved,
        created_at=flow_map.created_at.isoformat(),
        updated_at=flow_map.updated_at.isoformat(),
        locations=[
            DataLocationResponse(
                id=str(loc.id),
                name=loc.name,
                description=loc.description,
                country=loc.country,
                country_code=loc.country_code,
                region=loc.region,
                provider=loc.provider,
                service=loc.service,
                data_types=[dt.value for dt in loc.data_types],
                certifications=loc.certifications,
            )
            for loc in flow_map.locations
        ],
        flows=[
            DataFlowResponse(
                id=str(f.id),
                name=f.name,
                description=f.description,
                source_name=f.source_name,
                source_country=f.source_country,
                destination_name=f.destination_name,
                destination_country=f.destination_country,
                data_types=[dt.value for dt in f.data_types],
                data_categories=f.data_categories,
                purpose=f.purpose,
                transfer_mechanism=f.transfer_mechanism.value,
                compliance_status=f.compliance_status.value,
                risk_level=f.risk_level.value,
                regulations=f.regulations,
                actions_required=f.actions_required,
                detected_from=f.detected_from,
            )
            for f in flow_map.flows
        ],
        conflicts=[
            JurisdictionConflictResponse(
                id=str(c.id),
                flow_id=str(c.flow_id),
                source_jurisdiction=c.source_jurisdiction,
                destination_jurisdiction=c.destination_jurisdiction,
                source_regulation=c.source_regulation,
                destination_regulation=c.destination_regulation,
                conflict_type=c.conflict_type,
                description=c.description,
                severity=c.severity.value,
                resolution_options=c.resolution_options,
                recommended_resolution=c.recommended_resolution,
            )
            for c in flow_map.conflicts
        ],
    )


@router.post("/maps/{map_id}/flows", response_model=DataFlowResponse)
async def add_flow(
    map_id: str,
    request: AddFlowRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> DataFlowResponse:
    """Add a manual data flow to an existing map."""
    mapper = get_data_flow_mapper()
    
    try:
        map_uuid = UUID(map_id)
        source_uuid = UUID(request.source_id)
        dest_uuid = UUID(request.destination_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )
    
    flow = await mapper.add_flow(
        map_id=map_uuid,
        source_id=source_uuid,
        destination_id=dest_uuid,
        data_types=request.data_types,
        purpose=request.purpose,
    )
    
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map or locations not found",
        )
    
    return DataFlowResponse(
        id=str(flow.id),
        name=flow.name,
        description=flow.description,
        source_name=flow.source_name,
        source_country=flow.source_country,
        destination_name=flow.destination_name,
        destination_country=flow.destination_country,
        data_types=[dt.value for dt in flow.data_types],
        data_categories=flow.data_categories,
        purpose=flow.purpose,
        transfer_mechanism=flow.transfer_mechanism.value,
        compliance_status=flow.compliance_status.value,
        risk_level=flow.risk_level.value,
        regulations=flow.regulations,
        actions_required=flow.actions_required,
        detected_from=flow.detected_from,
    )


# ============================================================================
# Analysis Endpoints
# ============================================================================


@router.post("/maps/{map_id}/analyze", response_model=AnalysisResultResponse)
async def analyze_flow_map(
    map_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> AnalysisResultResponse:
    """Analyze a data flow map for compliance issues and generate TIAs.
    
    Performs:
    - Jurisdiction conflict detection
    - Transfer Impact Assessment generation
    - Risk assessment
    - Compliance recommendations
    """
    mapper = get_data_flow_mapper()
    analyzer = get_cross_border_analyzer()
    
    try:
        map_uuid = UUID(map_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid map ID format",
        )
    
    flow_map = await mapper.get_flow_map(map_uuid)
    if not flow_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow map not found",
        )
    
    result = await analyzer.analyze_flow_map(flow_map)
    
    return AnalysisResultResponse(
        total_flows=result["total_flows"],
        cross_border_flows=result["cross_border_flows"],
        conflicts_detected=result["conflicts_detected"],
        tias_required=result["tias_required"],
        critical_issues=result["critical_issues"],
        recommendations=result["recommendations"],
        compliance_summary=result["compliance_summary"],
    )


@router.get("/maps/{map_id}/tias", response_model=list[TIAResponse])
async def list_tias(
    map_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[TIAResponse]:
    """List Transfer Impact Assessments for a flow map."""
    mapper = get_data_flow_mapper()
    
    try:
        map_uuid = UUID(map_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid map ID format",
        )
    
    flow_map = await mapper.get_flow_map(map_uuid)
    if not flow_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow map not found",
        )
    
    return [
        TIAResponse(
            id=str(tia.id),
            flow_id=str(tia.flow_id),
            assessment_date=tia.assessment_date.isoformat(),
            source_country=tia.source_country,
            source_legal_framework=tia.source_legal_framework,
            destination_country=tia.destination_country,
            destination_legal_framework=tia.destination_legal_framework,
            destination_adequacy_status=tia.destination_adequacy_status.value,
            destination_government_access_risk=tia.destination_government_access_risk.value,
            overall_risk=tia.overall_risk.value,
            risk_factors=tia.risk_factors,
            mitigating_factors=tia.mitigating_factors,
            supplementary_measures_required=tia.supplementary_measures_required,
            recommended_measures=tia.recommended_measures,
            recommended_mechanism=tia.recommended_mechanism.value,
            mechanism_justification=tia.mechanism_justification,
            additional_clauses=tia.additional_clauses,
            approved=tia.approved,
            approver=tia.approver,
            approval_date=tia.approval_date.isoformat() if tia.approval_date else None,
            next_review_date=tia.next_review_date.isoformat() if tia.next_review_date else None,
        )
        for tia in flow_map.assessments
    ]


@router.post("/tias/{tia_id}/approve", response_model=TIAResponse)
async def approve_tia(
    tia_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> TIAResponse:
    """Approve a Transfer Impact Assessment."""
    analyzer = get_cross_border_analyzer()
    
    try:
        tia_uuid = UUID(tia_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TIA ID format",
        )
    
    # Use member info as approver
    approver = f"User:{member.user_id}" if hasattr(member, 'user_id') else "Authorized Approver"
    
    tia = await analyzer.approve_assessment(tia_uuid, approver)
    if not tia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TIA not found",
        )
    
    return TIAResponse(
        id=str(tia.id),
        flow_id=str(tia.flow_id),
        assessment_date=tia.assessment_date.isoformat(),
        source_country=tia.source_country,
        source_legal_framework=tia.source_legal_framework,
        destination_country=tia.destination_country,
        destination_legal_framework=tia.destination_legal_framework,
        destination_adequacy_status=tia.destination_adequacy_status.value,
        destination_government_access_risk=tia.destination_government_access_risk.value,
        overall_risk=tia.overall_risk.value,
        risk_factors=tia.risk_factors,
        mitigating_factors=tia.mitigating_factors,
        supplementary_measures_required=tia.supplementary_measures_required,
        recommended_measures=tia.recommended_measures,
        recommended_mechanism=tia.recommended_mechanism.value,
        mechanism_justification=tia.mechanism_justification,
        additional_clauses=tia.additional_clauses,
        approved=tia.approved,
        approver=tia.approver,
        approval_date=tia.approval_date.isoformat() if tia.approval_date else None,
        next_review_date=tia.next_review_date.isoformat() if tia.next_review_date else None,
    )


# ============================================================================
# Quick Actions
# ============================================================================


@router.post("/quick-scan")
async def quick_scan(
    code_files: dict[str, str],
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Quick scan code for cross-border data flow issues.
    
    Returns a summary of detected flows and compliance issues.
    Suitable for CI/CD integration.
    """
    mapper = get_data_flow_mapper()
    analyzer = get_cross_border_analyzer()
    
    flow_map = await mapper.discover_data_flows(
        organization_id=organization.id,
        code_files=code_files,
    )
    
    analysis = await analyzer.analyze_flow_map(flow_map)
    
    # Determine pass/fail
    passed = (
        analysis["critical_issues"] == 0 and
        analysis["compliance_summary"]["overall_status"] != "CRITICAL"
    )
    
    return {
        "passed": passed,
        "map_id": str(flow_map.id),
        "summary": {
            "locations_detected": flow_map.total_locations,
            "flows_detected": flow_map.total_flows,
            "cross_border_flows": flow_map.cross_border_flows,
            "compliance_status": analysis["compliance_summary"]["overall_status"],
        },
        "risks": {
            "critical": flow_map.critical_risks,
            "high": flow_map.high_risks,
            "medium": flow_map.medium_risks,
            "low": flow_map.low_risks,
        },
        "issues": {
            "conflicts": analysis["conflicts_detected"],
            "tias_needed": analysis["tias_required"],
        },
        "top_recommendations": analysis["recommendations"][:5],
        "countries": flow_map.countries_involved,
        "regions": flow_map.regions_involved,
    }


@router.get("/jurisdictions")
async def list_jurisdictions(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get jurisdiction reference data.
    
    Returns information about:
    - EEA countries
    - Adequate countries (EU adequacy decisions)
    - Data localization requirements
    - Government access risk countries
    """
    from app.services.data_flow.models import (
        EEA_COUNTRIES,
        EU_ADEQUATE_COUNTRIES,
        DATA_LOCALIZATION_COUNTRIES,
        HIGH_GOVERNMENT_ACCESS_RISK,
        JURISDICTION_REGULATIONS,
    )
    
    return {
        "eea_countries": EEA_COUNTRIES,
        "adequate_countries": EU_ADEQUATE_COUNTRIES,
        "data_localization": DATA_LOCALIZATION_COUNTRIES,
        "high_government_access_risk": HIGH_GOVERNMENT_ACCESS_RISK,
        "regulations_by_jurisdiction": JURISDICTION_REGULATIONS,
    }
