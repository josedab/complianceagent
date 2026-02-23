"""API endpoints for GitHub App."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.github_app import GitHubAppService, InstallationStatus


logger = structlog.get_logger()
router = APIRouter()


class InstallationSchema(BaseModel):
    id: str
    github_installation_id: int
    account_login: str
    account_type: str
    status: str
    plan: str
    repositories: list[str]
    installed_at: str | None

class WebhookRequest(BaseModel):
    event_type: str = Field(..., description="GitHub webhook event type")
    installation_id: int = Field(..., description="GitHub App installation ID")
    payload: dict[str, Any] = Field(default_factory=dict)

class WebhookEventSchema(BaseModel):
    id: str
    event_type: str
    installation_id: int
    processed: bool
    result: dict[str, Any]
    received_at: str | None

class HandleInstallationRequest(BaseModel):
    github_installation_id: int = Field(...)
    account_login: str = Field(...)
    account_type: str = Field(default="Organization")
    action: str = Field(default="created")
    repositories: list[str] = Field(default_factory=list)

class MarketplaceListingSchema(BaseModel):
    name: str
    slug: str
    description: str
    plans: list[dict[str, Any]]
    categories: list[str]
    install_url: str

class CheckResultSchema(BaseModel):
    id: str
    installation_id: int
    repo: str
    pr_number: int
    conclusion: str
    violations_found: int
    frameworks_checked: list[str]
    created_at: str | None

class UpdatePlanRequest(BaseModel):
    plan: str = Field(..., description="Plan tier")


@router.post("/installations", response_model=InstallationSchema, status_code=status.HTTP_201_CREATED, summary="Handle app installation")
async def handle_installation(request: HandleInstallationRequest, db: DB) -> InstallationSchema:
    service = GitHubAppService(db=db)
    inst = await service.handle_installation(
        github_installation_id=request.github_installation_id,
        account_login=request.account_login,
        account_type=request.account_type,
        action=request.action,
        repositories=request.repositories,
    )
    return InstallationSchema(
        id=str(inst.id), github_installation_id=inst.github_installation_id,
        account_login=inst.account_login, account_type=inst.account_type,
        status=inst.status.value, plan=inst.plan.value,
        repositories=inst.repositories,
        installed_at=inst.installed_at.isoformat() if inst.installed_at else None,
    )

@router.get("/installations", response_model=list[InstallationSchema], summary="List installations")
async def list_installations(db: DB, status_filter: str | None = None) -> list[InstallationSchema]:
    service = GitHubAppService(db=db)
    s = InstallationStatus(status_filter) if status_filter else None
    installations = await service.list_installations(status=s)
    return [
        InstallationSchema(
            id=str(i.id), github_installation_id=i.github_installation_id,
            account_login=i.account_login, account_type=i.account_type,
            status=i.status.value, plan=i.plan.value,
            repositories=i.repositories,
            installed_at=i.installed_at.isoformat() if i.installed_at else None,
        ) for i in installations
    ]

@router.post("/webhook", response_model=WebhookEventSchema, summary="Process webhook")
async def process_webhook(request: WebhookRequest, db: DB) -> WebhookEventSchema:
    service = GitHubAppService(db=db)
    event = await service.process_webhook(
        event_type=request.event_type, installation_id=request.installation_id, payload=request.payload,
    )
    return WebhookEventSchema(
        id=str(event.id), event_type=event.event_type.value,
        installation_id=event.installation_id, processed=event.processed,
        result=event.result,
        received_at=event.received_at.isoformat() if event.received_at else None,
    )

@router.get("/marketplace", response_model=MarketplaceListingSchema, summary="Get marketplace listing")
async def get_marketplace_listing(db: DB) -> MarketplaceListingSchema:
    service = GitHubAppService(db=db)
    listing = service.get_marketplace_listing()
    return MarketplaceListingSchema(
        name=listing.name, slug=listing.slug, description=listing.description,
        plans=listing.plans, categories=listing.categories, install_url=listing.install_url,
    )

@router.put("/installations/{installation_id}/plan", response_model=InstallationSchema, summary="Update plan")
async def update_plan(installation_id: int, request: UpdatePlanRequest, db: DB) -> InstallationSchema:
    service = GitHubAppService(db=db)
    inst = await service.update_plan(installation_id, request.plan)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Installation not found")
    return InstallationSchema(
        id=str(inst.id), github_installation_id=inst.github_installation_id,
        account_login=inst.account_login, account_type=inst.account_type,
        status=inst.status.value, plan=inst.plan.value,
        repositories=inst.repositories,
        installed_at=inst.installed_at.isoformat() if inst.installed_at else None,
    )

@router.get("/checks", response_model=list[CheckResultSchema], summary="Get check results")
async def get_check_results(db: DB, installation_id: int | None = None, repo: str | None = None) -> list[CheckResultSchema]:
    service = GitHubAppService(db=db)
    results = service.get_check_results(installation_id=installation_id, repo=repo)
    return [
        CheckResultSchema(
            id=str(r.id), installation_id=r.installation_id, repo=r.repo,
            pr_number=r.pr_number, conclusion=r.conclusion,
            violations_found=r.violations_found, frameworks_checked=r.frameworks_checked,
            created_at=r.created_at.isoformat() if r.created_at else None,
        ) for r in results
    ]
