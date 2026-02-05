"""API endpoints for Policy-as-Code (Rego/OPA integration)."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.policy_as_code import (
    PolicyFormat,
    PolicyGenerator,
    PolicyValidator,
    get_policy_generator,
    get_policy_validator,
)


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class PolicyRuleRequest(BaseModel):
    """Request model for a policy rule."""
    
    name: str
    description: str
    regulation: str = "Custom"
    article: str | None = None
    category: str = "data_protection"
    severity: str = "medium"
    condition: str
    remediation: str | None = None
    tags: list[str] = Field(default_factory=list)


class CreatePackageRequest(BaseModel):
    """Request to create a custom policy package."""
    
    name: str
    namespace: str = Field(
        description="Rego namespace (e.g., 'compliance.custom')"
    )
    description: str
    rules: list[PolicyRuleRequest]


class PolicyRuleResponse(BaseModel):
    """Response model for a policy rule."""
    
    id: str
    name: str
    description: str
    regulation: str
    article: str | None
    category: str
    severity: str
    condition: str
    remediation: str | None
    tags: list[str]


class PolicyPackageResponse(BaseModel):
    """Response model for a policy package."""
    
    id: str
    name: str
    namespace: str
    description: str
    version: str
    regulations: list[str]
    total_rules: int
    critical_rules: int
    created_at: str
    updated_at: str


class PolicyPackageDetailResponse(PolicyPackageResponse):
    """Detailed response with rules."""
    
    rules: list[PolicyRuleResponse]
    rego_code: str | None


class TemplateResponse(BaseModel):
    """Response model for a policy template."""
    
    id: str
    name: str
    description: str
    regulation: str
    version: str
    total_rules: int
    use_cases: list[str]
    industries: list[str]


class ValidationResultResponse(BaseModel):
    """Response model for validation result."""
    
    id: str
    policy_id: str
    valid: bool
    errors: list[str]
    warnings: list[str]
    syntax_valid: bool
    semantic_valid: bool
    tests_run: int
    tests_passed: int
    validated_at: str


class EvaluateRequest(BaseModel):
    """Request to evaluate a policy."""
    
    package_id: str
    input_data: dict[str, Any] = Field(
        description="Input data to evaluate against the policy"
    )


class EvaluateResponse(BaseModel):
    """Response from policy evaluation."""
    
    allow: bool
    violations: list[dict[str, Any]]
    compliance_score: float | None
    evaluated_at: str


# ============================================================================
# Template Endpoints
# ============================================================================


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[TemplateResponse]:
    """List available compliance policy templates.
    
    Pre-built templates are available for common regulations:
    - GDPR (data protection, privacy)
    - HIPAA (healthcare)
    - PCI-DSS (payment card)
    - EU AI Act (AI governance)
    """
    generator = get_policy_generator()
    templates = await generator.get_templates()
    
    return [
        TemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            regulation=t.regulation,
            version=t.version,
            total_rules=len(t.rules),
            use_cases=t.use_cases,
            industries=t.industries,
        )
        for t in templates
    ]


@router.get("/templates/{regulation}", response_model=TemplateResponse)
async def get_template(
    regulation: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> TemplateResponse:
    """Get a specific compliance policy template by regulation."""
    generator = get_policy_generator()
    template = await generator.get_template(regulation)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No template found for regulation: {regulation}",
        )
    
    return TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        regulation=template.regulation,
        version=template.version,
        total_rules=len(template.rules),
        use_cases=template.use_cases,
        industries=template.industries,
    )


@router.post("/templates/{regulation}/instantiate", response_model=PolicyPackageDetailResponse)
async def instantiate_template(
    regulation: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PolicyPackageDetailResponse:
    """Create a policy package from a pre-built template.
    
    This generates ready-to-use Rego policies for the specified regulation.
    """
    generator = get_policy_generator()
    
    try:
        package = await generator.create_package_from_template(
            regulation=regulation,
            organization_id=organization.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    return PolicyPackageDetailResponse(
        id=str(package.id),
        name=package.name,
        namespace=package.namespace,
        description=package.description,
        version=package.version,
        regulations=package.regulations,
        total_rules=package.total_rules,
        critical_rules=package.critical_rules,
        created_at=package.created_at.isoformat(),
        updated_at=package.updated_at.isoformat(),
        rules=[
            PolicyRuleResponse(
                id=str(r.id),
                name=r.name,
                description=r.description,
                regulation=r.regulation,
                article=r.article,
                category=r.category.value,
                severity=r.severity.value,
                condition=r.condition,
                remediation=r.remediation,
                tags=r.tags,
            )
            for r in package.rules
        ],
        rego_code=package.rego_package,
    )


# ============================================================================
# Package Endpoints
# ============================================================================


@router.get("/packages", response_model=list[PolicyPackageResponse])
async def list_packages(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[PolicyPackageResponse]:
    """List all policy packages for the organization."""
    generator = get_policy_generator()
    packages = await generator.list_packages(organization_id=organization.id)
    
    return [
        PolicyPackageResponse(
            id=str(p.id),
            name=p.name,
            namespace=p.namespace,
            description=p.description,
            version=p.version,
            regulations=p.regulations,
            total_rules=p.total_rules,
            critical_rules=p.critical_rules,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in packages
    ]


@router.post("/packages", response_model=PolicyPackageDetailResponse)
async def create_package(
    request: CreatePackageRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PolicyPackageDetailResponse:
    """Create a custom policy package.
    
    Define your own compliance rules and generate Rego policies.
    """
    generator = get_policy_generator()
    
    rules = [r.model_dump() for r in request.rules]
    
    package = await generator.create_custom_package(
        name=request.name,
        namespace=request.namespace,
        description=request.description,
        rules=rules,
        organization_id=organization.id,
    )
    
    return PolicyPackageDetailResponse(
        id=str(package.id),
        name=package.name,
        namespace=package.namespace,
        description=package.description,
        version=package.version,
        regulations=package.regulations,
        total_rules=package.total_rules,
        critical_rules=package.critical_rules,
        created_at=package.created_at.isoformat(),
        updated_at=package.updated_at.isoformat(),
        rules=[
            PolicyRuleResponse(
                id=str(r.id),
                name=r.name,
                description=r.description,
                regulation=r.regulation,
                article=r.article,
                category=r.category.value,
                severity=r.severity.value,
                condition=r.condition,
                remediation=r.remediation,
                tags=r.tags,
            )
            for r in package.rules
        ],
        rego_code=package.rego_package,
    )


@router.get("/packages/{package_id}", response_model=PolicyPackageDetailResponse)
async def get_package(
    package_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PolicyPackageDetailResponse:
    """Get a policy package by ID."""
    generator = get_policy_generator()
    
    try:
        pkg_uuid = UUID(package_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid package ID format",
        )
    
    package = await generator.get_package(pkg_uuid)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found",
        )
    
    return PolicyPackageDetailResponse(
        id=str(package.id),
        name=package.name,
        namespace=package.namespace,
        description=package.description,
        version=package.version,
        regulations=package.regulations,
        total_rules=package.total_rules,
        critical_rules=package.critical_rules,
        created_at=package.created_at.isoformat(),
        updated_at=package.updated_at.isoformat(),
        rules=[
            PolicyRuleResponse(
                id=str(r.id),
                name=r.name,
                description=r.description,
                regulation=r.regulation,
                article=r.article,
                category=r.category.value,
                severity=r.severity.value,
                condition=r.condition,
                remediation=r.remediation,
                tags=r.tags,
            )
            for r in package.rules
        ],
        rego_code=package.rego_package,
    )


@router.get("/packages/{package_id}/export")
async def export_package(
    package_id: str,
    format: str = "raw",
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Export a policy package in the specified format.
    
    Supported formats:
    - raw: Raw Rego code
    - opa-bundle: OPA bundle format
    - conftest: Conftest CI/CD format
    - gatekeeper: Kubernetes Gatekeeper format
    - kyverno: Kyverno policy format
    """
    generator = get_policy_generator()
    
    try:
        pkg_uuid = UUID(package_id)
        format_enum = PolicyFormat(format)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid package ID or format",
        )
    
    try:
        return await generator.export_package(pkg_uuid, format_enum)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# Validation Endpoints
