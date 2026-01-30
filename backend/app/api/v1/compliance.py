"""Compliance status and analysis endpoints."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization, OrgMember
from app.models.audit import ComplianceAction
from app.models.codebase import CodebaseMapping, ComplianceStatus, Repository
from app.models.customer_profile import CustomerProfile
from app.models.requirement import Requirement
from app.schemas.compliance import (
    AffectedFile,
    CodeGenerationRequest,
    CodeGenerationResponse,
    ComplianceStatusResponse,
    FrameworkComplianceStatus,
    GeneratedFile,
    GeneratedTest,
    ImpactAssessmentResponse,
)


logger = structlog.get_logger()
router = APIRouter()


@router.get("/status", response_model=ComplianceStatusResponse)
async def get_compliance_status(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    repository_id: UUID | None = None,
) -> ComplianceStatusResponse:
    """Get overall compliance status for the organization."""
    # Base query for repositories
    repo_query = (
        select(Repository)
        .join(CustomerProfile)
        .where(CustomerProfile.organization_id == organization.id)
    )
    if repository_id:
        repo_query = repo_query.where(Repository.id == repository_id)

    repo_result = await db.execute(repo_query)
    repositories = list(repo_result.scalars().all())

    if not repositories:
        return ComplianceStatusResponse(
            organization_id=organization.id,
            repository_id=repository_id,
            overall_score=0,
            overall_status=ComplianceStatus.NOT_APPLICABLE,
            frameworks=[],
            total_requirements=0,
            compliant_requirements=0,
            pending_actions=0,
            overdue_actions=0,
            assessed_at=datetime.now(UTC),
        )

    repo_ids = [r.id for r in repositories]

    # Get mappings
    mappings_result = await db.execute(
        select(CodebaseMapping)
        .options(selectinload(CodebaseMapping.requirement).selectinload(Requirement.regulation))
        .where(CodebaseMapping.repository_id.in_(repo_ids))
    )
    mappings = list(mappings_result.scalars().all())

    # Calculate per-framework status
    framework_stats: dict[str, dict] = {}
    total_reqs = 0
    compliant_reqs = 0

    for mapping in mappings:
        framework = mapping.requirement.regulation.framework.value
        if framework not in framework_stats:
            framework_stats[framework] = {
                "compliant": 0,
                "total": 0,
                "critical_gaps": 0,
                "major_gaps": 0,
                "minor_gaps": 0,
            }

        framework_stats[framework]["total"] += 1
        total_reqs += 1

        if mapping.compliance_status == ComplianceStatus.COMPLIANT:
            framework_stats[framework]["compliant"] += 1
            compliant_reqs += 1

        framework_stats[framework]["critical_gaps"] += mapping.critical_gaps
        framework_stats[framework]["major_gaps"] += mapping.major_gaps
        framework_stats[framework]["minor_gaps"] += mapping.minor_gaps

    # Build framework status list
    frameworks = []
    for fw, stats in framework_stats.items():
        pct = (stats["compliant"] / stats["total"] * 100) if stats["total"] > 0 else 0
        if pct >= 90:
            fw_status = ComplianceStatus.COMPLIANT
        elif pct >= 50:
            fw_status = ComplianceStatus.PARTIAL
        else:
            fw_status = ComplianceStatus.NON_COMPLIANT

        frameworks.append(
            FrameworkComplianceStatus(
                framework=fw,
                status=fw_status,
                compliant_count=stats["compliant"],
                total_count=stats["total"],
                compliance_percentage=pct,
                critical_gaps=stats["critical_gaps"],
                major_gaps=stats["major_gaps"],
                minor_gaps=stats["minor_gaps"],
            )
        )

    # Get pending actions
    actions_result = await db.execute(
        select(func.count())
        .select_from(ComplianceAction)
        .where(
            ComplianceAction.organization_id == organization.id,
            ComplianceAction.status.in_(["pending", "in_progress", "awaiting_review"]),
        )
    )
    pending_actions = actions_result.scalar() or 0

    # Calculate overall status
    overall_pct = (compliant_reqs / total_reqs * 100) if total_reqs > 0 else 0
    if overall_pct >= 90:
        overall_status = ComplianceStatus.COMPLIANT
    elif overall_pct >= 50:
        overall_status = ComplianceStatus.PARTIAL
    elif total_reqs == 0:
        overall_status = ComplianceStatus.NOT_APPLICABLE
    else:
        overall_status = ComplianceStatus.NON_COMPLIANT

    return ComplianceStatusResponse(
        organization_id=organization.id,
        repository_id=repository_id,
        overall_score=overall_pct,
        overall_status=overall_status,
        frameworks=frameworks,
        total_requirements=total_reqs,
        compliant_requirements=compliant_reqs,
        pending_actions=pending_actions,
        overdue_actions=0,  # TODO: Calculate based on deadlines
        assessed_at=datetime.now(UTC),
    )


@router.post("/assess/{mapping_id}", response_model=ImpactAssessmentResponse)
async def assess_impact(
    mapping_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ImpactAssessmentResponse:
    """Generate impact assessment for a mapping."""
    result = await db.execute(
        select(CodebaseMapping)
        .options(
            selectinload(CodebaseMapping.repository).selectinload(Repository.customer_profile),
            selectinload(CodebaseMapping.requirement).selectinload(Requirement.regulation),
        )
        .where(CodebaseMapping.id == mapping_id)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found",
        )

    if mapping.repository.customer_profile.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mapping not accessible",
        )

    # Build affected files list from mapping data
    affected_files = []
    for file_path in mapping.affected_files or []:
        affected_files.append(AffectedFile(
            path=file_path,
            change_type="modify",
            lines_added=0,
            lines_removed=0,
            complexity_change=0,
        ))

    # Calculate risk factors based on gaps
    risk_factors = []
    if mapping.critical_gaps > 0:
        risk_factors.append(f"{mapping.critical_gaps} critical compliance gap(s) requiring immediate attention")
    if mapping.major_gaps > 0:
        risk_factors.append(f"{mapping.major_gaps} major gap(s) affecting core functionality")
    if mapping.minor_gaps > 0:
        risk_factors.append(f"{mapping.minor_gaps} minor gap(s) for documentation or non-critical areas")
    if mapping.mapping_confidence < 0.7:
        risk_factors.append("Low AI confidence - manual review strongly recommended")

    # Determine dependencies from gaps
    dependencies = []
    for gap in mapping.gaps or []:
        if gap.get("dependencies"):
            dependencies.extend(gap["dependencies"])
    dependencies = list(set(dependencies))  # Deduplicate

    # Calculate days until deadline
    days_until_deadline = None
    if mapping.requirement.regulation.effective_date:
        deadline = mapping.requirement.regulation.effective_date
        days_until_deadline = (deadline - datetime.now(UTC).date()).days

    # Determine recommended priority
    if mapping.critical_gaps > 0 or (days_until_deadline is not None and days_until_deadline < 30):
        recommended_priority = "critical"
    elif mapping.major_gaps > 0 or (days_until_deadline is not None and days_until_deadline < 90):
        recommended_priority = "high"
    elif mapping.minor_gaps > 0:
        recommended_priority = "medium"
    else:
        recommended_priority = "low"

    # Build summary from mapping analysis
    summary_parts = [f"Impact assessment for requirement: {mapping.requirement.title}"]
    if mapping.compliance_status == ComplianceStatus.COMPLIANT:
        summary_parts.append("Repository is compliant with this requirement.")
    elif mapping.compliance_status == ComplianceStatus.NON_COMPLIANT:
        summary_parts.append(f"Found {mapping.gap_count} compliance gaps requiring remediation.")
    elif mapping.compliance_status == ComplianceStatus.PARTIAL:
        summary_parts.append("Partial compliance detected. Some implementations exist but gaps remain.")
    else:
        summary_parts.append("Compliance status pending review.")

    return ImpactAssessmentResponse(
        regulation_id=mapping.requirement.regulation_id,
        requirement_id=mapping.requirement_id,
        repository_id=mapping.repository_id,
        summary=" ".join(summary_parts),
        affected_files=affected_files,
        total_files_affected=len(mapping.affected_files or []),
        total_lines_affected=sum(f.lines_added + f.lines_removed for f in affected_files),
        estimated_effort_hours=mapping.estimated_effort_hours or (mapping.gap_count * 4.0),
        estimated_effort_description=mapping.estimated_effort_description or f"Estimated {mapping.gap_count} gap(s) to address",
        risk_level=mapping.risk_level or ("high" if mapping.critical_gaps > 0 else "medium"),
        risk_factors=risk_factors,
        dependencies=dependencies,
        recommended_priority=recommended_priority,
        deadline=mapping.requirement.regulation.effective_date,
        days_until_deadline=days_until_deadline,
        confidence=mapping.mapping_confidence,
        assessed_at=datetime.now(UTC),
    )


@router.post("/generate", response_model=CodeGenerationResponse)
async def generate_compliant_code(
    request: CodeGenerationRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> CodeGenerationResponse:
    """Generate compliant code for a mapping using AI.
    
    This endpoint uses the GitHub Copilot integration to analyze compliance
    gaps and generate code that addresses regulatory requirements.
    """
    result = await db.execute(
        select(CodebaseMapping)
        .options(
            selectinload(CodebaseMapping.repository).selectinload(Repository.customer_profile),
            selectinload(CodebaseMapping.requirement).selectinload(Requirement.regulation),
        )
        .where(CodebaseMapping.id == request.mapping_id)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found",
        )

    if mapping.repository.customer_profile.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mapping not accessible",
        )

    # Build requirement data for AI
    requirement_data = {
        "title": mapping.requirement.title,
        "description": mapping.requirement.description,
        "reference_id": mapping.requirement.reference_id,
        "regulation_name": mapping.requirement.regulation.name if mapping.requirement.regulation else "Unknown",
        "framework": mapping.requirement.regulation.framework.value if mapping.requirement.regulation else None,
    }

    # Identify compliance gaps from the mapping
    gaps = []
    if mapping.compliance_status != ComplianceStatus.COMPLIANT:
        gaps.append({
            "severity": "high" if mapping.compliance_status == ComplianceStatus.NON_COMPLIANT else "medium",
            "description": f"Code at {mapping.code_location} needs to address {mapping.requirement.title}",
            "location": mapping.code_location,
        })
        if mapping.gap_analysis:
            for gap in mapping.gap_analysis.get("gaps", []):
                gaps.append({
                    "severity": gap.get("severity", "medium"),
                    "description": gap.get("description", "Compliance gap identified"),
                })

    # Get existing code context
    existing_code = {}
    if mapping.code_snippet:
        existing_code[mapping.code_location or "unknown"] = mapping.code_snippet

    # Determine language from repository or mapping
    language = "python"  # Default fallback
    if mapping.repository.default_branch:
        language = _detect_language(mapping.code_location or "")

    try:
        logger.info(
            "Generating compliant code",
            mapping_id=str(mapping.id),
            requirement_id=str(mapping.requirement_id),
            gaps_count=len(gaps),
        )

        ai_result = await copilot.generate_compliant_code(
            requirement=requirement_data,
            gaps=gaps,
            existing_code=existing_code,
            language=language,
            style_guide=request.style_guide,
        )

        # Transform AI response to schema format
        files = [
            GeneratedFile(
                path=f.get("path", "unknown"),
                operation=f.get("operation", "create"),
                content=f.get("content"),
                diff=f.get("diff"),
                language=f.get("language", language),
            )
            for f in ai_result.get("files", [])
        ]

        tests = [
            GeneratedTest(
                path=t.get("path", "test_compliance.py"),
                test_type=t.get("test_type", "unit"),
                content=t.get("content", ""),
                description=t.get("description", "Generated compliance test"),
            )
            for t in ai_result.get("tests", [])
        ]

        return CodeGenerationResponse(
            mapping_id=mapping.id,
            requirement_id=mapping.requirement_id,
            files=files,
            tests=tests,
            documentation=ai_result.get("documentation"),
            pr_title=ai_result.get("pr_title", f"Compliance: {mapping.requirement.title}"),
            pr_body=ai_result.get("pr_body", f"This PR addresses compliance requirement {mapping.requirement.reference_id}"),
            compliance_comments=ai_result.get("compliance_comments", []),
            confidence=ai_result.get("confidence", 0.0),
            warnings=ai_result.get("warnings", []),
            generated_at=datetime.now(UTC),
        )

    except Exception as e:
        logger.exception(
            "Code generation failed",
            mapping_id=str(mapping.id),
            error=str(e),
        )
        return CodeGenerationResponse(
            mapping_id=mapping.id,
            requirement_id=mapping.requirement_id,
            files=[],
            tests=[],
            documentation=None,
            pr_title=f"Compliance: {mapping.requirement.title}",
            pr_body=f"This PR addresses compliance requirement {mapping.requirement.reference_id}",
            confidence=0.0,
            warnings=[f"Code generation failed: {str(e)}"],
            generated_at=datetime.now(UTC),
        )


def _detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".swift": "swift",
        ".kt": "kotlin",
    }
    for ext, lang in extension_map.items():
        if file_path.endswith(ext):
            return lang
    return "python"
