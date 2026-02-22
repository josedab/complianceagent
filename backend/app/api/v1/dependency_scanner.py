"""Dependency Risk Scanner API endpoints."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.dependency_scanner import DependencyScannerService


logger = structlog.get_logger()
router = APIRouter()


class ScanRequest(BaseModel):
    dependencies: list[dict] = Field(..., description="List of {name, version, license} dicts")
    ecosystem: str = Field("pip", description="Package ecosystem: pip, npm, maven, go")
    proprietary_project: bool = Field(
        True, description="True if project is proprietary (flags copyleft)"
    )


@router.post("/scan")
async def scan_dependencies(request: ScanRequest, db: DB) -> dict:
    """Scan dependencies for license, security, and compliance risks."""
    svc = DependencyScannerService(db)
    result = await svc.scan_requirements(
        dependencies=request.dependencies,
        ecosystem=request.ecosystem,
        proprietary_project=request.proprietary_project,
    )
    return {
        "total_dependencies": result.total_dependencies,
        "critical_risks": result.critical_risks,
        "high_risks": result.high_risks,
        "license_violations": result.license_violations,
        "deprecated_crypto_count": result.deprecated_crypto_count,
        "data_sharing_count": result.data_sharing_count,
        "risks": [
            {
                "package": r.package,
                "version": r.version,
                "license": r.license,
                "license_category": r.license_category.value,
                "risk_level": r.risk_level.value,
                "issues": r.issues,
                "data_sharing": r.data_sharing,
                "deprecated_crypto": r.deprecated_crypto,
            }
            for r in result.risks
        ],
    }


@router.get("/history")
async def scan_history(db: DB) -> list[dict]:
    """Get dependency scan history."""
    svc = DependencyScannerService(db)
    results = await svc.get_scan_history()
    return [
        {
            "id": str(r.id),
            "ecosystem": r.ecosystem,
            "total": r.total_dependencies,
            "critical": r.critical_risks,
            "high": r.high_risks,
            "scanned_at": r.scanned_at.isoformat() if r.scanned_at else None,
        }
        for r in results
    ]
