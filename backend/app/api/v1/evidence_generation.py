"""API endpoints for Automated Evidence Generation."""

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.v1.deps import DB
from app.services.evidence_generation import EvidenceGenerationService


logger = structlog.get_logger()
router = APIRouter()


class ControlMappingSchema(BaseModel):
    control_id: str
    control_name: str
    framework: str
    status: str
    evidence_count: int
    freshness: str
    code_refs: list[str]


class EvidenceItemSchema(BaseModel):
    id: str
    control_id: str
    title: str
    evidence_type: str
    freshness: str
    collected_at: str | None


class PackageSchema(BaseModel):
    id: str
    framework: str
    controls_total: int
    controls_met: int
    coverage_pct: float
    items: list[EvidenceItemSchema]
    control_mappings: list[ControlMappingSchema]
    generated_at: str | None


class StatsSchema(BaseModel):
    total_items: int
    by_framework: dict[str, int]
    by_freshness: dict[str, int]
    overall_coverage_pct: float
    stale_items: int


@router.post(
    "/generate/{framework}",
    response_model=PackageSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate evidence package",
)
async def generate_package(framework: str, db: DB) -> PackageSchema:
    service = EvidenceGenerationService(db=db)
    p = await service.generate_evidence_package(framework)
    return PackageSchema(
        id=str(p.id),
        framework=p.framework.value,
        controls_total=p.controls_total,
        controls_met=p.controls_met,
        coverage_pct=p.coverage_pct,
        items=[
            EvidenceItemSchema(
                id=str(i.id),
                control_id=i.control_id,
                title=i.title,
                evidence_type=i.evidence_type,
                freshness=i.freshness.value,
                collected_at=i.collected_at.isoformat() if i.collected_at else None,
            )
            for i in p.items
        ],
        control_mappings=[
            ControlMappingSchema(
                control_id=m.control_id,
                control_name=m.control_name,
                framework=m.framework.value,
                status=m.status.value,
                evidence_count=m.evidence_count,
                freshness=m.freshness.value,
                code_refs=m.code_refs,
            )
            for m in p.control_mappings
        ],
        generated_at=p.generated_at.isoformat() if p.generated_at else None,
    )


@router.get("/package/{framework}", response_model=PackageSchema, summary="Get evidence package")
async def get_package(framework: str, db: DB) -> PackageSchema:
    service = EvidenceGenerationService(db=db)
    p = service.get_package(framework)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Package not found — generate first"
        )
    return PackageSchema(
        id=str(p.id),
        framework=p.framework.value,
        controls_total=p.controls_total,
        controls_met=p.controls_met,
        coverage_pct=p.coverage_pct,
        items=[
            EvidenceItemSchema(
                id=str(i.id),
                control_id=i.control_id,
                title=i.title,
                evidence_type=i.evidence_type,
                freshness=i.freshness.value,
                collected_at=i.collected_at.isoformat() if i.collected_at else None,
            )
            for i in p.items
        ],
        control_mappings=[
            ControlMappingSchema(
                control_id=m.control_id,
                control_name=m.control_name,
                framework=m.framework.value,
                status=m.status.value,
                evidence_count=m.evidence_count,
                freshness=m.freshness.value,
                code_refs=m.code_refs,
            )
            for m in p.control_mappings
        ],
        generated_at=p.generated_at.isoformat() if p.generated_at else None,
    )


@router.get("/frameworks", summary="List supported frameworks")
async def list_frameworks(db: DB) -> list[dict]:
    service = EvidenceGenerationService(db=db)
    return service.list_frameworks()


@router.get("/stats", response_model=StatsSchema, summary="Get evidence stats")
async def get_stats(db: DB) -> StatsSchema:
    service = EvidenceGenerationService(db=db)
    s = service.get_stats()
    return StatsSchema(
        total_items=s.total_items,
        by_framework=s.by_framework,
        by_freshness=s.by_freshness,
        overall_coverage_pct=s.overall_coverage_pct,
        stale_items=s.stale_items,
    )
