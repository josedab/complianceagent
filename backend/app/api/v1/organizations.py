"""Organization endpoints with invitation support."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import EmailStr
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DB, CurrentUser, OrgAdmin, OrgMember
from app.core.config import settings
from app.core.security import revoke_all_user_tokens
from app.models.organization import (
    MemberRole,
    Organization,
    OrganizationInvitation,
    OrganizationMember,
)
from app.models.production_features import APIKeyRecord
from app.schemas.base import BaseSchema, MessageResponse
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationMemberCreate,
    OrganizationMemberRead,
    OrganizationRead,
    OrganizationUpdate,
)


logger = structlog.get_logger(__name__)

router = APIRouter()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _is_expired(value: datetime) -> bool:
    normalized = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return normalized < datetime.now(UTC)


def _require_matching_org(member: OrganizationMember, org_id: UUID) -> None:
    """Prevent path identifiers from escaping the token's organization scope."""
    if member.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization context does not match the requested organization",
        )


async def _send_invitation_email(email: str, invitation_url: str) -> None:
    """Deliver an invitation without exposing its token to application logs."""
    if settings.environment in ("development", "test") and not (
        settings.smtp_host or settings.email_api_endpoint
    ):
        logger.info("org.invitation_email_sink", email=email)
        return
    if not settings.smtp_host and not settings.email_api_endpoint:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transactional email is not configured",
        )

    from app.services.notification import (
        Notification,
        NotificationType,
        create_notification_service,
    )

    service = create_notification_service(
        smtp_host=settings.smtp_host or None,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_user or None,
        smtp_password=settings.smtp_password or None,
        smtp_from_email=settings.smtp_from_email,
        email_api_endpoint=settings.email_api_endpoint or None,
        email_api_key=settings.email_api_key or None,
    )
    notification = Notification(
        type=NotificationType.ACTION_REQUIRED,
        title="You have been invited to ComplianceAgent",
        message="Use the secure invitation link to join your organization.",
        action_url=invitation_url,
    )
    results = await service.send_notification(
        notification,
        channels=["email"],
        channel_configs={"email": {"email": email}},
    )
    if not results.get("email"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invitation email delivery failed",
        )


# ---------------------------------------------------------------------------
# Invitation schemas
# ---------------------------------------------------------------------------


class InvitationCreateRequest(BaseSchema):
    email: EmailStr
    role: MemberRole = MemberRole.MEMBER


class InvitationRead(BaseSchema):
    id: str
    email: str
    role: str
    status: str
    created_at: str
    expires_at: str


class InvitationAcceptRequest(BaseSchema):
    token: str


class InvitationAcceptResponse(MessageResponse):
    organization_id: str


# ---------------------------------------------------------------------------
# Organization CRUD
# ---------------------------------------------------------------------------


@router.post("/", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrganizationCreate,
    current_user: CurrentUser,
    db: DB,
) -> Organization:
    """Create a new organization."""
    result = await db.execute(select(Organization).where(Organization.slug == org_in.slug))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already exists",
        )

    organization = Organization(
        name=org_in.name,
        slug=org_in.slug,
        description=org_in.description,
    )
    db.add(organization)
    await db.flush()

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
    _require_matching_org(member, org_id)
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    organization = result.scalar_one_or_none()
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


@router.patch("/{org_id}", response_model=OrganizationRead)
async def update_organization(
    org_id: UUID,
    org_in: OrganizationUpdate,
    admin: OrgAdmin,
    db: DB,
) -> Organization:
    """Update organization details."""
    _require_matching_org(admin, org_id)
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    organization = result.scalar_one_or_none()
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    update_data = org_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)

    await db.flush()
    await db.refresh(organization)
    return organization


# ---------------------------------------------------------------------------
# Members with populated email/name
# ---------------------------------------------------------------------------


@router.get("/{org_id}/members", response_model=list[OrganizationMemberRead])
async def list_organization_members(
    org_id: UUID,
    member: OrgMember,
    db: DB,
) -> list[dict[str, Any]]:
    """List organization members with user details."""
    _require_matching_org(member, org_id)
    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(OrganizationMember.organization_id == org_id)
    )
    members = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "organization_id": str(m.organization_id),
            "user_id": str(m.user_id),
            "role": m.role,
            "accepted_at": m.accepted_at,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
            "user_email": m.user.email if m.user else None,
            "user_name": m.user.full_name if m.user else None,
        }
        for m in members
    ]


