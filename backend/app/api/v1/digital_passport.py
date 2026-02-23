"""API endpoints for Digital Passport management."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.digital_passport import (
    CredentialType,
    DigitalPassportService,
    VerifierType,
)


logger = structlog.get_logger()
router = APIRouter()


class PassportCreateRequest(BaseModel):
    org_name: str = Field(...)
    credentials: list[dict] = Field(default_factory=list)


class CredentialAddRequest(BaseModel):
    credential_type: str = Field(...)
    framework: str = Field(...)
    score: float = Field(...)


class VerifyPassportRequest(BaseModel):
    verifier: str = Field(...)
    verifier_type: str = Field(default="auditor")


@router.post("/passports", status_code=status.HTTP_201_CREATED, summary="Create a digital passport")
async def create_passport(request: PassportCreateRequest, db: DB) -> dict:
    """Create a new digital passport with credentials."""
    service = DigitalPassportService(db=db)
    result = await service.create_passport(
        org_name=request.org_name,
        credentials=request.credentials,
    )
    return {
        "id": str(result.id),
        "org_name": result.org_name,
        "overall_score": result.overall_score,
        "status": result.status.value,
        "credentials": len(result.credentials),
        "portable_url": result.portable_url,
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }


@router.post("/passports/{passport_id}/credentials", status_code=status.HTTP_201_CREATED, summary="Add a credential")
async def add_credential(passport_id: UUID, request: CredentialAddRequest, db: DB) -> dict:
    """Add a credential to an existing passport."""
    service = DigitalPassportService(db=db)
    try:
        result = await service.add_credential(
            passport_id=passport_id,
            credential_type=CredentialType(request.credential_type),
            framework=request.framework,
            score=request.score,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "id": str(result.id),
        "org_name": result.org_name,
        "credential_type": result.credential_type.value,
        "framework": result.framework,
        "score": result.score,
        "grade": result.grade,
        "issued_at": result.issued_at.isoformat() if result.issued_at else None,
    }


@router.post("/passports/{passport_id}/verify", summary="Verify a passport")
async def verify_passport(passport_id: UUID, request: VerifyPassportRequest, db: DB) -> dict:
    """Verify a digital passport."""
    service = DigitalPassportService(db=db)
    try:
        result = await service.verify_passport(
            passport_id=passport_id,
            verifier=request.verifier,
            verifier_type=VerifierType(request.verifier_type),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "id": str(result.id),
        "passport_id": str(result.passport_id),
        "verifier": result.verifier,
        "verifier_type": result.verifier_type.value,
        "verified": result.verified,
        "verified_at": result.verified_at.isoformat() if result.verified_at else None,
    }


@router.post("/passports/{passport_id}/suspend", summary="Suspend a passport")
async def suspend_passport(passport_id: UUID, db: DB) -> dict:
    """Suspend a digital passport."""
    service = DigitalPassportService(db=db)
    try:
        result = await service.suspend_passport(passport_id=passport_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "id": str(result.id),
        "org_name": result.org_name,
        "status": result.status.value,
        "last_updated": result.last_updated.isoformat() if result.last_updated else None,
    }


@router.get("/passports", summary="List all passports")
async def list_passports(db: DB) -> list[dict]:
    """List all passports."""
    service = DigitalPassportService(db=db)
    passports = await service.list_passports()
    return [
        {
            "id": str(p.id),
            "org_name": p.org_name,
            "overall_score": p.overall_score,
            "status": p.status.value,
            "credentials": len(p.credentials),
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in passports
    ]


@router.get("/passports/{passport_id}", summary="Get a passport")
async def get_passport(passport_id: UUID, db: DB) -> dict:
    """Get a passport by ID."""
    service = DigitalPassportService(db=db)
    try:
        result = await service.get_passport(passport_id=passport_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "id": str(result.id),
        "org_name": result.org_name,
        "overall_score": result.overall_score,
        "status": result.status.value,
        "credentials": [
            {
                "id": str(c.id),
                "credential_type": c.credential_type.value,
                "framework": c.framework,
                "score": c.score,
                "grade": c.grade,
            }
            for c in result.credentials
        ],
        "portable_url": result.portable_url,
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }


@router.get("/stats", summary="Get digital passport stats")
async def get_stats(db: DB) -> dict:
    """Get aggregate passport statistics."""
    service = DigitalPassportService(db=db)
    stats = await service.get_stats()
    return {
        "total_passports": stats.total_passports,
        "active": stats.active,
        "credentials_issued": stats.credentials_issued,
        "verifications": stats.verifications,
        "by_credential_type": stats.by_credential_type,
    }
