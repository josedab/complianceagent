"""API endpoints for IaC Policy Engine."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB


logger = structlog.get_logger()
router = APIRouter()


def _serialize(obj):
    """Convert a dataclass to a JSON-serializable dict."""
    from dataclasses import fields, is_dataclass

    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        v = getattr(obj, f.name)
        result[f.name] = _ser_val(v)
    return result


def _ser_val(v):
    from dataclasses import is_dataclass
    from datetime import datetime
    from enum import Enum
    from uuid import UUID

    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, list):
        return [_ser_val(item) for item in v]
    if isinstance(v, dict):
        return {k: _ser_val(val) for k, val in v.items()}
    if is_dataclass(v):
        return _serialize(v)
    return v


# --- Schemas ---


class ScanRequest(BaseModel):
    file_content: str = Field(..., description="Content of the infrastructure file to scan")
    file_path: str = Field(..., description="Path of the file being scanned")


class ScanViolation(BaseModel):
    rule_id: str
    severity: str
    message: str
    line: int | None = None
    resource: str | None = None
    framework: str | None = None
    remediation: str | None = None


class ScanResultResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: UUID | None = None
    provider: str = ""
    file_path: str = ""
    violations: list[ScanViolation] = Field(default_factory=list)
    total_violations: int = 0
    critical_count: int = 0
    high_count: int = 0
    passed_rules: int = 0
    scanned_at: str = ""


class PolicyRuleResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: str = ""
    name: str = ""
    description: str = ""
    provider: str = ""
    framework: str = ""
    severity: str = ""
    enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyRuleListResponse(BaseModel):
    model_config = {"extra": "ignore"}
    rules: list[PolicyRuleResponse] = Field(default_factory=list)
    total: int = 0


class CreateRuleRequest(BaseModel):
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    provider: str = Field(
        ..., description="Cloud provider (e.g. 'terraform', 'kubernetes', 'cloudformation')"
    )
    framework: str = Field(..., description="Compliance framework")
    severity: str = Field(..., description="Severity level (critical, high, medium, low)")
    pattern: str = Field(..., description="Detection pattern or expression")
    remediation: str = Field("", description="Suggested remediation")


class ScanHistoryEntry(BaseModel):
    id: UUID
    provider: str
    file_path: str
    total_violations: int
    critical_count: int
    scanned_at: str


class ScanHistoryResponse(BaseModel):
    model_config = {"extra": "ignore"}
    entries: list[ScanHistoryEntry] = Field(default_factory=list)
    total: int = 0


# --- Endpoints ---


@router.post("/scan/terraform", response_model=ScanResultResponse, summary="Scan Terraform files")
async def scan_terraform(request: ScanRequest, db: DB) -> ScanResultResponse:
    """Scan Terraform infrastructure files for policy violations."""
    from app.services.iac_policy import IaCPolicyEngine as IacPolicyEngineService

    service = IacPolicyEngineService(db=db)
    from app.services.iac_policy.models import CloudProvider
    result = await service.scan_terraform(provider=CloudProvider.AWS)
    return ScanResultResponse(**_serialize(result))


@router.post(
    "/scan/kubernetes", response_model=ScanResultResponse, summary="Scan Kubernetes manifests"
)
async def scan_kubernetes(request: ScanRequest, db: DB) -> ScanResultResponse:
    """Scan Kubernetes manifest files for policy violations."""
    from app.services.iac_policy import IaCPolicyEngine as IacPolicyEngineService

    service = IacPolicyEngineService(db=db)
    result = await service.scan_kubernetes()
    return ScanResultResponse(**_serialize(result))


@router.post(
    "/scan/cloudformation",
    response_model=ScanResultResponse,
    summary="Scan CloudFormation templates",
)
async def scan_cloudformation(request: ScanRequest, db: DB) -> ScanResultResponse:
    """Scan CloudFormation template files for policy violations."""
    from app.services.iac_policy import IaCPolicyEngine as IacPolicyEngineService

    service = IacPolicyEngineService(db=db)
    result = await service.scan_cloudformation()
    return ScanResultResponse(**_serialize(result))


@router.get("/rules", response_model=PolicyRuleListResponse, summary="List policy rules")
async def list_rules(
    db: DB,
    provider: str | None = None,
    framework: str | None = None,
) -> PolicyRuleListResponse:
    """List all policy rules with optional provider and framework filters."""
    from app.services.iac_policy import IaCPolicyEngine as IacPolicyEngineService

    service = IacPolicyEngineService(db=db)
    rules = await service.list_rules(provider=provider, framework=framework)
    return PolicyRuleListResponse(
        rules=[PolicyRuleResponse(**_serialize(r)) for r in rules],
        total=len(rules),
    )


@router.get(
    "/rules/{rule_id}", response_model=PolicyRuleResponse, summary="Get policy rule details"
)
async def get_rule(rule_id: str, db: DB) -> PolicyRuleResponse:
    """Get details of a specific policy rule."""
    from app.services.iac_policy import IaCPolicyEngine as IacPolicyEngineService

    service = IacPolicyEngineService(db=db)
    rule = await service.get_rule(rule_id=rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return PolicyRuleResponse(**_serialize(rule))


@router.post(
    "/rules",
    response_model=PolicyRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a custom policy rule",
)
async def create_rule(request: CreateRuleRequest, db: DB) -> PolicyRuleResponse:
    """Add a custom policy rule."""
    from app.services.iac_policy import IaCPolicyEngine as IacPolicyEngineService

    service = IacPolicyEngineService(db=db)
    rule = await service.create_rule(
        name=request.name,
        description=request.description,
        provider=request.provider,
        framework=request.framework,
        severity=request.severity,
        pattern=request.pattern,
        remediation=request.remediation,
    )
    return PolicyRuleResponse(**_serialize(rule))


@router.get("/scan-history", response_model=ScanHistoryResponse, summary="Get scan history")
async def get_scan_history(db: DB) -> ScanHistoryResponse:
    """Get the history of infrastructure scans."""
    from app.services.iac_policy import IaCPolicyEngine as IacPolicyEngineService

    service = IacPolicyEngineService(db=db)
    entries = await service.get_scan_history()
    return ScanHistoryResponse(
        entries=[ScanHistoryEntry(**e) for e in entries],
        total=len(entries),
    )
