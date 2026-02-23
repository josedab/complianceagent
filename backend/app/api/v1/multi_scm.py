"""API endpoints for Multi-SCM Support."""

from typing import Any

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.multi_scm import MultiSCMService, SCMProvider


logger = structlog.get_logger()
router = APIRouter()


class ConnectProviderRequest(BaseModel):
    provider: str = Field(...)
    organization: str = Field(...)
    base_url: str = Field(default="")
    config: dict[str, Any] = Field(default_factory=dict)

class SCMConnectionSchema(BaseModel):
    id: str
    provider: str
    organization: str
    base_url: str
    status: str
    repositories_synced: int
    connected_at: str | None

class UnifiedRepoSchema(BaseModel):
    id: str
    provider: str
    full_name: str
    default_branch: str
    url: str
    language: str
    compliance_score: float

class CreatePRRequest(BaseModel):
    provider: str = Field(...)
    repo_full_name: str = Field(...)
    title: str = Field(...)
    source_branch: str = Field(...)
    target_branch: str = Field(default="main")

class UnifiedPRSchema(BaseModel):
    id: str
    provider: str
    repo_full_name: str
    number: int
    title: str
    status: str
    source_branch: str
    target_branch: str
    compliance_check_status: str
    url: str
    created_at: str | None

class WebhookRequest(BaseModel):
    provider: str = Field(...)
    event_type: str = Field(...)
    payload: dict[str, Any] = Field(default_factory=dict)

class SyncStatusSchema(BaseModel):
    provider: str
    total_repos: int
    repos_scanned: int
    prs_analyzed: int
    webhooks_processed: int
    last_sync_at: str | None


@router.post("/connections", response_model=SCMConnectionSchema, status_code=status.HTTP_201_CREATED, summary="Connect SCM provider")
async def connect_provider(request: ConnectProviderRequest, db: DB) -> SCMConnectionSchema:
    service = MultiSCMService(db=db)
    conn = await service.connect_provider(
        provider=request.provider, organization=request.organization,
        base_url=request.base_url, config=request.config,
    )
    return SCMConnectionSchema(
        id=str(conn.id), provider=conn.provider.value, organization=conn.organization,
        base_url=conn.base_url, status=conn.status.value,
        repositories_synced=conn.repositories_synced,
        connected_at=conn.connected_at.isoformat() if conn.connected_at else None,
    )

@router.get("/connections", response_model=list[SCMConnectionSchema], summary="List connections")
async def list_connections(db: DB, provider: str | None = None) -> list[SCMConnectionSchema]:
    service = MultiSCMService(db=db)
    p = SCMProvider(provider) if provider else None
    conns = service.list_connections(provider=p)
    return [
        SCMConnectionSchema(
            id=str(c.id), provider=c.provider.value, organization=c.organization,
            base_url=c.base_url, status=c.status.value,
            repositories_synced=c.repositories_synced,
            connected_at=c.connected_at.isoformat() if c.connected_at else None,
        ) for c in conns
    ]

@router.post("/sync/{provider}/{organization}", response_model=list[UnifiedRepoSchema], summary="Sync repositories")
async def sync_repositories(provider: str, organization: str, db: DB) -> list[UnifiedRepoSchema]:
    service = MultiSCMService(db=db)
    repos = await service.sync_repositories(provider, organization)
    return [
        UnifiedRepoSchema(
            id=str(r.id), provider=r.provider.value, full_name=r.full_name,
            default_branch=r.default_branch, url=r.url,
            language=r.language, compliance_score=r.compliance_score,
        ) for r in repos
    ]

@router.get("/repositories", response_model=list[UnifiedRepoSchema], summary="List repositories")
async def list_repositories(db: DB, provider: str | None = None, limit: int = 50) -> list[UnifiedRepoSchema]:
    service = MultiSCMService(db=db)
    p = SCMProvider(provider) if provider else None
    repos = service.list_repositories(provider=p, limit=limit)
    return [
        UnifiedRepoSchema(
            id=str(r.id), provider=r.provider.value, full_name=r.full_name,
            default_branch=r.default_branch, url=r.url,
            language=r.language, compliance_score=r.compliance_score,
        ) for r in repos
    ]

@router.post("/pull-requests", response_model=UnifiedPRSchema, status_code=status.HTTP_201_CREATED, summary="Create compliance PR")
async def create_pr(request: CreatePRRequest, db: DB) -> UnifiedPRSchema:
    service = MultiSCMService(db=db)
    pr = await service.create_compliance_pr(
        provider=request.provider, repo_full_name=request.repo_full_name,
        title=request.title, source_branch=request.source_branch,
        target_branch=request.target_branch,
    )
    return UnifiedPRSchema(
        id=str(pr.id), provider=pr.provider.value, repo_full_name=pr.repo_full_name,
        number=pr.number, title=pr.title, status=pr.status.value,
        source_branch=pr.source_branch, target_branch=pr.target_branch,
        compliance_check_status=pr.compliance_check_status, url=pr.url,
        created_at=pr.created_at.isoformat() if pr.created_at else None,
    )

@router.post("/webhooks", summary="Process SCM webhook")
async def process_webhook(request: WebhookRequest, db: DB) -> dict:
    service = MultiSCMService(db=db)
    wh = await service.process_webhook(provider=request.provider, event_type=request.event_type, payload=request.payload)
    return {"id": str(wh.id), "processed": wh.processed, "provider": wh.provider.value}

@router.get("/sync-status", response_model=list[SyncStatusSchema], summary="Get sync status")
async def get_sync_status(db: DB, provider: str | None = None) -> list[SyncStatusSchema]:
    service = MultiSCMService(db=db)
    statuses = service.get_sync_status(provider=provider)
    return [
        SyncStatusSchema(
            provider=s.provider.value, total_repos=s.total_repos,
            repos_scanned=s.repos_scanned, prs_analyzed=s.prs_analyzed,
            webhooks_processed=s.webhooks_processed,
            last_sync_at=s.last_sync_at.isoformat() if s.last_sync_at else None,
        ) for s in statuses
    ]
