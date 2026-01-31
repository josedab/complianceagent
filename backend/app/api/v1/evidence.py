"""API endpoints for Multi-Framework Evidence Auto-Generator."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.evidence import (
    Framework,
    ExtendedEvidenceCollector,
    get_extended_collector,
    ControlMapper,
    get_control_mapper,
    ReportGenerator,
    get_report_generator,
)


router = APIRouter(prefix="/evidence", tags=["evidence"])


# Request/Response Models
class CollectEvidenceRequest(BaseModel):
    """Request to collect evidence."""
    
    organization_id: UUID
    frameworks: list[str] = Field(..., description="Frameworks: SOC2, ISO27001, HIPAA, GDPR, PCI-DSS, etc.")
    sources: dict[str, Any] | None = None


class GenerateReportRequest(BaseModel):
    """Request to generate evidence report."""
    
    organization_id: UUID
    frameworks: list[str]
    title: str | None = None
    include_evidence_details: bool = True


class GapAnalysisRequest(BaseModel):
    """Request for gap analysis."""
    
    organization_id: UUID
    frameworks: list[str]


class CrossFrameworkRequest(BaseModel):
    """Request for cross-framework analysis."""
    
    organization_id: UUID
    primary_framework: str
    target_frameworks: list[str]


class ControlMappingRequest(BaseModel):
    """Request to get control mappings."""
    
    framework: str
    control_id: str
    target_framework: str | None = None


class CoverageRequest(BaseModel):
    """Request to calculate coverage."""
    
    source_framework: str
    completed_controls: list[str]
    target_framework: str


class ReusePotentialRequest(BaseModel):
    """Request to analyze evidence reuse potential."""
    
    frameworks: list[str]


def _parse_framework(fw: str) -> Framework:
    """Parse framework string to enum."""
    mapping = {
        "soc2": Framework.SOC2,
        "iso27001": Framework.ISO27001,
        "hipaa": Framework.HIPAA,
        "gdpr": Framework.GDPR,
        "pci-dss": Framework.PCI_DSS,
        "pci_dss": Framework.PCI_DSS,
        "sox": Framework.SOX,
        "nist-csf": Framework.NIST_CSF,
        "nist_csf": Framework.NIST_CSF,
        "fedramp": Framework.FEDRAMP,
        "ccpa": Framework.CCPA,
        "eu-ai-act": Framework.EU_AI_ACT,
        "eu_ai_act": Framework.EU_AI_ACT,
    }
    
    fw_lower = fw.lower().strip()
    if fw_lower in mapping:
        return mapping[fw_lower]
    
    try:
        return Framework(fw)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid framework: {fw}. Supported: {[f.value for f in Framework]}",
        )


# Collection Endpoints
@router.post("/collect")
async def collect_evidence(request: CollectEvidenceRequest):
    """Collect compliance evidence for specified frameworks.
    
    Automatically gathers evidence from configured sources for all controls
    in the specified frameworks. Returns collected evidence organized by control.
    """
    frameworks = [_parse_framework(f) for f in request.frameworks]
    collector = get_extended_collector()
    
    collections = await collector.collect_evidence(
        organization_id=request.organization_id,
        frameworks=frameworks,
        sources=request.sources,
    )
    
    # Group by framework
    by_framework = {}
    for collection in collections:
        fw = collection.framework.value
        if fw not in by_framework:
            by_framework[fw] = []
        by_framework[fw].append({
            "collection_id": str(collection.id),
            "control_id": collection.control_id,
            "control_title": collection.control_title,
            "status": collection.status.value,
            "evidence_count": len(collection.evidence),
            "missing_evidence": collection.missing_evidence,
        })
    
    return {
        "organization_id": str(request.organization_id),
        "frameworks": [f.value for f in frameworks],
        "total_collections": len(collections),
        "by_framework": by_framework,
    }


@router.get("/collections/{collection_id}")
async def get_collection(collection_id: UUID):
    """Get evidence collection details."""
    collector = get_extended_collector()
    collection = await collector.get_collection(collection_id)
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    return {
        "id": str(collection.id),
        "organization_id": str(collection.organization_id) if collection.organization_id else None,
        "framework": collection.framework.value,
        "control_id": collection.control_id,
        "control_title": collection.control_title,
        "status": collection.status.value,
        "created_at": collection.created_at.isoformat(),
        "evidence": [
            {
                "id": str(e.id),
                "type": e.evidence_type.value,
                "title": e.title,
                "source": e.source,
                "collected_at": e.collected_at.isoformat(),
                "controls": e.controls,
            }
            for e in collection.evidence
        ],
        "missing_evidence": collection.missing_evidence,
    }


@router.post("/collections/{collection_id}/validate")
async def validate_collection(collection_id: UUID, validator: str):
    """Validate an evidence collection."""
    collector = get_extended_collector()
    collection = await collector.validate_collection(collection_id, validator)
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    return {
        "id": str(collection.id),
        "status": collection.status.value,
        "validated_at": collection.validated_at.isoformat() if collection.validated_at else None,
        "validated_by": collection.validated_by,
    }


# Report Endpoints
@router.post("/reports/generate")
async def generate_report(request: GenerateReportRequest):
    """Generate a comprehensive evidence report.
    
    Creates an audit-ready report showing evidence coverage, gaps,
    and compliance status for the specified frameworks.
    """
    frameworks = [_parse_framework(f) for f in request.frameworks]
    generator = get_report_generator()
    
    report = await generator.generate_report(
        organization_id=request.organization_id,
        frameworks=frameworks,
        title=request.title,
        include_evidence_details=request.include_evidence_details,
    )
    
    return {
        "report_id": str(report.id),
        "title": report.title,
        "generated_at": report.generated_at.isoformat(),
        "frameworks": [f.value for f in report.frameworks],
        "summary": {
            "total_controls": report.total_controls,
            "controls_with_evidence": report.controls_with_evidence,
            "controls_missing_evidence": report.controls_missing_evidence,
            "coverage_percentage": round(report.coverage_percentage, 2),
        },
        "gaps_count": len(report.gaps),
    }


@router.get("/reports/{report_id}")
async def get_report(report_id: UUID, format: str = "json"):
    """Get or export an evidence report."""
    generator = get_report_generator()
    
    try:
        exported = await generator.export_report(report_id, format)
        return exported
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reports/gap-analysis")
async def gap_analysis(request: GapAnalysisRequest):
    """Generate a gap analysis report.
    
    Identifies missing evidence and provides remediation guidance
    for the specified frameworks.
    """
    frameworks = [_parse_framework(f) for f in request.frameworks]
    generator = get_report_generator()
    
    analysis = await generator.generate_gap_analysis(
        organization_id=request.organization_id,
        frameworks=frameworks,
    )
    
    return analysis


@router.post("/reports/cross-framework")
async def cross_framework_report(request: CrossFrameworkRequest):
    """Generate cross-framework evidence mapping report.
    
    Shows how evidence from the primary framework maps to other frameworks,
    useful for organizations pursuing multiple certifications.
    """
    primary = _parse_framework(request.primary_framework)
    targets = [_parse_framework(f) for f in request.target_frameworks]
    generator = get_report_generator()
    
    report = await generator.generate_cross_framework_report(
        organization_id=request.organization_id,
        primary_framework=primary,
        target_frameworks=targets,
    )
    
    return report


# Mapping Endpoints
@router.post("/mappings/lookup")
async def lookup_control_mappings(request: ControlMappingRequest):
    """Find equivalent controls across frameworks.
    
    Returns controls in other frameworks that map to the specified control,
    enabling evidence reuse.
    """
    source_framework = _parse_framework(request.framework)
    target = _parse_framework(request.target_framework) if request.target_framework else None
    
    mapper = get_control_mapper()
    equivalents = mapper.get_equivalent_controls(
        framework=source_framework,
        control_id=request.control_id,
        target_framework=target,
    )
    
    return {
        "source": {
            "framework": source_framework.value,
            "control_id": request.control_id,
        },
        "equivalent_controls": equivalents,
    }


@router.post("/mappings/coverage")
async def calculate_coverage(request: CoverageRequest):
    """Calculate coverage of target framework based on completed controls.
    
    Shows how much of the target framework is covered by evidence
    from completed controls in the source framework.
    """
    source = _parse_framework(request.source_framework)
    target = _parse_framework(request.target_framework)
    
    mapper = get_control_mapper()
    coverage = mapper.calculate_coverage(
        source_framework=source,
        completed_controls=request.completed_controls,
        target_framework=target,
    )
    
    return coverage


@router.post("/mappings/reuse-potential")
async def analyze_reuse_potential(request: ReusePotentialRequest):
    """Analyze evidence reuse potential across frameworks.
    
    Shows opportunities to reuse evidence when pursuing multiple
    compliance certifications simultaneously.
    """
    frameworks = [_parse_framework(f) for f in request.frameworks]
    mapper = get_control_mapper()
    
    report = mapper.generate_reuse_report(frameworks)
    
    return report


# Framework Information
@router.get("/frameworks")
async def list_frameworks():
    """List all supported compliance frameworks."""
    return {
        "frameworks": [
            {"id": f.value, "name": f.value, "description": _get_framework_description(f)}
            for f in Framework
        ]
    }


def _get_framework_description(framework: Framework) -> str:
    """Get description for a framework."""
    descriptions = {
        Framework.SOC2: "Service Organization Control 2 - Trust Services Criteria",
        Framework.ISO27001: "ISO/IEC 27001 - Information Security Management",
        Framework.HIPAA: "Health Insurance Portability and Accountability Act",
        Framework.GDPR: "General Data Protection Regulation (EU)",
        Framework.PCI_DSS: "Payment Card Industry Data Security Standard",
        Framework.SOX: "Sarbanes-Oxley Act - Financial Reporting Controls",
        Framework.NIST_CSF: "NIST Cybersecurity Framework",
        Framework.FEDRAMP: "Federal Risk and Authorization Management Program",
        Framework.CCPA: "California Consumer Privacy Act",
        Framework.EU_AI_ACT: "EU Artificial Intelligence Act",
    }
    return descriptions.get(framework, framework.value)
