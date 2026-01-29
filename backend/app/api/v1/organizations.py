"""Organization endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DB, CurrentUser, OrgAdmin, OrgMember
from app.models.organization import MemberRole, Organization, OrganizationMember
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationMemberCreate,
    OrganizationMemberRead,
    OrganizationRead,
    OrganizationUpdate,
)


router = APIRouter()


@router.post("/", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrganizationCreate,
    current_user: CurrentUser,
    db: DB,
) -> Organization:
    """Create a new organization."""
    # Check if slug is unique
    result = await db.execute(select(Organization).where(Organization.slug == org_in.slug))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already exists",
        )

    # Create organization
    organization = Organization(
        name=org_in.name,
        slug=org_in.slug,
        description=org_in.description,
    )
    db.add(organization)
    await db.flush()

    # Add creator as owner
    member = OrganizationMember(
        organization_id=organization.id,
        user_id=current_user.id,
        role=MemberRole.OWNER,
    )
    db.add(member)
    await db.flush()
    await db.refresh(organization)

    return organization


@router.get("/", response_model=list[OrganizationRead])
async def list_organizations(
    current_user: CurrentUser,
    db: DB,
) -> list[Organization]:
    """List organizations the user is a member of."""
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.get("/{org_id}", response_model=OrganizationRead)
async def get_organization(
    org_id: UUID,
    member: OrgMember,
    db: DB,
) -> Organization:
    """Get organization details."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization


@router.patch("/{org_id}", response_model=OrganizationRead)
async def update_organization(
    org_id: UUID,
    org_in: OrganizationUpdate,
    admin: OrgAdmin,
    db: DB,
) -> Organization:
    """Update organization details."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    update_data = org_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)

    await db.flush()
    await db.refresh(organization)

    return organization


@router.get("/{org_id}/members", response_model=list[OrganizationMemberRead])
async def list_organization_members(
    org_id: UUID,
    member: OrgMember,
    db: DB,
) -> list[OrganizationMember]:
    """List organization members."""
    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(OrganizationMember.organization_id == org_id)
    )
    return list(result.scalars().all())


@router.post("/{org_id}/members", response_model=OrganizationMemberRead)
async def add_organization_member(
    org_id: UUID,
    member_in: OrganizationMemberCreate,
    admin: OrgAdmin,
    db: DB,
) -> OrganizationMember:
    """Add a member to the organization."""
    from app.models.user import User

    # Find user by email
    result = await db.execute(select(User).where(User.email == member_in.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already a member
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member",
        )

    # Add member
    member = OrganizationMember(
        organization_id=org_id,
        user_id=user.id,
        role=member_in.role,
        invited_by=admin.user_id,
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)

    return member


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: UUID,
    user_id: UUID,
    admin: OrgAdmin,
    db: DB,
) -> None:
    """Remove a member from the organization."""
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    if member.role == MemberRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove organization owner",
        )

    await db.delete(member)
