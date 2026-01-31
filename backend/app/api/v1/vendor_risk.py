"""API endpoints for Vendor Risk Compliance Graph."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.vendor_risk import (
    DependencyScanner,
    RiskScorer,
    get_dependency_scanner,
    get_risk_scorer,
)


router = APIRouter(prefix="/vendor-risk", tags=["vendor-risk"])


# Request/Response Models
class ScanRequest(BaseModel):
    """Request to scan repository for dependencies."""
    
    organization_id: UUID
    repository_id: UUID | None = None
    manifests: dict[str, str] = Field(
        ...,
        description="Map of filename to content (e.g., {'package.json': '...'})",
    )


class AssessVendorRequest(BaseModel):
    """Request to assess a single vendor."""
    
    vendor_name: str
    vendor_type: str = "package"
    data_processing: list[str] = []
    certifications: list[str] = []
    organization_regulations: list[str] = []


class InheritanceRequest(BaseModel):
    """Request to calculate compliance inheritance."""
    
    vendor_name: str
    data_processing: list[str]
    organization_regulations: list[str]


# Scan Endpoints
@router.post("/scan")
async def scan_dependencies(request: ScanRequest):
    """Scan repository manifests for dependencies and build vendor graph.
    
    Supported manifest files:
    - package.json (npm)
    - requirements.txt, Pipfile, pyproject.toml (Python)
    - go.mod (Go)
    - Gemfile (Ruby)
    - pom.xml (Maven)
    - Cargo.toml (Rust)
    
    Returns a dependency graph with compliance risk assessment.
    """
    scanner = get_dependency_scanner()
    
    graph = await scanner.scan_repository(
        organization_id=request.organization_id,
        repository_id=request.repository_id,
        files=request.manifests,
    )
    
    return {
        "graph_id": str(graph.id),
        "organization_id": str(graph.organization_id),
        "total_vendors": graph.total_vendors,
        "total_dependencies": graph.total_dependencies,
        "overall_risk": graph.overall_risk.value,
        "risk_summary": {
            "critical": graph.critical_risks,
            "high": graph.high_risks,
            "medium": graph.medium_risks,
        },
        "compliance_summary": {
            "certified": graph.certified_vendors,
            "uncertified": graph.uncertified_vendors,
        },
        "source_files": graph.source,
        "generated_at": graph.generated_at.isoformat(),
    }


@router.get("/graphs/{graph_id}")
async def get_graph(graph_id: UUID):
    """Get vendor graph details."""
    scanner = get_dependency_scanner()
    graph = await scanner.get_graph(graph_id)
    
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    
    return {
        "graph_id": str(graph.id),
        "total_vendors": graph.total_vendors,
        "overall_risk": graph.overall_risk.value,
        "vendors": [
            {
                "name": v.name,
                "type": v.vendor_type.value,
                "version": v.version,
                "registry": v.registry,
                "compliance_tier": v.compliance_tier.value,
                "risk_level": v.risk_level.value,
                "data_processing": v.data_processing,
            }
            for v in graph.vendors.values()
        ],
        "edges": [
            {
                "source": e.source,
                "target": e.target,
                "is_direct": e.is_direct,
            }
            for e in graph.edges
        ],
    }


@router.get("/graphs/{graph_id}/vendors")
async def get_graph_vendors(graph_id: UUID, risk_level: str | None = None):
    """Get vendors from a graph with optional filtering."""
    scanner = get_dependency_scanner()
    graph = await scanner.get_graph(graph_id)
    
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    
    vendors = list(graph.vendors.values())
    
    if risk_level:
        vendors = [v for v in vendors if v.risk_level.value == risk_level]
    
    return {
        "graph_id": str(graph_id),
        "count": len(vendors),
        "vendors": [
            {
                "id": str(v.id),
                "name": v.name,
                "type": v.vendor_type.value,
                "version": v.version,
                "compliance_tier": v.compliance_tier.value,
                "risk_level": v.risk_level.value,
                "certifications": [c.name for c in v.certifications],
                "data_processing": v.data_processing,
                "dependencies": v.dependencies[:10],  # Limit
            }
            for v in vendors
        ],
    }


# Risk Assessment Endpoints
@router.post("/graphs/{graph_id}/assess")
async def assess_graph_risk(
    graph_id: UUID,
    organization_regulations: list[str] | None = None,
):
    """Assess compliance risk for all vendors in a graph.
    
    Returns aggregate risk assessment and vendor-specific recommendations.
    """
    scanner = get_dependency_scanner()
    scorer = get_risk_scorer()
    
    graph = await scanner.get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    
    assessment = await scorer.assess_graph(graph, organization_regulations)
    return assessment


@router.post("/assess")
async def assess_vendor(request: AssessVendorRequest):
    """Assess compliance risk for a single vendor.
    
    Useful for ad-hoc vendor evaluation during procurement.
    """
    from app.services.vendor_risk.models import (
        ComplianceTier,
        Vendor,
        VendorType,
        Certification,
    )
    
    # Create vendor object
    vendor = Vendor(
        name=request.vendor_name,
        vendor_type=VendorType(request.vendor_type) if request.vendor_type else VendorType.PACKAGE,
        data_processing=request.data_processing,
    )
    
    # Add certifications
    for cert_name in request.certifications:
        vendor.certifications.append(Certification(name=cert_name))
    
    # Set compliance tier
    if vendor.certifications:
        vendor.compliance_tier = ComplianceTier.FULLY_CERTIFIED
    else:
        vendor.compliance_tier = ComplianceTier.UNKNOWN
    
    scorer = get_risk_scorer()
    assessment = await scorer.assess_vendor(vendor, request.organization_regulations)
    
    return {
        "vendor_name": assessment.vendor_name,
        "overall_risk": assessment.overall_risk.value,
        "risk_score": assessment.risk_score,
        "scores": {
            "security": round(assessment.security_score, 1),
            "compliance": round(assessment.compliance_score, 1),
            "maintenance": round(assessment.maintenance_score, 1),
            "transparency": round(assessment.transparency_score, 1),
        },
        "risk_factors": assessment.risk_factors,
        "mitigating_factors": assessment.mitigating_factors,
        "recommendations": assessment.recommendations,
        "required_actions": assessment.required_actions,
    }


# Inheritance Endpoints
@router.post("/inheritance")
async def calculate_inheritance(request: InheritanceRequest):
    """Calculate compliance requirements inherited from using a vendor.
    
    Shows what additional compliance work is needed when adding a vendor
    to your technology stack.
    """
    from app.services.vendor_risk.models import Vendor
    
    vendor = Vendor(
        name=request.vendor_name,
        data_processing=request.data_processing,
    )
    
    scorer = get_risk_scorer()
    inheritance = scorer.calculate_inheritance(
        vendor,
        request.organization_regulations,
    )
    
    return {
        "vendor_name": inheritance.vendor_name,
        "affected_regulations": inheritance.affected_regulations,
        "inherited_requirements": inheritance.inherited_requirements,
        "dpa_required": inheritance.dpa_required,
        "baa_required": "HIPAA" in inheritance.affected_regulations,
        "audit_rights_needed": inheritance.audit_rights,
        "compliance_gaps": inheritance.compliance_gaps,
        "impact_summary": inheritance.impact_summary,
    }


# Known Vendors
@router.get("/known-vendors")
async def list_known_vendors():
    """List known vendors in the database with their compliance status."""
    from app.services.vendor_risk.models import KNOWN_VENDORS
    
    return {
        "vendors": [
            {
                "key": key,
                "name": data.get("name", key),
                "type": data.get("type", "unknown").value if hasattr(data.get("type"), "value") else str(data.get("type", "unknown")),
                "certifications": data.get("certifications", []),
                "data_processing": data.get("data_processing", []),
                "risk_level": data.get("risk_level", "unknown").value if hasattr(data.get("risk_level"), "value") else str(data.get("risk_level", "unknown")),
            }
            for key, data in KNOWN_VENDORS.items()
        ],
        "total": len(KNOWN_VENDORS),
    }


@router.get("/known-vendors/{vendor_key}")
async def get_known_vendor(vendor_key: str):
    """Get details about a known vendor."""
    from app.services.vendor_risk.models import KNOWN_VENDORS
    
    vendor_key_lower = vendor_key.lower()
    if vendor_key_lower not in KNOWN_VENDORS:
        raise HTTPException(status_code=404, detail="Vendor not found in database")
    
    data = KNOWN_VENDORS[vendor_key_lower]
    
    return {
        "key": vendor_key_lower,
        "name": data.get("name", vendor_key),
        "type": str(data.get("type", "unknown")),
        "certifications": data.get("certifications", []),
        "data_processing": data.get("data_processing", []),
        "risk_level": str(data.get("risk_level", "unknown")),
    }
