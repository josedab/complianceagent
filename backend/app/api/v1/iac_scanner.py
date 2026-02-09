"""API endpoints for Multi-Cloud IaC Compliance Scanner."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.iac_scanner import (
    CloudProvider,
    IaCPlatform,
    IaCScannerService,
    ScanConfiguration,
    ViolationSeverity,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class ScanRepositoryRequest(BaseModel):
    """Request to scan a repository's IaC files."""

    org_id: str = Field(..., description="Organization ID")
    repo_url: str = Field(..., description="Repository URL")
    platforms: list[str] = Field(default_factory=lambda: ["terraform"])
    providers: list[str] = Field(default_factory=lambda: ["aws"])
    regulations: list[str] = Field(default_factory=list)
    severity_threshold: str = Field(default="low")
    ignore_rules: list[str] = Field(default_factory=list)


class ScanFileRequest(BaseModel):
    """Request to scan a single IaC file."""

    content: str = Field(..., description="File content")
    platform: str = Field(..., description="IaC platform (terraform, cloudformation, kubernetes)")
    filename: str = Field(default="main.tf", description="Filename")


class ScanDiffRequest(BaseModel):
    """Request to scan a PR diff."""

    org_id: str = Field(..., description="Organization ID")
    diff_content: str = Field(..., description="PR diff content")
    platform: str = Field(default="terraform")
    base_branch: str = Field(default="main")


class ViolationSchema(BaseModel):
    """Violation response."""

    id: str
    rule_id: str
    severity: str
    resource_type: str
    resource_name: str
    file_path: str
    line_number: int
    description: str
    regulation: str
    article: str
    fix_suggestion: str
    auto_fixable: bool


class ScanSummarySchema(BaseModel):
    """Scan summary response."""

    total_resources: int
    total_violations: int
    critical: int
    high: int
    medium: int
    low: int
    compliance_score: float
    top_violations: list[str]


class ScanResultSchema(BaseModel):
    """Scan result response."""

    id: str
    org_id: str
    platform: str
    provider: str
    files_scanned: int
    violations: list[ViolationSchema]
    summary: ScanSummarySchema
    scanned_at: str | None
    duration_ms: int


class FixSuggestionSchema(BaseModel):
    """Fix suggestion response."""

    violation_id: str
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float


class ComplianceRuleSchema(BaseModel):
    """Compliance rule response."""

    id: str
    name: str
    description: str
    platform: str
    provider: str
    resource_type: str
    severity: str
    regulation: str
    article: str
    fix_template: str
    enabled: bool


class PlatformInfoSchema(BaseModel):
    """Supported platform information."""

    name: str
    value: str
    providers: list[str]


# --- Helpers ---


def _violation_to_schema(v: Any) -> ViolationSchema:
    """Convert a violation dataclass to response schema."""
    return ViolationSchema(
        id=str(v.id), rule_id=v.rule_id, severity=v.severity.value,
        resource_type=v.resource_type.value, resource_name=v.resource_name,
        file_path=v.file_path, line_number=v.line_number,
        description=v.description, regulation=v.regulation,
        article=v.article, fix_suggestion=v.fix_suggestion,
        auto_fixable=v.auto_fixable,
    )


def _result_to_schema(result: Any) -> ScanResultSchema:
    """Convert a scan result dataclass to response schema."""
    return ScanResultSchema(
        id=str(result.id), org_id=result.org_id,
        platform=result.platform.value, provider=result.provider.value,
        files_scanned=result.files_scanned,
        violations=[_violation_to_schema(v) for v in result.violations],
        summary=ScanSummarySchema(
            total_resources=result.summary.total_resources,
            total_violations=result.summary.total_violations,
            critical=result.summary.critical, high=result.summary.high,
            medium=result.summary.medium, low=result.summary.low,
            compliance_score=result.summary.compliance_score,
            top_violations=result.summary.top_violations,
        ),
        scanned_at=result.scanned_at.isoformat() if result.scanned_at else None,
        duration_ms=result.duration_ms,
    )


# --- Endpoints ---


@router.post(
    "/scan/repository",
    response_model=ScanResultSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Scan a repository's IaC files",
)
async def scan_repository(request: ScanRepositoryRequest, db: DB) -> ScanResultSchema:
    """Scan a repository for IaC compliance violations."""
    config = ScanConfiguration(
        platforms=[IaCPlatform(p) for p in request.platforms],
        providers=[CloudProvider(p) for p in request.providers],
        regulations=request.regulations,
        severity_threshold=ViolationSeverity(request.severity_threshold),
        ignore_rules=request.ignore_rules,
    )
    service = IaCScannerService(db=db)
    result = await service.scan_repository(
        org_id=request.org_id, repo_url=request.repo_url, config=config,
    )
    return _result_to_schema(result)


