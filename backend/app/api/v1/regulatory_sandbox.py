"""API endpoints for Regulatory Sandbox Integration."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.sandbox.regulatory import (
    SandboxProvider,
    ApplicationStatus,
    RegulatorySandboxIntegration,
    get_regulatory_sandbox_integration,
)


router = APIRouter()


# Request/Response Models
class CreateApplicationRequest(BaseModel):
    provider: str
    project_name: str
    project_description: str
    ai_system_type: str = ""


class UpdateApplicationRequest(BaseModel):
    project_description: str | None = None
    innovation_description: str | None = None
    target_market: list[str] | None = None
    risk_classification: str | None = None
    primary_contact: str | None = None


class AddEvidenceRequest(BaseModel):
    requirement_id: str
    evidence_type: str
    title: str
    description: str = ""
    file_reference: str | None = None


class CreateTestRequest(BaseModel):
    name: str
    test_type: str
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    safeguards: list[str] = Field(default_factory=list)


class ApplicationResponse(BaseModel):
    id: str
    provider: str
    status: str
    project_name: str
    requirements_met: int
    requirements_total: int
    created_at: str


class RequirementResponse(BaseModel):
    id: str
    category: str
    description: str
    mandatory: bool
    status: str
    evidence_required: list[str]


# =====================
# SANDBOX DISCOVERY
# =====================

@router.get("/providers")
async def list_sandbox_providers(
    region: str | None = None,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """List available regulatory sandbox providers."""
    sandbox = get_regulatory_sandbox_integration()
    
    providers = await sandbox.get_available_sandboxes(region=region)
    
    return {
        "providers": providers,
        "total": len(providers),
    }


# =====================
# APPLICATION MANAGEMENT
# =====================

@router.post("/applications", response_model=ApplicationResponse)
async def create_application(
    request: CreateApplicationRequest,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> ApplicationResponse:
    """Create a new sandbox application."""
    sandbox = get_regulatory_sandbox_integration()
    
    try:
        provider = SandboxProvider(request.provider)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Valid options: {[p.value for p in SandboxProvider]}",
        )
    
    app = await sandbox.create_application(
        organization_id=organization.id,
        provider=provider,
        project_name=request.project_name,
        project_description=request.project_description,
        ai_system_type=request.ai_system_type,
    )
    
    return ApplicationResponse(
        id=str(app.id),
        provider=app.provider.value,
        status=app.status.value,
        project_name=app.project_name,
        requirements_met=app.requirements_met_count,
        requirements_total=app.requirements_total_count,
        created_at=app.created_at.isoformat(),
    )


@router.get("/applications")
async def list_applications(
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """List sandbox applications for the organization."""
    sandbox = get_regulatory_sandbox_integration()
    
    apps = await sandbox.list_applications(organization.id)
    
    return {
        "applications": [
            ApplicationResponse(
                id=str(app.id),
                provider=app.provider.value,
                status=app.status.value,
                project_name=app.project_name,
                requirements_met=app.requirements_met_count,
                requirements_total=app.requirements_total_count,
                created_at=app.created_at.isoformat(),
            ).model_dump()
            for app in apps
        ],
        "total": len(apps),
    }


@router.get("/applications/{application_id}")
async def get_application(
    application_id: UUID,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Get details of a sandbox application."""
    sandbox = get_regulatory_sandbox_integration()
    
    app = await sandbox.get_application(application_id)
    if not app or app.organization_id != organization.id:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {
        "id": str(app.id),
        "provider": app.provider.value,
        "status": app.status.value,
        "project_name": app.project_name,
        "project_description": app.project_description,
        "innovation_description": app.innovation_description,
        "ai_system_type": app.ai_system_type,
        "target_market": app.target_market,
        "risk_classification": app.risk_classification,
        "requirements_met": app.requirements_met_count,
        "requirements_total": app.requirements_total_count,
        "testing_duration_months": app.testing_duration_months,
        "created_at": app.created_at.isoformat(),
        "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
        "status_history": app.status_history,
        "feedback": app.feedback,
    }


