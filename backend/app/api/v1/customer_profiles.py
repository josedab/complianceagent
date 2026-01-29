"""Customer profile endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.v1.deps import DB, CurrentOrganization, OrgAdmin, OrgMember
from app.models.customer_profile import CustomerProfile
from app.schemas.customer_profile import (
    CustomerProfileCreate,
    CustomerProfileRead,
    CustomerProfileUpdate,
)


router = APIRouter()


@router.get("/", response_model=list[CustomerProfileRead])
async def list_customer_profiles(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[CustomerProfile]:
    """List customer profiles for the organization."""
    result = await db.execute(
        select(CustomerProfile)
        .where(CustomerProfile.organization_id == organization.id)
        .order_by(CustomerProfile.name)
    )
    profiles = result.scalars().all()

    # Add inferred frameworks
    return [
        CustomerProfileRead(
            **CustomerProfileRead.model_validate(p).model_dump(exclude={"inferred_frameworks"}),
            inferred_frameworks=[f.value for f in p.get_applicable_frameworks()],
        )
        for p in profiles
    ]


@router.post("/", response_model=CustomerProfileRead, status_code=status.HTTP_201_CREATED)
async def create_customer_profile(
    profile_in: CustomerProfileCreate,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> CustomerProfile:
    """Create a new customer profile."""
    # If setting as default, unset other defaults
    if profile_in.is_default:
        result = await db.execute(
            select(CustomerProfile).where(
                CustomerProfile.organization_id == organization.id,
                CustomerProfile.is_default,
            )
        )
        for existing in result.scalars():
            existing.is_default = False

    profile = CustomerProfile(
        organization_id=organization.id,
        **profile_in.model_dump(),
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)

    return CustomerProfileRead(
        **CustomerProfileRead.model_validate(profile).model_dump(exclude={"inferred_frameworks"}),
        inferred_frameworks=[f.value for f in profile.get_applicable_frameworks()],
    )


@router.get("/{profile_id}", response_model=CustomerProfileRead)
async def get_customer_profile(
    profile_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> CustomerProfile:
    """Get customer profile details."""
    result = await db.execute(
        select(CustomerProfile).where(
            CustomerProfile.id == profile_id,
            CustomerProfile.organization_id == organization.id,
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    return CustomerProfileRead(
        **CustomerProfileRead.model_validate(profile).model_dump(exclude={"inferred_frameworks"}),
        inferred_frameworks=[f.value for f in profile.get_applicable_frameworks()],
    )


@router.patch("/{profile_id}", response_model=CustomerProfileRead)
async def update_customer_profile(
    profile_id: UUID,
    profile_in: CustomerProfileUpdate,
    organization: CurrentOrganization,
    admin: OrgAdmin,
    db: DB,
) -> CustomerProfile:
    """Update customer profile."""
    result = await db.execute(
        select(CustomerProfile).where(
            CustomerProfile.id == profile_id,
            CustomerProfile.organization_id == organization.id,
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    update_data = profile_in.model_dump(exclude_unset=True)

    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        other_result = await db.execute(
            select(CustomerProfile).where(
                CustomerProfile.organization_id == organization.id,
                CustomerProfile.is_default,
                CustomerProfile.id != profile_id,
            )
        )
        for existing in other_result.scalars():
            existing.is_default = False

    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)

    return CustomerProfileRead(
        **CustomerProfileRead.model_validate(profile).model_dump(exclude={"inferred_frameworks"}),
        inferred_frameworks=[f.value for f in profile.get_applicable_frameworks()],
    )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer_profile(
    profile_id: UUID,
    organization: CurrentOrganization,
    admin: OrgAdmin,
    db: DB,
) -> None:
    """Delete customer profile."""
    result = await db.execute(
        select(CustomerProfile).where(
            CustomerProfile.id == profile_id,
            CustomerProfile.organization_id == organization.id,
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    await db.delete(profile)
