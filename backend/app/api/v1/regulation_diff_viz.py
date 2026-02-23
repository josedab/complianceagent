"""API endpoints for Regulation Diff Visualizer."""

from uuid import UUID

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.regulation_diff_viz import RegulationDiffVizService


logger = structlog.get_logger()
router = APIRouter()


class RegVersionSchema(BaseModel):
    regulation: str
    version: str
    effective_date: str
    section_count: int

class DiffSectionSchema(BaseModel):
    section_id: str
    title: str
    change_type: str
    old_text: str
    new_text: str
    impact_level: str
    affected_code_areas: list[str]
    recommendations: list[str]

class DiffResultSchema(BaseModel):
    id: str
    regulation: str
    old_version: str
    new_version: str
    total_sections: int
    changed_sections: int
    sections: list[DiffSectionSchema]
    impact_summary: dict[str, int]
    generated_at: str | None

class ComputeDiffRequest(BaseModel):
    regulation: str = Field(...)
    old_version: str = Field(default="")
    new_version: str = Field(default="")

class AddAnnotationRequest(BaseModel):
    section_id: str = Field(...)
    author: str = Field(...)
    comment: str = Field(...)
    action_required: bool = Field(default=False)

class AnnotationSchema(BaseModel):
    id: str
    diff_id: str
    section_id: str
    author: str
    comment: str
    action_required: bool
    created_at: str | None


@router.get("/regulations", response_model=list[str], summary="List available regulations")
async def list_regulations(db: DB) -> list[str]:
    service = RegulationDiffVizService(db=db)
    return service.list_available_regulations()

@router.get("/versions/{regulation}", response_model=list[RegVersionSchema], summary="List regulation versions")
async def list_versions(regulation: str, db: DB) -> list[RegVersionSchema]:
    service = RegulationDiffVizService(db=db)
    versions = service.list_regulation_versions(regulation)
    return [
        RegVersionSchema(regulation=v.regulation, version=v.version, effective_date=v.effective_date, section_count=len(v.sections))
        for v in versions
    ]

@router.post("/diff", response_model=DiffResultSchema, summary="Compute regulation diff")
async def compute_diff(request: ComputeDiffRequest, db: DB) -> DiffResultSchema:
    service = RegulationDiffVizService(db=db)
    result = await service.compute_diff(regulation=request.regulation, old_version=request.old_version, new_version=request.new_version)
    return DiffResultSchema(
        id=str(result.id), regulation=result.regulation,
        old_version=result.old_version, new_version=result.new_version,
        total_sections=result.total_sections, changed_sections=result.changed_sections,
        sections=[
            DiffSectionSchema(
                section_id=s.section_id, title=s.title, change_type=s.change_type.value,
                old_text=s.old_text, new_text=s.new_text, impact_level=s.impact_level.value,
                affected_code_areas=s.affected_code_areas, recommendations=s.recommendations,
            ) for s in result.sections
        ],
        impact_summary=result.impact_summary,
        generated_at=result.generated_at.isoformat() if result.generated_at else None,
    )

@router.post("/diff/{diff_id}/annotations", response_model=AnnotationSchema, status_code=status.HTTP_201_CREATED, summary="Add annotation")
async def add_annotation(diff_id: UUID, request: AddAnnotationRequest, db: DB) -> AnnotationSchema:
    service = RegulationDiffVizService(db=db)
    ann = await service.add_annotation(
        diff_id=diff_id, section_id=request.section_id,
        author=request.author, comment=request.comment, action_required=request.action_required,
    )
    return AnnotationSchema(
        id=str(ann.id), diff_id=str(ann.diff_id), section_id=ann.section_id,
        author=ann.author, comment=ann.comment, action_required=ann.action_required,
        created_at=ann.created_at.isoformat() if ann.created_at else None,
    )

@router.get("/diff/{diff_id}/annotations", response_model=list[AnnotationSchema], summary="Get annotations")
async def get_annotations(diff_id: UUID, db: DB) -> list[AnnotationSchema]:
    service = RegulationDiffVizService(db=db)
    anns = service.get_annotations(diff_id)
    return [
        AnnotationSchema(
            id=str(a.id), diff_id=str(a.diff_id), section_id=a.section_id,
            author=a.author, comment=a.comment, action_required=a.action_required,
            created_at=a.created_at.isoformat() if a.created_at else None,
        ) for a in anns
    ]