# ============================================================================


@router.post("/packages/{package_id}/validate", response_model=ValidationResultResponse)
async def validate_package(
    package_id: str,
    run_tests: bool = True,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> ValidationResultResponse:
    """Validate a policy package.
    
    Performs syntax and semantic validation, and optionally runs test cases.
    Requires OPA CLI for full validation (falls back to basic checks).
    """
    generator = get_policy_generator()
    validator = get_policy_validator()
    
    try:
        pkg_uuid = UUID(package_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid package ID format",
        )
    
    package = await generator.get_package(pkg_uuid)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found",
        )
    
    result = await validator.validate_package(package, run_tests=run_tests)
    
    return ValidationResultResponse(
        id=str(result.id),
        policy_id=str(result.policy_id),
        valid=result.valid,
        errors=result.errors,
        warnings=result.warnings,
        syntax_valid=result.syntax_valid,
        semantic_valid=result.semantic_valid,
        tests_run=result.tests_run,
        tests_passed=result.tests_passed,
        validated_at=result.validated_at.isoformat(),
    )


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_policy(
    request: EvaluateRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> EvaluateResponse:
    """Evaluate input data against a policy package.
    
    Returns compliance result (allow/deny), violations, and score.
    """
    from datetime import datetime
    
    generator = get_policy_generator()
    validator = get_policy_validator()
    
    try:
        pkg_uuid = UUID(request.package_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid package ID format",
        )
    
    package = await generator.get_package(pkg_uuid)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found",
        )
    
    result = await validator.evaluate_policy(package, request.input_data)
    
    return EvaluateResponse(
        allow=result.get("allow", False),
        violations=result.get("violations", []),
        compliance_score=result.get("compliance_score"),
        evaluated_at=datetime.utcnow().isoformat(),
    )


# ============================================================================
# Quick Actions
# ============================================================================


@router.post("/quick-generate")
async def quick_generate(
    regulations: list[str],
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Quickly generate policies for multiple regulations.
    
    Returns combined Rego code for all specified regulations.
    """
    generator = get_policy_generator()
    packages = []
    
    for regulation in regulations:
        try:
            package = await generator.create_package_from_template(
                regulation=regulation,
                organization_id=organization.id,
            )
            packages.append(package)
        except ValueError:
            # Skip unknown regulations
            continue
    
    if not packages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No templates found for regulations: {regulations}",
        )
    
    # Combine all Rego code
    combined_rego = "\n\n".join([
        f"# {'=' * 70}\n# {p.name}\n# {'=' * 70}\n\n{p.rego_package}"
        for p in packages
        if p.rego_package
    ])
    
    return {
        "regulations": [p.regulations[0] for p in packages if p.regulations],
        "total_rules": sum(p.total_rules for p in packages),
        "critical_rules": sum(p.critical_rules for p in packages),
        "package_ids": [str(p.id) for p in packages],
        "combined_rego": combined_rego,
        "ci_integration": {
            "conftest_command": "conftest test --policy policy/ input.json",
            "opa_command": "opa eval -d policy/ -i input.json 'data.compliance.violations'",
            "github_action": """
- name: Policy Check
  run: |
    opa eval -d policy/ -i input.json 'data.compliance.violations' --fail-defined
""",
        },
    }
