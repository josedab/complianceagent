"""API endpoints for GitHub Marketplace App integration."""

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.gh_marketplace_app import GHMarketplaceAppService


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class InstallRequest(BaseModel):
    github_id: int = Field(..., description="GitHub installation ID")
    account: str = Field(..., description="GitHub account or organization")
    plan: str = Field(..., description="Marketplace plan slug")
    repos: list[str] = Field(default_factory=list, description="Repositories to install on")


class RunCheckRequest(BaseModel):
    github_id: int = Field(..., description="GitHub installation ID")
    repo: str = Field(..., description="Repository full name")
    pr_number: int = Field(..., description="Pull request number")
    sha: str = Field(..., description="Commit SHA to check")
    diff_content: str = Field(..., description="Diff content for analysis")


class ChangePlanRequest(BaseModel):
    new_plan: str = Field(..., description="New marketplace plan slug")


# --- Endpoints ---


@router.get("/app-info")
async def get_app_info(db: DB) -> dict:
    """Get marketplace app information."""
    svc = GHMarketplaceAppService()
    return await svc.get_app_info(db)


@router.post("/installs")
async def handle_install(request: InstallRequest, db: DB) -> dict:
    """Handle a new marketplace installation."""
    svc = GHMarketplaceAppService()
    return await svc.handle_install(
        db,
        github_id=request.github_id,
        account=request.account,
        plan=request.plan,
        repos=request.repos,
    )


@router.delete("/installs/{github_id}")
async def handle_uninstall(github_id: int, db: DB) -> dict:
    """Handle marketplace uninstallation."""
    svc = GHMarketplaceAppService()
    return await svc.handle_uninstall(db, github_id=github_id)


@router.post("/checks")
async def run_check(request: RunCheckRequest, db: DB) -> dict:
    """Run a compliance check on a PR."""
    svc = GHMarketplaceAppService()
    return await svc.run_check(
        db,
        github_id=request.github_id,
        repo=request.repo,
        pr_number=request.pr_number,
        sha=request.sha,
        diff_content=request.diff_content,
    )


@router.put("/installs/{github_id}/plan")
async def change_plan(github_id: int, request: ChangePlanRequest, db: DB) -> dict:
    """Change the marketplace plan for an installation."""
    svc = GHMarketplaceAppService()
    return await svc.change_plan(db, github_id=github_id, new_plan=request.new_plan)


@router.get("/installs")
async def list_installs(db: DB) -> list[dict]:
    """List all marketplace installations."""
    svc = GHMarketplaceAppService()
    return await svc.list_installs(db)


@router.get("/checks")
async def list_checks(
    db: DB,
    repo: str | None = Query(None, description="Filter by repository"),
) -> list[dict]:
    """List compliance checks."""
    svc = GHMarketplaceAppService()
    return await svc.list_checks(db, repo=repo)


@router.get("/stats")
async def get_stats(db: DB) -> dict:
    """Get marketplace app statistics."""
    svc = GHMarketplaceAppService()
    return await svc.get_stats(db)
