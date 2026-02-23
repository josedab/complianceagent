"""API endpoints for Trust Network."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.trust_network import TrustNetworkService


logger = structlog.get_logger()
router = APIRouter()


class CreateAttestationRequest(BaseModel):
    org_name: str = Field(...)
    attestation_type: str = Field(...)
    framework: str = Field(...)
    score: float = Field(...)


class AttestationSchema(BaseModel):
    id: str
    org_name: str
    attestation_type: str
    framework: str
    score: float
    status: str
    verified: bool
    created_at: str | None


class ChainEntrySchema(BaseModel):
    id: str
    attestation_id: str
    hash: str
    previous_hash: str | None
    timestamp: str | None


class StatsSchema(BaseModel):
    total_attestations: int
    verified_attestations: int
    revoked_attestations: int
    organizations: int
    avg_score: float


@router.post(
    "/attestations",
    response_model=AttestationSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create attestation",
)
async def create_attestation(
    request: CreateAttestationRequest, db: DB
) -> AttestationSchema:
    """Create a new trust attestation."""
    service = TrustNetworkService(db=db)
    att = await service.create_attestation(
        org_name=request.org_name,
        attestation_type=request.attestation_type,
        framework=request.framework,
        score=request.score,
    )
    return AttestationSchema(
        id=str(att.id),
        org_name=att.org_name,
        attestation_type=att.attestation_type,
        framework=att.framework,
        score=att.score,
        status=att.status,
        verified=att.verified,
        created_at=att.created_at.isoformat() if att.created_at else None,
    )


@router.get(
    "/attestations",
    response_model=list[AttestationSchema],
    summary="List attestations",
)
async def list_attestations(
    db: DB,
    org_name: str | None = None,
    attestation_type: str | None = None,
) -> list[AttestationSchema]:
    """List attestations with optional filters."""
    service = TrustNetworkService(db=db)
    atts = service.list_attestations(
        org_name=org_name, attestation_type=attestation_type
    )
    return [
        AttestationSchema(
            id=str(a.id),
            org_name=a.org_name,
            attestation_type=a.attestation_type,
            framework=a.framework,
            score=a.score,
            status=a.status,
            verified=a.verified,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in atts
    ]


@router.post("/attestations/{attestation_id}/verify", summary="Verify attestation")
async def verify_attestation(attestation_id: UUID, db: DB) -> dict:
    """Verify a trust attestation."""
    service = TrustNetworkService(db=db)
    ok = await service.verify_attestation(attestation_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attestation not found"
        )
    return {"status": "verified", "attestation_id": str(attestation_id)}


@router.post("/attestations/{attestation_id}/revoke", summary="Revoke attestation")
async def revoke_attestation(attestation_id: UUID, db: DB) -> dict:
    """Revoke a trust attestation."""
    service = TrustNetworkService(db=db)
    ok = await service.revoke_attestation(attestation_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attestation not found"
        )
    return {"status": "revoked", "attestation_id": str(attestation_id)}


@router.get("/chain", response_model=list[ChainEntrySchema], summary="Get chain")
async def get_chain(db: DB) -> list[ChainEntrySchema]:
    """Get the attestation trust chain."""
    service = TrustNetworkService(db=db)
    chain = service.get_chain()
    return [
        ChainEntrySchema(
            id=str(c.id),
            attestation_id=str(c.attestation_id),
            hash=c.hash,
            previous_hash=c.previous_hash,
            timestamp=c.timestamp.isoformat() if c.timestamp else None,
        )
        for c in chain
    ]


@router.get("/stats", response_model=StatsSchema, summary="Get stats")
async def get_stats(db: DB) -> StatsSchema:
    """Get trust network statistics."""
    service = TrustNetworkService(db=db)
    stats = service.get_stats()
    return StatsSchema(
        total_attestations=stats.total_attestations,
        verified_attestations=stats.verified_attestations,
        revoked_attestations=stats.revoked_attestations,
        organizations=stats.organizations,
        avg_score=stats.avg_score,
    )
