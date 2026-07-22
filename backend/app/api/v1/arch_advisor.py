"""API endpoints for Architecture Advisor."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.arch_advisor import ArchAdvisorService, ArchAdvisorStats, ArchitectureDiagram


logger = structlog.get_logger()
router = APIRouter()


# --- Request / Response Schemas ---


class GenerateArchitectureRequest(BaseModel):
    frameworks: list[str] = Field(..., description="Frameworks to include in the architecture")
    diagram_format: str = Field("mermaid", description="Output diagram format")
    app_name: str = Field(..., description="Application name for the architecture")


# --- Endpoints ---


@router.post("/generate")
async def generate_architecture(
    request: GenerateArchitectureRequest, db: DB
) -> ArchitectureDiagram:
    """Generate a compliance architecture diagram."""
    svc = ArchAdvisorService(db)
    return await svc.generate_architecture(
        frameworks=request.frameworks,
        diagram_format=request.diagram_format,
        app_name=request.app_name,
    )


@router.get("/frameworks")
async def list_available_frameworks(db: DB) -> list[str]:
    """List available compliance frameworks."""
    svc = ArchAdvisorService(db)
    return svc.list_available_frameworks()


@router.get("/stats")
async def get_stats(db: DB) -> ArchAdvisorStats:
    """Get architecture advisor statistics."""
    svc = ArchAdvisorService(db)
    return svc.get_stats()
