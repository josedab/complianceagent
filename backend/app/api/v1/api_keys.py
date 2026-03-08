"""API Key management endpoints."""

import hashlib
import secrets
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import Field
from sqlalchemy import select

from app.api.v1.deps import DB, CurrentUser
from app.models.production_features import APIKeyRecord
from app.schemas.base import BaseSchema, MessageResponse


logger = structlog.get_logger(__name__)

router = APIRouter()


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


class APIKeyCreateResponse(BaseSchema):
    """Response when creating an API key — the only time the raw key is shown."""

    id: str
    name: str
    key: str  # Raw key, shown only once
    prefix: str
    scopes: list[str]
    created_at: str


class APIKeyRead(BaseSchema):
    """Public representation of an API key (no raw key)."""

    id: str
    name: str
    prefix: str
    scopes: list[str]
    status: str
    created_at: str
    last_used_at: str | None = None
    usage_count: int = 0


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
async def create_api_key(body: APIKeyCreateRequest, user: CurrentUser, db: DB) -> dict:
    """Generate a new API key for the current user."""
    raw_key = f"ca_{secrets.token_urlsafe(32)}"
    prefix = raw_key[:10]
    key_hash = _hash_key(raw_key)

    # Resolve organization from user's first membership
    org_id = None
    if user.memberships:
        org_id = user.memberships[0].organization_id

    record = APIKeyRecord(
        key_prefix=prefix,
        key_hash=key_hash,
        name=body.name,
        organization_id=org_id,
        status="active",
        scopes=body.scopes,
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
    }


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(user: CurrentUser, db: DB) -> dict:
    """List all API keys visible to the current user (scoped by organization)."""
    org_ids = [m.organization_id for m in (user.memberships or [])]

    if org_ids:
        stmt = (
            select(APIKeyRecord)
            .where(
                APIKeyRecord.organization_id.in_(org_ids),
                APIKeyRecord.status != "revoked",
            )
            .order_by(APIKeyRecord.created_at.desc())
        )
    else:
        # User with no org — return keys with no org scope
        stmt = (
            select(APIKeyRecord)
            .where(
                APIKeyRecord.organization_id.is_(None),
                APIKeyRecord.status != "revoked",
            )
            .order_by(APIKeyRecord.created_at.desc())
        )

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
            "last_used_at": r.last_used_at.isoformat() if r.last_used_at else None,
            "usage_count": r.usage_count,
        }
        for r in records
    ]

    return {"items": items, "total": len(items)}


@router.delete("/{key_id}", response_model=MessageResponse)
async def revoke_api_key(key_id: str, user: CurrentUser, db: DB) -> dict:
    """Revoke an API key (soft delete by setting status to 'revoked')."""
    try:
        uid = UUID(key_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key ID format",
        ) from exc

    org_ids = [m.organization_id for m in (user.memberships or [])]

    result = await db.execute(
        select(APIKeyRecord).where(APIKeyRecord.id == uid)
    )
    record = result.scalar_one_or_none()

    if not record or (record.organization_id and record.organization_id not in org_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    record.status = "revoked"
    await db.flush()

    logger.info("api_key.revoked", key_id=key_id, user=user.email)

    return {"message": "API key revoked", "success": True}