@router.patch("/applications/{application_id}")
async def update_application(
    application_id: UUID,
    request: UpdateApplicationRequest,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Update a sandbox application."""
    sandbox = get_regulatory_sandbox_integration()
    
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    app = await sandbox.update_application(application_id, updates)
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"status": "updated", "application_id": str(application_id)}


@router.post("/applications/{application_id}/submit")
async def submit_application(
    application_id: UUID,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Submit an application for regulatory review."""
    sandbox = get_regulatory_sandbox_integration()
    
    try:
        app = await sandbox.submit_application(application_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {
        "status": "submitted",
        "application_id": str(application_id),
        "submitted_at": app.submitted_at.isoformat(),
    }


# =====================
# REQUIREMENTS & EVIDENCE
# =====================

@router.get("/applications/{application_id}/requirements")
async def get_requirements(
    application_id: UUID,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Get requirements for an application."""
    sandbox = get_regulatory_sandbox_integration()
    
    app = await sandbox.get_application(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {
        "application_id": str(application_id),
        "requirements": [
            RequirementResponse(
                id=r.id,
                category=r.category,
                description=r.description,
                mandatory=r.mandatory,
                status=r.status,
                evidence_required=r.evidence_required,
            ).model_dump()
            for r in app.requirements
        ],
        "met_count": app.requirements_met_count,
        "total_count": app.requirements_total_count,
    }


@router.get("/applications/{application_id}/pre-check")
async def pre_submission_check(
    application_id: UUID,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Check if application is ready for submission."""
    sandbox = get_regulatory_sandbox_integration()
    
    try:
        results = await sandbox.check_pre_submission(application_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return results


@router.post("/applications/{application_id}/requirements/{requirement_id}/status")
async def update_requirement_status(
    application_id: UUID,
    requirement_id: str,
    status: str,
    notes: str = "",
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Update requirement status."""
    sandbox = get_regulatory_sandbox_integration()
    
    req = await sandbox.update_requirement_status(
        application_id=application_id,
        requirement_id=requirement_id,
        status=status,
        notes=notes,
    )
    
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    return {
        "requirement_id": req.id,
        "status": req.status,
        "notes": req.notes,
    }


@router.post("/applications/{application_id}/evidence")
async def add_evidence(
    application_id: UUID,
    request: AddEvidenceRequest,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Add evidence for a requirement."""
    sandbox = get_regulatory_sandbox_integration()
    
    evidence = await sandbox.add_evidence(
        application_id=application_id,
        requirement_id=request.requirement_id,
        evidence_type=request.evidence_type,
        title=request.title,
        description=request.description,
        file_reference=request.file_reference,
    )
    
    return {
        "evidence_id": str(evidence.id),
        "requirement_id": evidence.requirement_id,
        "title": evidence.title,
        "collected_at": evidence.collected_at.isoformat(),
    }


# =====================
# SANDBOX TESTING
# =====================

@router.post("/applications/{application_id}/tests")
async def create_test(
    application_id: UUID,
    request: CreateTestRequest,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Create a sandbox test."""
    sandbox = get_regulatory_sandbox_integration()
    
    try:
        test = await sandbox.create_test(
            application_id=application_id,
            name=request.name,
            test_type=request.test_type,
            description=request.description,
            parameters=request.parameters,
            safeguards=request.safeguards,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "test_id": str(test.id),
        "name": test.name,
        "test_type": test.test_type,
        "status": test.status,
    }


@router.post("/tests/{test_id}/run")
async def run_test(
    test_id: UUID,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Run a sandbox test."""
    sandbox = get_regulatory_sandbox_integration()
    
    try:
        test = await sandbox.run_test(test_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {
        "test_id": str(test.id),
        "status": test.status,
        "started_at": test.started_at.isoformat() if test.started_at else None,
        "completed_at": test.completed_at.isoformat() if test.completed_at else None,
        "results": test.results,
        "compliance_findings": test.compliance_findings,
        "recommendations": test.recommendations,
    }


@router.get("/applications/{application_id}/tests")
async def get_tests(
    application_id: UUID,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Get tests for an application."""
    sandbox = get_regulatory_sandbox_integration()
    
    tests = await sandbox.get_test_results(application_id)
    
    return {
        "application_id": str(application_id),
        "tests": [
            {
                "id": str(t.id),
                "name": t.name,
                "test_type": t.test_type,
                "phase": t.phase.value,
                "status": t.status,
                "findings_count": len(t.compliance_findings),
            }
            for t in tests
        ],
        "total": len(tests),
    }


# =====================
# REPORTING
# =====================

@router.get("/applications/{application_id}/report")
async def generate_report(
    application_id: UUID,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Generate comprehensive sandbox participation report."""
    sandbox = get_regulatory_sandbox_integration()
    
    try:
        report = await sandbox.generate_sandbox_report(application_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return report
