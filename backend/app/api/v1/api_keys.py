"""API Key management endpoints."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import Field
from sqlalchemy import select

from app.api.v1.deps import DB, CurrentOrganization, CurrentUser
from app.models.organization import MemberRole
from app.models.production_features import APIKeyRecord
from app.schemas.base import BaseSchema, MessageResponse


logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Valid scopes — honest about what each controls
# ---------------------------------------------------------------------------

VALID_SCOPES = {
    "read",
    "write",
    "read:regulations",
    "write:regulations",
    "read:repositories",
    "write:repositories",
    "read:compliance",
    "write:compliance",
    "read:audit",
    "read:billing",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class APIKeyCreateRequest(BaseSchema):
    """Create a new API key."""

    name: str = Field(..., min_length=1, max_length=100)
    scopes: list[str] = Field(
        default_factory=lambda: ["read"],
        max_length=20,
    )
    expires_in_days: int | None = Field(
        None, ge=1, le=365, description="Optional expiry in days from now"
    )


class APIKeyCreateResponse(BaseSchema):
    """Response when creating an API key — the only time the raw key is shown."""

    id: str
    name: str
    key: str
    prefix: str
    scopes: list[str]
    created_at: str
    expires_at: str | None = None


class APIKeyRead(BaseSchema):
    """Public representation of an API key (no raw key)."""

    id: str
    name: str
    prefix: str
    scopes: list[str]
    status: str
    created_at: str
    expires_at: str | None = None
    last_used_at: str | None = None
    usage_count: int = 0
    created_by: str | None = None


class APIKeyListResponse(BaseSchema):
    """List of API keys."""

    items: list[APIKeyRead]
    total: int


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: APIKeyCreateRequest,
    user: CurrentUser,
    organization: CurrentOrganization,
    db: DB,
) -> dict[str, Any]:
    """Generate a new API key for the current user."""
    # Validate scopes
    invalid = set(body.scopes) - VALID_SCOPES
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid scopes: {', '.join(sorted(invalid))}. "
                f"Valid: {', '.join(sorted(VALID_SCOPES))}"
            ),
        )

    raw_key = f"ca_{secrets.token_urlsafe(32)}"
    prefix = raw_key[:10]
    key_hash = _hash_key(raw_key)

    expires_at = None
    if body.expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=body.expires_in_days)

    record = APIKeyRecord(
        key_prefix=prefix,
        key_hash=key_hash,
        name=body.name,
        organization_id=organization.id,
        created_by=user.id,
        status="active",
        scopes=body.scopes,
        expires_at=expires_at,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    logger.info("api_key.created", key_id=str(record.id), user=user.email, name=body.name)

    return {
        "id": str(record.id),
        "name": record.name,
        "key": raw_key,
        "prefix": prefix,
        "scopes": body.scopes,
        "created_at": record.created_at.isoformat(),
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
    }


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    user: CurrentUser,
    organization: CurrentOrganization,
    db: DB,
) -> dict[str, Any]:
    """List API keys visible to the current user.

    * Admin/owner: sees all org keys
    * Member/viewer: sees only keys they created
    """
    membership = next(
        (m for m in user.memberships if m.organization_id == organization.id),
        None,
    )
    is_admin = bool(membership and membership.role in (MemberRole.ADMIN, MemberRole.OWNER))
    stmt = (
        select(APIKeyRecord)
        .where(
            APIKeyRecord.organization_id == organization.id,
            APIKeyRecord.status != "revoked",
        )
        .order_by(APIKeyRecord.created_at.desc())
    )
    if not is_admin:
        stmt = stmt.where(APIKeyRecord.created_by == user.id)

    result = await db.execute(stmt)
    records = result.scalars().all()

    items = [
        {
            "id": str(r.id),
            "name": r.name,
            "prefix": r.key_prefix,
            "scopes": r.scopes or [],
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            "last_used_at": r.last_used_at.isoformat() if r.last_used_at else None,
            "usage_count": r.usage_count,
            "created_by": str(r.created_by) if r.created_by else None,
        }
        for r in records
    ]

    return {"items": items, "total": len(items)}


@router.delete("/{key_id}", response_model=MessageResponse)
async def revoke_api_key(
    key_id: str,
    user: CurrentUser,
    organization: CurrentOrganization,
    db: DB,
) -> dict[str, Any]:
    """Revoke an API key.

    * The key creator can always revoke their own key.
    * Admin/owner can revoke any key in their org.
    """
    try:
        uid = UUID(key_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key ID format",
        ) from exc

    result = await db.execute(
        select(APIKeyRecord).where(
            APIKeyRecord.id == uid,
            APIKeyRecord.organization_id == organization.id,
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    # Authorization: creator or admin of the org
    membership = next(
        (m for m in user.memberships if m.organization_id == organization.id),
        None,
    )
    is_admin = bool(membership and membership.role in (MemberRole.ADMIN, MemberRole.OWNER))
    is_creator = record.created_by == user.id

    if not is_creator and not is_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    record.status = "revoked"
    await db.flush()

    logger.info("api_key.revoked", key_id=key_id, user=user.email)

    return {"message": "API key revoked", "success": True}


@router.get("/scopes", response_model=list[str])
async def list_valid_scopes() -> list[str]:
    """Return the list of valid API key scopes."""
    return sorted(VALID_SCOPES)
