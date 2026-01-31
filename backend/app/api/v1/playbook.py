"""API endpoints for Compliance Playbook Generator."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.playbook import (
    CloudProvider,
    Framework,
    PlaybookCategory,
    PlaybookGenerator,
    StackProfile,
    StepDifficulty,
    TechStack,
    get_playbook_generator,
)


router = APIRouter(prefix="/playbooks", tags=["playbooks"])


# Request/Response Models
class GeneratePlaybookRequest(BaseModel):
    """Request to generate a playbook."""
    
    template: str = Field(..., description="Template slug (e.g., 'encryption_at_rest')")
    tech_stack: str = Field(..., description="Technology stack (python, javascript, java, etc.)")
    framework: str | None = Field(None, description="Framework (fastapi, django, express, etc.)")
    cloud_provider: str | None = Field(None, description="Cloud provider (aws, gcp, azure)")
    organization_id: UUID | None = None
    
    # Additional context
    uses_containers: bool = False
    uses_kubernetes: bool = False
    database_type: str = ""


class StartExecutionRequest(BaseModel):
    """Request to start playbook execution."""
    
    playbook_id: UUID
    organization_id: UUID


class UpdateExecutionRequest(BaseModel):
    """Request to update execution progress."""
    
    completed_step: int | None = None
    skipped_step: int | None = None
    note: str | None = None


def _parse_tech_stack(value: str) -> TechStack:
    """Parse tech stack string."""
    try:
        return TechStack(value.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tech_stack: {value}. Valid: {[t.value for t in TechStack]}",
        )


def _parse_framework(value: str | None) -> Framework | None:
    """Parse framework string."""
    if not value:
        return None
    try:
        return Framework(value.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid framework: {value}. Valid: {[f.value for f in Framework]}",
        )


def _parse_cloud_provider(value: str | None) -> CloudProvider | None:
    """Parse cloud provider string."""
    if not value:
        return None
    try:
        return CloudProvider(value.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cloud_provider: {value}. Valid: {[c.value for c in CloudProvider]}",
        )


# Templates Endpoint
@router.get("/templates")
async def list_templates(
    category: str | None = None,
    regulation: str | None = None,
):
    """List available playbook templates.
    
    Filter by category or regulation to find relevant playbooks.
    """
    generator = get_playbook_generator()
    
    cat_enum = None
    if category:
        try:
            cat_enum = PlaybookCategory(category.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Valid: {[c.value for c in PlaybookCategory]}",
            )
    
    templates = await generator.list_templates(category=cat_enum, regulation=regulation)
    
    return {
        "templates": templates,
        "total": len(templates),
    }


@router.get("/templates/{slug}")
async def get_template(slug: str):
    """Get details about a specific template."""
    from app.services.playbook.models import PLAYBOOK_TEMPLATES
    
    template = PLAYBOOK_TEMPLATES.get(slug)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {
        "slug": slug,
        "name": template["name"],
        "category": template["category"].value,
        "regulations": template.get("regulations", []),
        "controls": template.get("controls", []),
        "difficulty": template.get("difficulty", StepDifficulty.MEDIUM).value,
        "estimated_hours": template.get("estimated_hours", 4),
        "supported_tech_stacks": [t.value for t in TechStack],
        "supported_cloud_providers": [c.value for c in CloudProvider],
    }


# Generation Endpoint
@router.post("/generate")
async def generate_playbook(request: GeneratePlaybookRequest):
    """Generate a customized compliance playbook.
    
    Creates a step-by-step implementation guide tailored to your
    technology stack and cloud provider.
    """
    generator = get_playbook_generator()
    
    # Build stack profile
    profile = StackProfile(
        tech_stack=_parse_tech_stack(request.tech_stack),
        framework=_parse_framework(request.framework),
        cloud_provider=_parse_cloud_provider(request.cloud_provider),
        uses_containers=request.uses_containers,
        uses_kubernetes=request.uses_kubernetes,
        database_type=request.database_type,
    )
    
    try:
        playbook = await generator.generate_playbook(
            template_slug=request.template,
            stack_profile=profile,
            organization_id=request.organization_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "playbook_id": str(playbook.id),
        "name": playbook.name,
        "overview": playbook.overview,
        "regulations": playbook.regulations,
        "controls": playbook.controls,
        "total_steps": playbook.total_steps,
        "estimated_hours": playbook.estimated_hours,
        "difficulty": playbook.difficulty.value,
        "prerequisites": playbook.prerequisites,
        "tech_stack": [t.value for t in playbook.tech_stacks],
        "cloud_provider": [c.value for c in playbook.cloud_providers] if playbook.cloud_providers else None,
    }


@router.get("/{playbook_id}")
async def get_playbook(playbook_id: UUID):
    """Get a generated playbook with all steps."""
    generator = get_playbook_generator()
    playbook = await generator.get_playbook(playbook_id)
    
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    return {
        "id": str(playbook.id),
        "name": playbook.name,
        "slug": playbook.slug,
        "category": playbook.category.value,
        "overview": playbook.overview,
        "regulations": playbook.regulations,
        "controls": playbook.controls,
        "total_steps": playbook.total_steps,
        "estimated_hours": playbook.estimated_hours,
        "difficulty": playbook.difficulty.value,
        "prerequisites": playbook.prerequisites,
        "steps": [
            {
                "step_number": s.step_number,
                "title": s.title,
                "description": s.description,
                "code_snippet": s.code_snippet,
                "commands": s.commands,
                "prerequisites": s.prerequisites,
                "difficulty": s.difficulty.value,
                "estimated_minutes": s.estimated_minutes,
                "verification_steps": s.verification_steps,
            }
            for s in playbook.steps
        ],
        "evidence_generated": playbook.evidence_generated,
        "created_at": playbook.created_at.isoformat(),
    }


@router.get("/{playbook_id}/steps/{step_number}")
async def get_playbook_step(playbook_id: UUID, step_number: int):
    """Get details for a specific step."""
    generator = get_playbook_generator()
    playbook = await generator.get_playbook(playbook_id)
    
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    step = next((s for s in playbook.steps if s.step_number == step_number), None)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    # Include context
    prev_step = next((s for s in playbook.steps if s.step_number == step_number - 1), None)
    next_step = next((s for s in playbook.steps if s.step_number == step_number + 1), None)
    
    return {
        "playbook_id": str(playbook_id),
        "total_steps": playbook.total_steps,
        "step": {
            "step_number": step.step_number,
            "title": step.title,
            "description": step.description,
            "code_snippet": step.code_snippet,
            "commands": step.commands,
            "file_changes": step.file_changes,
            "prerequisites": step.prerequisites,
            "required_tools": step.required_tools,
            "difficulty": step.difficulty.value,
            "estimated_minutes": step.estimated_minutes,
            "responsible_role": step.responsible_role,
            "verification_steps": step.verification_steps,
            "expected_outcome": step.expected_outcome,
        },
        "navigation": {
            "previous": prev_step.step_number if prev_step else None,
            "next": next_step.step_number if next_step else None,
        },
    }


# Execution Endpoints
@router.post("/executions")
async def start_execution(request: StartExecutionRequest):
    """Start executing a playbook.
    
    Tracks progress through playbook steps.
    """
    generator = get_playbook_generator()
    
    playbook = await generator.get_playbook(request.playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    execution = await generator.start_execution(
        playbook_id=request.playbook_id,
        organization_id=request.organization_id,
    )
    
    return {
        "execution_id": str(execution.id),
        "playbook_id": str(execution.playbook_id),
        "status": execution.status,
        "current_step": execution.current_step,
        "total_steps": playbook.total_steps,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
    }


@router.patch("/executions/{execution_id}")
async def update_execution(execution_id: UUID, request: UpdateExecutionRequest):
    """Update execution progress."""
    generator = get_playbook_generator()
    
    execution = await generator.update_execution(
        execution_id=execution_id,
        completed_step=request.completed_step,
        skipped_step=request.skipped_step,
        note=request.note,
    )
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    playbook = await generator.get_playbook(execution.playbook_id)
    
    return {
        "execution_id": str(execution.id),
        "status": execution.status,
        "current_step": execution.current_step,
        "completed_steps": execution.completed_steps,
        "skipped_steps": execution.skipped_steps,
        "progress_percent": round(
            (len(execution.completed_steps) + len(execution.skipped_steps))
            / playbook.total_steps * 100
            if playbook else 0,
            1,
        ),
    }


# Categories and Options
@router.get("/categories")
async def list_categories():
    """List all playbook categories."""
    return {
        "categories": [
            {"value": c.value, "name": c.value.replace("_", " ").title()}
            for c in PlaybookCategory
        ]
    }


@router.get("/tech-stacks")
async def list_tech_stacks():
    """List supported technology stacks."""
    return {
        "tech_stacks": [t.value for t in TechStack]
    }


@router.get("/frameworks")
async def list_frameworks():
    """List supported frameworks."""
    return {
        "frameworks": [f.value for f in Framework]
    }


@router.get("/cloud-providers")
async def list_cloud_providers():
    """List supported cloud providers."""
    return {
        "cloud_providers": [c.value for c in CloudProvider]
    }
