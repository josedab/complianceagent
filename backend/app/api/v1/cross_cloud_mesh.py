"""API endpoints for Cross-Cloud Mesh."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.cross_cloud_mesh import CrossCloudMeshService


logger = structlog.get_logger()
router = APIRouter()


class ConnectAccountRequest(BaseModel):
    provider: str = Field(...)
    account_id: str = Field(...)
    name: str = Field(...)
    regions: list[str] = Field(default_factory=list)


class AccountSchema(BaseModel):
    id: str
    provider: str
    account_id: str
    name: str
    regions: list[str]
    status: str
    resources_discovered: int
    created_at: str | None


class DiscoveryResultSchema(BaseModel):
    account_id: str
    resources_found: int
    resource_types: dict[str, int]
    completed_at: str | None


class ScanResultSchema(BaseModel):
    account_id: str
    findings: int
    critical: int
    high: int
    medium: int
    low: int
    compliance_score: float
    completed_at: str | None


class PostureSchema(BaseModel):
    overall_score: float
    accounts: int
    total_resources: int
    total_findings: int
    critical_findings: int
    by_provider: dict[str, float]


class StatsSchema(BaseModel):
    total_accounts: int
    total_resources: int
    total_scans: int
    avg_compliance_score: float
    providers: list[str]


@router.post(
    "/accounts",
    response_model=AccountSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Connect account",
)
async def connect_account(request: ConnectAccountRequest, db: DB) -> AccountSchema:
    """Connect a cloud account to the mesh."""
    service = CrossCloudMeshService(db=db)
    account = await service.connect_account(
        provider=request.provider,
        account_id=request.account_id,
        name=request.name,
        regions=request.regions,
    )
    return AccountSchema(
        id=str(account.id),
        provider=account.provider,
        account_id=account.account_id,
        name=account.name,
        regions=account.regions,
        status=account.status,
        resources_discovered=account.resources_discovered,
        created_at=account.created_at.isoformat() if account.created_at else None,
    )


@router.post(
    "/accounts/{account_id}/discover",
    response_model=DiscoveryResultSchema,
    summary="Discover resources",
)
async def discover_resources(account_id: UUID, db: DB) -> DiscoveryResultSchema:
    """Discover resources in a cloud account."""
    service = CrossCloudMeshService(db=db)
    result = await service.discover_resources(account_id=account_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return DiscoveryResultSchema(
        account_id=str(result.account_id),
        resources_found=result.resources_found,
        resource_types=result.resource_types,
        completed_at=result.completed_at.isoformat()
        if result.completed_at
        else None,
    )


@router.post(
    "/accounts/{account_id}/scan",
    response_model=ScanResultSchema,
    summary="Scan account",
)
async def scan_account(account_id: UUID, db: DB) -> ScanResultSchema:
    """Scan a cloud account for compliance issues."""
    service = CrossCloudMeshService(db=db)
    result = await service.scan_account(account_id=account_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return ScanResultSchema(
        account_id=str(result.account_id),
        findings=result.findings,
        critical=result.critical,
        high=result.high,
        medium=result.medium,
        low=result.low,
        compliance_score=result.compliance_score,
        completed_at=result.completed_at.isoformat()
        if result.completed_at
        else None,
    )


@router.get("/posture", response_model=PostureSchema, summary="Get posture")
async def get_posture(db: DB) -> PostureSchema:
    """Get the overall cloud security posture."""
    service = CrossCloudMeshService(db=db)
    posture = service.get_posture()
    return PostureSchema(
        overall_score=posture.overall_score,
        accounts=posture.accounts,
        total_resources=posture.total_resources,
        total_findings=posture.total_findings,
        critical_findings=posture.critical_findings,
        by_provider=posture.by_provider,
    )


@router.get("/accounts", response_model=list[AccountSchema], summary="List accounts")
async def list_accounts(db: DB) -> list[AccountSchema]:
    """List all connected cloud accounts."""
    service = CrossCloudMeshService(db=db)
    accounts = service.list_accounts()
    return [
        AccountSchema(
            id=str(a.id),
            provider=a.provider,
            account_id=a.account_id,
            name=a.name,
            regions=a.regions,
            status=a.status,
            resources_discovered=a.resources_discovered,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in accounts
    ]


@router.get("/stats", response_model=StatsSchema, summary="Get stats")
async def get_stats(db: DB) -> StatsSchema:
    """Get cross-cloud mesh statistics."""
    service = CrossCloudMeshService(db=db)
    stats = service.get_stats()
    return StatsSchema(
        total_accounts=stats.total_accounts,
        total_resources=stats.total_resources,
        total_scans=stats.total_scans,
        avg_compliance_score=stats.avg_compliance_score,
        providers=stats.providers,
    )
