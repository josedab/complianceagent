"""Starter kits API endpoints."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from io import BytesIO

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization
from app.services.starter_kits import (
    StarterKitsService,
    TemplateCategory,
    TemplateLanguage,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---

class TemplateSchema(BaseModel):
    """Code template response."""
    id: str
    name: str
    description: str
    language: str
    category: str
    file_name: str
    frameworks: list[str]
    requirement_ids: list[str]


class StarterKitSummarySchema(BaseModel):
    """Starter kit summary response."""
    framework: str
    name: str
    description: str
    version: str
    supported_languages: list[str]
    requirements_covered: list[str]
    template_count: int
    download_count: int


class StarterKitDetailSchema(StarterKitSummarySchema):
    """Detailed starter kit response."""
    code_templates: list[TemplateSchema] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)
    quick_start: str
    prerequisites: list[str]


class DownloadRequest(BaseModel):
    """Request to download a starter kit."""
    language: str = "python"
    customizations: dict = Field(default_factory=dict)


class TemplatePreviewSchema(BaseModel):
    """Template content preview."""
    name: str
    file_name: str
    language: str
    content: str


# --- Endpoints ---

@router.get(
    "",
    response_model=list[StarterKitSummarySchema],
    summary="List starter kits",
    description="Get available regulation-specific starter kits",
)
async def list_starter_kits(
    db: DB,
    copilot: CopilotDep,
    framework: str | None = None,
    language: str | None = None,
) -> list[StarterKitSummarySchema]:
    """List available starter kits."""
    service = StarterKitsService(db=db, copilot=copilot)
    
    lang = TemplateLanguage(language) if language else None
    kits = await service.list_kits(framework=framework, language=lang)
    
    return [
        StarterKitSummarySchema(
            framework=kit.framework,
            name=kit.name,
            description=kit.description,
            version=kit.version,
            supported_languages=[l.value for l in kit.supported_languages],
            requirements_covered=kit.requirements_covered,
            template_count=len(kit.code_templates) + len(kit.config_templates),
            download_count=kit.download_count,
        )
        for kit in kits
    ]


@router.get(
    "/{framework}",
    response_model=StarterKitDetailSchema,
    summary="Get starter kit",
    description="Get detailed information about a starter kit",
)
async def get_starter_kit(
    framework: str,
    db: DB,
    copilot: CopilotDep,
) -> StarterKitDetailSchema:
    """Get starter kit details."""
    service = StarterKitsService(db=db, copilot=copilot)
    kit = await service.get_kit(framework)
    
    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Starter kit not found: {framework}",
        )
    
    return StarterKitDetailSchema(
        framework=kit.framework,
        name=kit.name,
        description=kit.description,
        version=kit.version,
        supported_languages=[l.value for l in kit.supported_languages],
        requirements_covered=kit.requirements_covered,
        template_count=len(kit.code_templates) + len(kit.config_templates),
        download_count=kit.download_count,
        code_templates=[
            TemplateSchema(
                id=str(t.id),
                name=t.name,
                description=t.description,
                language=t.language.value,
                category=t.category.value,
                file_name=t.file_name,
                frameworks=t.frameworks,
                requirement_ids=t.requirement_ids,
            )
            for t in kit.code_templates
        ],
        config_files=[c.file_name for c in kit.config_templates],
        documents=[d.name for d in kit.document_templates],
        quick_start=kit.quick_start,
        prerequisites=kit.prerequisites,
    )


@router.get(
    "/{framework}/templates/{template_id}",
    response_model=TemplatePreviewSchema,
    summary="Preview template",
    description="Preview the content of a specific template",
)
async def preview_template(
    framework: str,
    template_id: str,
    db: DB,
    copilot: CopilotDep,
) -> TemplatePreviewSchema:
    """Preview a template's content."""
    service = StarterKitsService(db=db, copilot=copilot)
    
    template = await service.get_template(framework, UUID(template_id))
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    
    return TemplatePreviewSchema(
        name=template.name,
        file_name=getattr(template, "file_name", "document.md"),
        language=getattr(template, "language", TemplateLanguage.MARKDOWN).value 
            if hasattr(template, "language") else "markdown",
        content=template.content,
    )


@router.post(
    "/{framework}/download",
    summary="Download starter kit",
    description="Download starter kit as ZIP archive",
)
async def download_starter_kit(
    framework: str,
    request: DownloadRequest,
    db: DB,
    copilot: CopilotDep,
) -> StreamingResponse:
    """Download starter kit as ZIP file."""
    service = StarterKitsService(db=db, copilot=copilot)
    
    try:
        language = TemplateLanguage(request.language)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: {request.language}",
        )
    
    try:
        archive = await service.generate_kit_archive(
            framework=framework,
            language=language,
            customizations=request.customizations,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    return StreamingResponse(
        BytesIO(archive),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={framework.lower()}_starter_kit.zip"
        },
    )


@router.get(
    "/languages",
    summary="Get supported languages",
    description="Get list of supported programming languages",
)
async def get_supported_languages() -> dict:
    """Get supported languages."""
    return {
        "languages": [
            {"value": lang.value, "name": lang.value.title()}
            for lang in TemplateLanguage
            if lang not in [TemplateLanguage.CONFIG, TemplateLanguage.MARKDOWN]
        ]
    }


@router.get(
    "/categories",
    summary="Get template categories",
    description="Get list of template categories",
)
async def get_template_categories() -> dict:
    """Get template categories."""
    return {
        "categories": [
            {"value": cat.value, "name": cat.value.replace("_", " ").title()}
            for cat in TemplateCategory
        ]
    }