@router.post(
    "/scan/file",
    response_model=list[ViolationSchema],
    summary="Scan a single IaC file",
)
async def scan_file(request: ScanFileRequest, db: DB) -> list[ViolationSchema]:
    """Scan a single IaC file for compliance violations."""
    service = IaCScannerService(db=db)
    platform = IaCPlatform(request.platform)
    violations = await service.scan_file(
        content=request.content, platform=platform, filename=request.filename,
    )
    return [_violation_to_schema(v) for v in violations]


@router.get(
    "/results",
    response_model=list[ScanResultSchema],
    summary="List scan results",
)
async def list_results(
    db: DB,
    org_id: str = "",
    limit: int = 20,
) -> list[ScanResultSchema]:
    """List scan results for an organization."""
    service = IaCScannerService(db=db)
    results = await service.get_scan_results(org_id=org_id, limit=limit)
    return [_result_to_schema(r) for r in results]


@router.get(
    "/results/{scan_id}",
    response_model=ScanResultSchema,
    summary="Get scan result details",
)
async def get_result(scan_id: UUID, db: DB) -> ScanResultSchema:
    """Get a specific scan result by ID."""
    service = IaCScannerService(db=db)
    results = await service.get_scan_results(org_id="")
    for result in results:
        if result.id == scan_id:
            return _result_to_schema(result)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Scan result not found",
    )


@router.post(
    "/fix/{violation_id}",
    response_model=FixSuggestionSchema,
    summary="Get auto-fix suggestion",
)
async def get_fix_suggestion(violation_id: UUID, db: DB) -> FixSuggestionSchema:
    """Get an auto-fix suggestion for a violation."""
    service = IaCScannerService(db=db)
    fix = await service.get_fix_suggestion(violation_id)
    return FixSuggestionSchema(
        violation_id=str(fix.violation_id),
        original_code=fix.original_code,
        fixed_code=fix.fixed_code,
        explanation=fix.explanation,
        confidence=fix.confidence,
    )


@router.get(
    "/rules",
    response_model=list[ComplianceRuleSchema],
    summary="List compliance rules",
)
async def list_rules(
    db: DB,
    platform: str | None = None,
    regulation: str | None = None,
) -> list[ComplianceRuleSchema]:
    """List available compliance rules."""
    service = IaCScannerService(db=db)
    p = IaCPlatform(platform) if platform else None
    rules = await service.list_rules(platform=p, regulation=regulation)
    return [
        ComplianceRuleSchema(
            id=r.id, name=r.name, description=r.description,
            platform=r.platform.value, provider=r.provider.value,
            resource_type=r.resource_type.value, severity=r.severity.value,
            regulation=r.regulation, article=r.article,
            fix_template=r.fix_template, enabled=r.enabled,
        )
        for r in rules
    ]


@router.post(
    "/sarif/{scan_id}",
    summary="Generate SARIF report",
)
async def generate_sarif_report(scan_id: UUID, db: DB) -> dict:
    """Generate a SARIF-format report for a scan result."""
    service = IaCScannerService(db=db)
    results = await service.get_scan_results(org_id="")
    for result in results:
        if result.id == scan_id:
            return await service.generate_sarif_report(result)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Scan result not found",
    )


@router.get(
    "/pre-commit-config",
    summary="Get pre-commit hook config",
)
async def get_pre_commit_config(
    db: DB,
    platforms: str = "terraform",
) -> dict[str, str]:
    """Get pre-commit hook configuration for IaC scanning."""
    service = IaCScannerService(db=db)
    platform_list = [IaCPlatform(p.strip()) for p in platforms.split(",")]
    config = await service.get_pre_commit_config(platform_list)
    return {"config": config}


@router.get(
    "/supported-platforms",
    response_model=list[PlatformInfoSchema],
    summary="List supported platforms",
)
async def list_supported_platforms() -> list[PlatformInfoSchema]:
    """List all supported IaC platforms and their providers."""
    platform_providers = {
        IaCPlatform.TERRAFORM: [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
        IaCPlatform.CLOUDFORMATION: [CloudProvider.AWS],
        IaCPlatform.KUBERNETES: [CloudProvider.MULTI_CLOUD],
        IaCPlatform.PULUMI: [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
        IaCPlatform.ANSIBLE: [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
    }
    return [
        PlatformInfoSchema(
            name=p.value.title(), value=p.value,
            providers=[pr.value for pr in providers],
        )
        for p, providers in platform_providers.items()
    ]


@router.post(
    "/scan/diff",
    response_model=list[ViolationSchema],
    summary="Scan a PR diff for IaC violations",
)
async def scan_diff(request: ScanDiffRequest, db: DB) -> list[ViolationSchema]:
    """Scan a PR diff for IaC compliance violations."""
    service = IaCScannerService(db=db)
    platform = IaCPlatform(request.platform)
    violations = await service.scan_file(
        content=request.diff_content, platform=platform,
        filename=f"diff:{request.base_branch}",
    )
    return [_violation_to_schema(v) for v in violations]
