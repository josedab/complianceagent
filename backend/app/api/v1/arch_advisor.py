"""API endpoints for Architecture Advisor."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.arch_advisor import ArchAdvisorService


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class GenerateArchitectureRequest(BaseModel):
    frameworks: list[str] = Field(..., description="Frameworks to include in the architecture")
    diagram_format: str = Field("mermaid", description="Output diagram format")
    app_name: str = Field(..., description="Application name for the architecture")


# --- Endpoints ---


@router.post("/generate")
async def generate_architecture(request: GenerateArchitectureRequest, db: DB) -> dict:
    """Generate a compliance architecture diagram."""
    svc = ArchAdvisorService()
    return await svc.generate_architecture(
        db,
        frameworks=request.frameworks,
        diagram_format=request.diagram_format,
        app_name=request.app_name,
    )


@router.get("/frameworks")
async def list_available_frameworks(db: DB) -> list[dict]:
    """List available compliance frameworks."""
    svc = ArchAdvisorService()
    return await svc.list_available_frameworks(db)


@router.get("/stats")
async def get_stats(db: DB) -> dict:
    """Get architecture advisor statistics."""
    svc = ArchAdvisorService()
    return await svc.get_stats(db)
