"""Compliance Templates API endpoints."""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.v1.deps import DB, CurrentOrganization, OrgMember


router = APIRouter()


class TemplateResponse(BaseModel):
    """Template response model."""

    id: str
    name: str
    description: str
    category: str
    regulations: list[str]
    languages: list[str]
    version: str
    tags: list[str]


class TemplateCodeResponse(BaseModel):
    """Template code response."""

    template_id: str
    language: str
    code: str
    tests: str | None = None
    documentation: str | None = None


@router.get("/", response_model=list[TemplateResponse])
async def list_templates(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    category: str | None = Query(default=None),
    regulation: str | None = Query(default=None),
    language: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> list[TemplateResponse]:
    """List available compliance code templates."""
    from app.services.templates import TemplateCategory, get_template_registry

    registry = get_template_registry()

    cat = None
    if category:
        try:
            cat = TemplateCategory(category)
        except ValueError:
            pass

    templates = registry.list_templates(
        category=cat,
        regulation=regulation,
        language=language,
        search=search,
    )

    return [
        TemplateResponse(
            id=str(t.id),
            name=t.name,
            description=t.description,
            category=t.category.value,
            regulations=t.regulations,
            languages=t.languages,
            version=t.version,
            tags=t.tags,
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> TemplateResponse:
    """Get template details."""
    from app.services.templates import get_template_registry

    registry = get_template_registry()
    template = registry.get_template(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )

    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        category=template.category.value,
        regulations=template.regulations,
        languages=template.languages,
        version=template.version,
        tags=template.tags,
    )


@router.get("/{template_id}/code/{language}", response_model=TemplateCodeResponse)
async def get_template_code(
    template_id: str,
    language: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> TemplateCodeResponse:
    """Get template code for a specific language."""
    from app.services.templates import get_template_registry

    registry = get_template_registry()
    template = registry.get_template(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )

    if language not in template.code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not available in {language}",
        )

    return TemplateCodeResponse(
        template_id=template_id,
        language=language,
        code=template.code.get(language, ""),
        tests=template.tests.get(language),
        documentation=template.documentation,
    )
