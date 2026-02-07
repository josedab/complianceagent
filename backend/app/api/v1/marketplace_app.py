"""API endpoints for GitHub/GitLab Marketplace App."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB

from app.services.marketplace_app import (
    AppPlatform,
    InstallationStatus,
    MarketplaceAppService,
    MarketplacePlan,
    WebhookEvent,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class InstallationResponse(BaseModel):
    """App installation response."""

    id: str
    platform: str
    external_id: int
    account_login: str
    account_type: str
    plan: str
    status: str
    repositories: list[str]
    installed_at: str | None


class WebhookPayload(BaseModel):
    """Incoming webhook payload."""

    event_type: str = Field(..., description="Event type (e.g., installation, pull_request)")
    action: str = Field(default="", description="Event action")
    installation_id: int = Field(default=0)
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncResponse(BaseModel):
    """Repository sync result."""

    installation_id: str
    repos_added: list[str]
    repos_removed: list[str]
    scans_triggered: int


class UpdatePlanRequest(BaseModel):
    """Plan update request."""

    plan: str = Field(..., description="New plan name")


# --- Endpoints ---


@router.post(
    "/webhook",
    summary="Receive webhook",
    description="Process incoming webhook from GitHub/GitLab",
)
async def receive_webhook(
    payload: WebhookPayload,
    db: DB,
) -> dict:
    """Process incoming platform webhook."""
    service = MarketplaceAppService(db=db)

    event = WebhookEvent(
        platform=AppPlatform.GITHUB,
        event_type=payload.event_type,
        action=payload.action,
        installation_id=payload.installation_id,
        payload=payload.payload,
    )

    result = await service.process_webhook(event)
    return result


@router.get(
    "/installations",
    response_model=list[InstallationResponse],
    summary="List installations",
    description="List all marketplace app installations",
)
async def list_installations(
    db: DB,
    platform: str | None = None,
    installation_status: str | None = None,
) -> list[InstallationResponse]:
    """List app installations."""
    service = MarketplaceAppService(db=db)

    p = AppPlatform(platform) if platform else None
    s = InstallationStatus(installation_status) if installation_status else None

    installations = await service.list_installations(platform=p, status=s)
    return [
        InstallationResponse(
            id=str(i.id),
            platform=i.platform.value,
            external_id=i.external_id,
            account_login=i.account_login,
            account_type=i.account_type,
            plan=i.plan.value,
            status=i.status.value,
            repositories=i.repositories,
            installed_at=i.installed_at.isoformat() if i.installed_at else None,
        )
        for i in installations
    ]


@router.get(
    "/installations/{installation_id}",
    response_model=InstallationResponse,
    summary="Get installation",
)
async def get_installation(
    installation_id: UUID,
    db: DB,
) -> InstallationResponse:
    """Get installation details."""
    service = MarketplaceAppService(db=db)
    inst = await service.get_installation(installation_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Installation not found")

    return InstallationResponse(
        id=str(inst.id),
        platform=inst.platform.value,
        external_id=inst.external_id,
        account_login=inst.account_login,
        account_type=inst.account_type,
        plan=inst.plan.value,
        status=inst.status.value,
        repositories=inst.repositories,
        installed_at=inst.installed_at.isoformat() if inst.installed_at else None,
    )


@router.post(
    "/installations/{installation_id}/sync",
    response_model=SyncResponse,
    summary="Sync repositories",
)
async def sync_repositories(
    installation_id: UUID,
    db: DB,
) -> SyncResponse:
    """Sync repositories for an installation."""
    service = MarketplaceAppService(db=db)
    result = await service.sync_repositories(installation_id)
    return SyncResponse(
        installation_id=str(result.installation_id),
        repos_added=result.repos_added,
        repos_removed=result.repos_removed,
        scans_triggered=result.scans_triggered,
    )


@router.put(
    "/installations/{installation_id}/plan",
    response_model=InstallationResponse,
    summary="Update plan",
)
async def update_plan(
    installation_id: UUID,
    request: UpdatePlanRequest,
    db: DB,
) -> InstallationResponse:
    """Update the plan for an installation."""
    service = MarketplaceAppService(db=db)
    plan = MarketplacePlan(request.plan)
    inst = await service.update_plan(installation_id, plan)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Installation not found")

    return InstallationResponse(
        id=str(inst.id),
        platform=inst.platform.value,
        external_id=inst.external_id,
        account_login=inst.account_login,
        account_type=inst.account_type,
        plan=inst.plan.value,
        status=inst.status.value,
        repositories=inst.repositories,
        installed_at=inst.installed_at.isoformat() if inst.installed_at else None,
    )


@router.get(
    "/listing",
    summary="Get marketplace listing info",
)
async def get_listing_info(db: DB) -> dict:
    """Get marketplace listing metadata."""
    service = MarketplaceAppService(db=db)
    info = await service.get_listing_info()
    return {
        "app_name": info.app_name,
        "description": info.description,
        "plans": info.plans,
        "categories": info.categories,
        "install_url": info.install_url,
        "webhook_url": info.webhook_url,
    }