@router.post("/{org_id}/members", response_model=OrganizationMemberRead)
async def add_organization_member(
    org_id: UUID,
    member_in: OrganizationMemberCreate,
    admin: OrgAdmin,
    db: DB,
) -> dict[str, Any]:
    """Add a member to the organization (user must already be registered)."""
    _require_matching_org(admin, org_id)
    from app.models.user import User

    result = await db.execute(select(User).where(User.email == member_in.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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

    member = OrganizationMember(
        organization_id=org_id,
        user_id=user.id,
        role=member_in.role,
        invited_by=admin.user_id,
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)

    return {
        "id": str(member.id),
        "organization_id": str(member.organization_id),
        "user_id": str(member.user_id),
        "role": member.role,
        "accepted_at": member.accepted_at,
        "created_at": member.created_at,
        "updated_at": member.updated_at,
        "user_email": user.email,
        "user_name": user.full_name,
    }


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: UUID,
    user_id: UUID,
    admin: OrgAdmin,
    db: DB,
) -> None:
    """Remove a member from the organization."""
    _require_matching_org(admin, org_id)
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
    await db.execute(
        update(APIKeyRecord)
        .where(
            APIKeyRecord.organization_id == org_id,
            APIKeyRecord.created_by == user_id,
            APIKeyRecord.status == "active",
        )
        .values(status="revoked")
    )
    revoke_all_user_tokens(str(user_id))


# ---------------------------------------------------------------------------
# Invitations (for unregistered emails)
# ---------------------------------------------------------------------------

_INVITATION_EXPIRY_DAYS = 7


@router.post(
    "/{org_id}/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    org_id: UUID,
    body: InvitationCreateRequest,
    admin: OrgAdmin,
    db: DB,
) -> dict[str, Any]:
    """Invite a user by email (works for unregistered emails too)."""
    _require_matching_org(admin, org_id)
    # Check existing invitation
    result = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.email == body.email,
            OrganizationInvitation.status == "pending",
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already pending",
        )

    raw_token = secrets.token_urlsafe(32)
    invitation = OrganizationInvitation(
        organization_id=org_id,
        email=body.email,
        role=body.role,
        invited_by=admin.user_id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(days=_INVITATION_EXPIRY_DAYS),
    )
    db.add(invitation)
    await db.flush()
    await db.refresh(invitation)

    invitation_url = f"{settings.next_public_app_url.rstrip('/')}/signup#invitation={raw_token}"
    await _send_invitation_email(body.email, invitation_url)
    logger.info("org.invitation_created", email=body.email, org_id=str(org_id))

    return {
        "id": str(invitation.id),
        "email": invitation.email,
        "role": invitation.role,
        "status": invitation.status,
        "created_at": invitation.created_at.isoformat(),
        "expires_at": invitation.expires_at.isoformat(),
    }


@router.get("/{org_id}/invitations", response_model=list[InvitationRead])
async def list_invitations(
    org_id: UUID,
    admin: OrgAdmin,
    db: DB,
) -> list[dict[str, Any]]:
    """List pending invitations for an organization."""
    _require_matching_org(admin, org_id)
    result = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.status == "pending",
        )
    )
    invitations = result.scalars().all()
    return [
        {
            "id": str(inv.id),
            "email": inv.email,
            "role": inv.role,
            "status": inv.status,
            "created_at": inv.created_at.isoformat(),
            "expires_at": inv.expires_at.isoformat(),
        }
        for inv in invitations
    ]


@router.post("/invitations/accept", response_model=InvitationAcceptResponse)
async def accept_invitation(
    body: InvitationAcceptRequest,
    user: CurrentUser,
    db: DB,
) -> dict[str, Any]:
    """Accept an invitation using the token from the email."""
    token_hash = _hash_token(body.token)
    result = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.token_hash == token_hash,
            OrganizationInvitation.status == "pending",
        )
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invitation",
        )

    if _is_expired(invitation.expires_at):
        invitation.status = "expired"
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired",
        )

    if invitation.email != user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invitation is for a different email",
        )

    # Check not already a member
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == invitation.organization_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        invitation.status = "accepted"
        await db.flush()
        return {
            "message": "You are already a member",
            "success": True,
            "organization_id": str(invitation.organization_id),
        }

    member = OrganizationMember(
        organization_id=invitation.organization_id,
        user_id=user.id,
        role=invitation.role,
        invited_by=invitation.invited_by,
        accepted_at=datetime.now(UTC),
    )
    db.add(member)
    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(UTC)
    await db.flush()

    return {
        "message": "Invitation accepted",
        "success": True,
        "organization_id": str(invitation.organization_id),
    }


@router.delete("/{org_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    org_id: UUID,
    invitation_id: UUID,
    admin: OrgAdmin,
    db: DB,
) -> None:
    """Revoke a pending invitation."""
    _require_matching_org(admin, org_id)
    result = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.status == "pending",
        )
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    invitation.status = "revoked"
    await db.flush()
