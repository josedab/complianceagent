"""API endpoints for infrastructure compliance analysis."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Path, Query
from pydantic import BaseModel, Field

from app.services.infrastructure import (
    CloudProvider,
    ComplianceViolation,
    InfrastructureAnalysisResult,
    InfrastructureResource,
    InfrastructureType,
    ViolationSeverity,
    get_infrastructure_analyzer,
)

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])


# Request/Response Models

class AnalyzeContentRequest(BaseModel):
    """Request to analyze infrastructure configuration content."""
    
    content: str = Field(..., description="Infrastructure configuration content")
    infrastructure_type: InfrastructureType = Field(
        ...,
        description="Type of infrastructure configuration",
    )
    file_path: str = Field(
        default="inline",
        description="Virtual file path for reporting",
    )
    regulations: list[str] | None = Field(
        default=None,
        description="Specific regulations to check (e.g., ['GDPR', 'SOC2'])",
    )


class AnalyzeDirectoryRequest(BaseModel):
    """Request to analyze infrastructure configurations in a directory."""
    
    directory: str = Field(..., description="Directory path to scan")
    recursive: bool = Field(
        default=True,
        description="Whether to scan subdirectories",
    )
    regulations: list[str] | None = Field(
        default=None,
        description="Specific regulations to check",
    )


class ViolationResponse(BaseModel):
    """Compliance violation response."""
    
    id: str
    rule_id: str
    rule_name: str
    severity: ViolationSeverity
    category: str
    description: str
    resource_name: str
    resource_type: str
    provider: CloudProvider
    file_path: str
    line_number: int
    regulations: list[str]
    remediation: dict[str, Any] | None = None


class ResourceResponse(BaseModel):
    """Infrastructure resource response."""
    
    id: str
    name: str
    resource_type: str
    provider: CloudProvider
    infrastructure_type: InfrastructureType
    file_path: str
    contains_pii: bool
    contains_phi: bool
    contains_pci: bool


class AnalysisResultResponse(BaseModel):
    """Infrastructure analysis result response."""
    
    id: str
    compliance_score: float
    total_resources: int
    compliant_resources: int
    non_compliant_resources: int
    violation_counts: dict[str, int]
    violations: list[ViolationResponse]
    resources: list[ResourceResponse]
    provider_breakdown: dict[str, dict[str, int]]
    category_breakdown: dict[str, dict[str, int]]
    regulation_breakdown: dict[str, dict[str, int]]
    analyzed_files: list[str]
    analysis_duration_ms: int


class PolicyRuleResponse(BaseModel):
    """Policy rule response."""
    
    id: str
    name: str
    description: str
    severity: ViolationSeverity
    category: str
    regulations: list[str]
    resource_types: list[str]
    providers: list[CloudProvider]
    remediation_guidance: str
    auto_remediation_available: bool
    enabled: bool


# Helper functions

def _violation_to_response(v: ComplianceViolation) -> ViolationResponse:
    """Convert violation to response model."""
    return ViolationResponse(
        id=str(v.id),
        rule_id=v.rule_id,
        rule_name=v.rule_name,
        severity=v.severity,
        category=v.category.value,
        description=v.description,
        resource_name=v.resource_name,
        resource_type=v.resource_type,
        provider=v.provider,
        file_path=v.file_path,
        line_number=v.line_number,
        regulations=v.regulations,
        remediation=v.remediation.to_dict() if v.remediation else None,
    )


def _resource_to_response(r: InfrastructureResource) -> ResourceResponse:
    """Convert resource to response model."""
    return ResourceResponse(
        id=str(r.id),
        name=r.name,
        resource_type=r.resource_type,
        provider=r.provider,
        infrastructure_type=r.infrastructure_type,
        file_path=r.file_path,
        contains_pii=r.contains_pii,
        contains_phi=r.contains_phi,
        contains_pci=r.contains_pci,
    )


def _result_to_response(result: InfrastructureAnalysisResult) -> AnalysisResultResponse:
    """Convert analysis result to response model."""
    return AnalysisResultResponse(
        id=str(result.id),
        compliance_score=result.compliance_score,
        total_resources=result.total_resources,
        compliant_resources=result.compliant_resources,
        non_compliant_resources=result.non_compliant_resources,
        violation_counts={
            "critical": result.critical_count,
            "high": result.high_count,
            "medium": result.medium_count,
            "low": result.low_count,
            "info": result.info_count,
        },
        violations=[_violation_to_response(v) for v in result.violations],
        resources=[_resource_to_response(r) for r in result.resources],
        provider_breakdown=result.provider_breakdown,
        category_breakdown=result.category_breakdown,
        regulation_breakdown=result.regulation_breakdown,
        analyzed_files=result.analyzed_files,
        analysis_duration_ms=result.analysis_duration_ms,
    )


# Endpoints

@router.post(
    "/analyze",
    response_model=AnalysisResultResponse,
    summary="Analyze infrastructure configuration",
    description="Analyze infrastructure configuration content for compliance violations",
)
async def analyze_infrastructure(
    request: AnalyzeContentRequest = Body(...),
) -> AnalysisResultResponse:
    """Analyze infrastructure configuration for compliance violations."""
    analyzer = get_infrastructure_analyzer()
    
    result = analyzer.analyze_content(
        content=request.content,
        infrastructure_type=request.infrastructure_type,
        file_path=request.file_path,
        regulations=request.regulations,
    )
    
    return _result_to_response(result)


@router.post(
    "/analyze/terraform",
    response_model=AnalysisResultResponse,
    summary="Analyze Terraform configuration",
    description="Analyze Terraform HCL configuration for compliance violations",
)
async def analyze_terraform(
    content: str = Body(..., embed=True, description="Terraform HCL content"),
    regulations: list[str] | None = Body(None, description="Specific regulations to check"),
) -> AnalysisResultResponse:
    """Analyze Terraform configuration for compliance."""
    analyzer = get_infrastructure_analyzer()
    
    result = analyzer.analyze_content(
        content=content,
        infrastructure_type=InfrastructureType.TERRAFORM,
        regulations=regulations,
    )
    
    return _result_to_response(result)


@router.post(
    "/analyze/kubernetes",
    response_model=AnalysisResultResponse,
    summary="Analyze Kubernetes manifest",
    description="Analyze Kubernetes YAML manifest for compliance violations",
)
async def analyze_kubernetes(
    content: str = Body(..., embed=True, description="Kubernetes YAML content"),
    regulations: list[str] | None = Body(None, description="Specific regulations to check"),
) -> AnalysisResultResponse:
    """Analyze Kubernetes manifest for compliance."""
    analyzer = get_infrastructure_analyzer()
    
    result = analyzer.analyze_content(
        content=content,
        infrastructure_type=InfrastructureType.KUBERNETES,
        regulations=regulations,
    )
    
    return _result_to_response(result)


@router.post(
    "/analyze/cloudformation",
    response_model=AnalysisResultResponse,
    summary="Analyze CloudFormation template",
    description="Analyze AWS CloudFormation template for compliance violations",
)
async def analyze_cloudformation(
    content: str = Body(..., embed=True, description="CloudFormation template content"),
    regulations: list[str] | None = Body(None, description="Specific regulations to check"),
) -> AnalysisResultResponse:
    """Analyze CloudFormation template for compliance."""
    analyzer = get_infrastructure_analyzer()
    
    result = analyzer.analyze_content(
        content=content,
        infrastructure_type=InfrastructureType.CLOUDFORMATION,
        regulations=regulations,
    )
    
    return _result_to_response(result)


@router.post(
    "/analyze/directory",
    response_model=AnalysisResultResponse,
    summary="Analyze infrastructure directory",
    description="Analyze all infrastructure files in a directory",
)
async def analyze_directory(
    request: AnalyzeDirectoryRequest = Body(...),
) -> AnalysisResultResponse:
    """Analyze all infrastructure files in a directory."""
    analyzer = get_infrastructure_analyzer()
    
    result = analyzer.analyze_directory(
        directory=request.directory,
        regulations=request.regulations,
        recursive=request.recursive,
    )
    
    return _result_to_response(result)


@router.get(
    "/policies",
    response_model=list[PolicyRuleResponse],
    summary="List policy rules",
    description="List all available compliance policy rules",
)
async def list_policy_rules(
    regulation: str | None = Query(None, description="Filter by regulation"),
    category: str | None = Query(None, description="Filter by category"),
    severity: ViolationSeverity | None = Query(None, description="Filter by severity"),
    provider: CloudProvider | None = Query(None, description="Filter by cloud provider"),
) -> list[PolicyRuleResponse]:
    """List all available policy rules."""
    analyzer = get_infrastructure_analyzer()
    rules = analyzer.get_policy_rules()
    
    # Apply filters
    filtered = rules
    
    if regulation:
        filtered = [r for r in filtered if regulation in r.regulations]
    
    if category:
        filtered = [r for r in filtered if r.category.value == category]
    
    if severity:
        filtered = [r for r in filtered if r.severity == severity]
    
    if provider:
        filtered = [r for r in filtered if provider in r.providers or not r.providers]
    
    return [
        PolicyRuleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            severity=r.severity,
            category=r.category.value,
            regulations=r.regulations,
            resource_types=r.resource_types,
            providers=r.providers,
            remediation_guidance=r.remediation_guidance,
            auto_remediation_available=r.auto_remediation_available,
            enabled=r.enabled,
        )
        for r in filtered
    ]


@router.get(
    "/policies/{rule_id}",
    response_model=PolicyRuleResponse,
    summary="Get policy rule",
    description="Get a specific policy rule by ID",
)
async def get_policy_rule(
    rule_id: str = Path(..., description="Policy rule ID"),
) -> PolicyRuleResponse:
    """Get a specific policy rule."""
    analyzer = get_infrastructure_analyzer()
    rules = analyzer.get_policy_rules()
    
    for rule in rules:
        if rule.id == rule_id:
            return PolicyRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                severity=rule.severity,
                category=rule.category.value,
                regulations=rule.regulations,
                resource_types=rule.resource_types,
                providers=rule.providers,
                remediation_guidance=rule.remediation_guidance,
                auto_remediation_available=rule.auto_remediation_available,
                enabled=rule.enabled,
            )
    
    raise HTTPException(status_code=404, detail=f"Policy rule {rule_id} not found")


@router.get(
    "/supported-types",
    summary="Get supported infrastructure types",
    description="Get list of supported infrastructure configuration types",
)
async def get_supported_types() -> dict[str, list[str]]:
    """Get supported infrastructure types."""
    return {
        "infrastructure_types": [t.value for t in InfrastructureType],
        "cloud_providers": [p.value for p in CloudProvider],
        "regulations": ["GDPR", "HIPAA", "PCI-DSS", "SOC2", "ISO27001"],
        "severity_levels": [s.value for s in ViolationSeverity],
    }
