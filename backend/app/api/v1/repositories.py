"""Repository endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DB, CurrentOrganization, OrgAdmin, OrgMember
from app.models.codebase import Repository
from app.models.customer_profile import CustomerProfile
from app.schemas.codebase import RepositoryCreate, RepositoryRead


router = APIRouter()


@router.get("/", response_model=list[RepositoryRead])
async def list_repositories(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    profile_id: UUID | None = None,
) -> list[Repository]:
    """List repositories for the organization."""
    query = (
        select(Repository)
        .join(CustomerProfile)
        .where(CustomerProfile.organization_id == organization.id)
    )

    if profile_id:
        query = query.where(Repository.customer_profile_id == profile_id)

    result = await db.execute(query.order_by(Repository.full_name))
    return list(result.scalars().all())


@router.post("/", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repo_in: RepositoryCreate,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> Repository:
    """Add a repository to monitor."""
    # Verify profile belongs to organization
    result = await db.execute(
        select(CustomerProfile).where(
            CustomerProfile.id == repo_in.customer_profile_id,
            CustomerProfile.organization_id == organization.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    # Check repository limit
    count_result = await db.execute(
        select(Repository)
        .join(CustomerProfile)
        .where(CustomerProfile.organization_id == organization.id)
    )
    current_count = len(list(count_result.scalars().all()))

    if current_count >= organization.max_repositories:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Repository limit reached ({organization.max_repositories})",
        )

    # Check if already exists
    full_name = f"{repo_in.owner}/{repo_in.name}"
    result = await db.execute(
        select(Repository).where(
            Repository.customer_profile_id == repo_in.customer_profile_id,
            Repository.full_name == full_name,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository already added",
        )

    repository = Repository(
        **repo_in.model_dump(),
        full_name=full_name,
    )
    db.add(repository)
    await db.flush()
    await db.refresh(repository)

    return repository


@router.get("/{repo_id}", response_model=RepositoryRead)
async def get_repository(
    repo_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> Repository:
    """Get repository details."""
    result = await db.execute(
        select(Repository)
        .options(selectinload(Repository.customer_profile))
        .where(Repository.id == repo_id)
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    if repository.customer_profile.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Repository not accessible",
        )

    return repository


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repo_id: UUID,
    organization: CurrentOrganization,
    admin: OrgAdmin,
    db: DB,
) -> None:
    """Remove a repository."""
    result = await db.execute(
        select(Repository)
        .options(selectinload(Repository.customer_profile))
        .where(Repository.id == repo_id)
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    if repository.customer_profile.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Repository not accessible",
        )

    await db.delete(repository)


@router.post("/{repo_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def trigger_repository_analysis(
    repo_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict:
    """Trigger compliance analysis for a repository."""
    result = await db.execute(
        select(Repository)
        .options(selectinload(Repository.customer_profile))
        .where(Repository.id == repo_id)
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    if repository.customer_profile.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Repository not accessible",
        )

    # TODO: Trigger async analysis task
    repository.analysis_status = "queued"
    await db.flush()

    return {
        "message": "Analysis queued",
        "repository_id": str(repo_id),
        "status": "queued",
    }
