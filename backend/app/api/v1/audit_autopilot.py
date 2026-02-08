"""API endpoints for Audit Preparation Autopilot."""

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.audit_autopilot import AuditAutopilotService, AuditFramework

logger = structlog.get_logger()
router = APIRouter()


class GapAnalysisSchema(BaseModel):
    id: str
    framework: str
    total_controls: int
    controls_met: int
    controls_partial: int
    controls_missing: int
    readiness_score: float
    critical_gaps: list[str]
    estimated_remediation_hours: float


class EvidencePackageSchema(BaseModel):
    id: str
    framework: str
    title: str
    total_items: int
    controls_covered: int
    total_controls: int
    coverage_percent: float


class ReadinessReportSchema(BaseModel):
    id: str
    framework: str
    overall_readiness: float
    recommendations: list[str]
    estimated_prep_weeks: float


def _parse_framework(fw: str) -> AuditFramework:
    try:
        return AuditFramework(fw)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported framework: {fw}. Use: {[f.value for f in AuditFramework]}")


@router.post("/gap-analysis/{framework}", response_model=GapAnalysisSchema, summary="Run gap analysis")
async def run_gap_analysis(framework: str, db: DB, copilot: CopilotDep) -> GapAnalysisSchema:
    fw = _parse_framework(framework)
    service = AuditAutopilotService(db=db, copilot_client=copilot)
    analysis = await service.run_gap_analysis(fw)
    return GapAnalysisSchema(
        id=str(analysis.id), framework=analysis.framework.value,
        total_controls=analysis.total_controls, controls_met=analysis.controls_met,
        controls_partial=analysis.controls_partial, controls_missing=analysis.controls_missing,
        readiness_score=analysis.readiness_score, critical_gaps=analysis.critical_gaps,
        estimated_remediation_hours=analysis.estimated_remediation_hours,
    )


@router.post("/evidence-package/{framework}", response_model=EvidencePackageSchema, summary="Generate evidence package")
async def generate_evidence_package(framework: str, db: DB, copilot: CopilotDep) -> EvidencePackageSchema:
    fw = _parse_framework(framework)
    service = AuditAutopilotService(db=db, copilot_client=copilot)
    package = await service.generate_evidence_package(fw)
    return EvidencePackageSchema(
        id=str(package.id), framework=package.framework.value, title=package.title,
        total_items=package.total_items, controls_covered=package.controls_covered,
        total_controls=package.total_controls, coverage_percent=package.coverage_percent,
    )


@router.post("/readiness-report/{framework}", response_model=ReadinessReportSchema, summary="Generate readiness report")
async def generate_readiness_report(framework: str, db: DB, copilot: CopilotDep) -> ReadinessReportSchema:
    fw = _parse_framework(framework)
    service = AuditAutopilotService(db=db, copilot_client=copilot)
    report = await service.generate_readiness_report(fw)
    return ReadinessReportSchema(
        id=str(report.id), framework=report.framework.value,
        overall_readiness=report.overall_readiness, recommendations=report.recommendations,
        estimated_prep_weeks=report.estimated_prep_weeks,
    )


@router.get("/frameworks", summary="List supported audit frameworks")
async def list_frameworks(db: DB, copilot: CopilotDep) -> list[dict]:
    service = AuditAutopilotService(db=db, copilot_client=copilot)
    return await service.list_supported_frameworks()
