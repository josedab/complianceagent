"""CI/CD compliance gate API endpoints."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.cicd import CICDComplianceService


router = APIRouter()


class FileContent(BaseModel):
    """File content for scanning."""

    path: str = Field(..., description="File path relative to repository root")
    content: str = Field(..., description="File content")


class ScanRequest(BaseModel):
    """Request for CI/CD compliance scan."""

    files: list[FileContent] = Field(..., description="Files to scan")
    regulations: list[str] | None = Field(
        default=None,
        description="Regulations to check (e.g., GDPR, CCPA, HIPAA). Defaults to all.",
    )
    fail_on_severity: str = Field(
        default="error",
        description="Minimum severity to fail the check (error, warning, info)",
    )
    include_ai_fixes: bool = Field(
        default=True,
        description="Include AI-generated fix suggestions",
    )
    incremental: bool = Field(
        default=False,
        description="Only report issues in changed lines",
    )
    diff: str | None = Field(
        default=None,
        description="Git diff for incremental scanning",
    )
    repository: str | None = Field(
        default=None,
        description="Repository identifier (e.g., owner/repo)",
    )
    commit_sha: str | None = Field(
        default=None,
        description="Git commit SHA",
    )
    branch: str | None = Field(
        default=None,
        description="Git branch name",
    )
    pr_number: int | None = Field(
        default=None,
        description="Pull request number",
    )
    output_format: str = Field(
        default="full",
        description="Output format: full, sarif, markdown, gitlab",
    )


class ScanIssue(BaseModel):
    """A compliance issue found during scan."""

    file: str
    line: int
    column: int
    end_line: int
    end_column: int
    code: str
    message: str
    severity: str
    regulation: str | None = None
    article_reference: str | None = None
    category: str | None = None
    fix_code: str | None = None
    fix_explanation: str | None = None
    ai_generated: bool = False
    confidence: float | None = None


class ScanResponse(BaseModel):
    """Response from compliance scan."""

    scan_id: str
    passed: bool
    files_analyzed: int
    total_issues: int
    critical_count: int
    warning_count: int
    info_count: int
    by_regulation: dict[str, int]
    issues: list[ScanIssue]
    scanned_at: datetime


class SARIFResponse(BaseModel):
    """SARIF format response."""

    scan_id: str
    passed: bool
    sarif: dict[str, Any]


class MarkdownResponse(BaseModel):
    """Markdown summary response."""

    scan_id: str
    passed: bool
    markdown: str


class GitLabReportResponse(BaseModel):
    """GitLab Code Quality report response."""

    scan_id: str
    passed: bool
    issues: list[dict[str, Any]]


class CheckRunRequest(BaseModel):
    """Request to create GitHub check run."""

    owner: str
    repo: str
    head_sha: str
    scan_id: str


@router.post("/scan", response_model=ScanResponse)
async def run_compliance_scan(
    request: ScanRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ScanResponse:
    """Run compliance scan on provided files.

    This endpoint is used by CI/CD pipelines to check code for compliance
    issues before merging.

    Returns detailed results including issues found, severity counts,
    and optional AI-generated fixes.
    """
    from app.services.cicd.service import CICDScanRequest

    service = CICDComplianceService()

    scan_request = CICDScanRequest(
        files=[{"path": f.path, "content": f.content} for f in request.files],
        regulations=request.regulations,
        fail_on_severity=request.fail_on_severity,
        include_ai_fixes=request.include_ai_fixes,
        incremental=request.incremental,
        diff=request.diff,
        repository=request.repository,
        commit_sha=request.commit_sha,
        branch=request.branch,
        pr_number=request.pr_number,
    )

    result = await service.run_scan(scan_request)

    issues = [
        ScanIssue(
            file=i["file"],
            line=i["line"],
            column=i["column"],
            end_line=i["end_line"],
            end_column=i["end_column"],
            code=i["code"],
            message=i["message"],
            severity=i["severity"],
            regulation=i.get("regulation"),
            article_reference=i.get("article_reference"),
            category=i.get("category"),
            fix_code=i.get("fix_code"),
            fix_explanation=i.get("fix_explanation"),
            ai_generated=i.get("ai_generated", False),
            confidence=i.get("confidence"),
        )
        for i in result.issues
    ]

    return ScanResponse(
        scan_id=result.scan_id,
        passed=result.passed,
        files_analyzed=result.files_analyzed,
        total_issues=result.total_issues,
        critical_count=result.critical_count,
        warning_count=result.warning_count,
        info_count=result.info_count,
        by_regulation=result.by_regulation,
        issues=issues,
        scanned_at=result.scanned_at,
    )


@router.post("/scan/sarif", response_model=SARIFResponse)
async def run_scan_sarif(
    request: ScanRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SARIFResponse:
    """Run compliance scan and return SARIF format.

    SARIF (Static Analysis Results Interchange Format) is used by
    GitHub Security tab and other security tools.
    """
    from app.services.cicd.service import CICDScanRequest

    service = CICDComplianceService()

    scan_request = CICDScanRequest(
        files=[{"path": f.path, "content": f.content} for f in request.files],
        regulations=request.regulations,
        fail_on_severity=request.fail_on_severity,
        include_ai_fixes=False,  # SARIF doesn't include fixes
        incremental=request.incremental,
        diff=request.diff,
        repository=request.repository,
        commit_sha=request.commit_sha,
    )

    result = await service.run_scan(scan_request)

    return SARIFResponse(
        scan_id=result.scan_id,
        passed=result.passed,
        sarif=result.sarif,
    )


@router.post("/scan/markdown", response_model=MarkdownResponse)
async def run_scan_markdown(
    request: ScanRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> MarkdownResponse:
    """Run compliance scan and return markdown summary.

    Returns a formatted markdown summary suitable for PR comments.
    """
    from app.services.cicd.service import CICDScanRequest

    service = CICDComplianceService()

    scan_request = CICDScanRequest(
        files=[{"path": f.path, "content": f.content} for f in request.files],
        regulations=request.regulations,
        fail_on_severity=request.fail_on_severity,
        include_ai_fixes=request.include_ai_fixes,
        incremental=request.incremental,
        diff=request.diff,
        repository=request.repository,
        commit_sha=request.commit_sha,
        branch=request.branch,
        pr_number=request.pr_number,
    )

    result = await service.run_scan(scan_request)

    return MarkdownResponse(
        scan_id=result.scan_id,
        passed=result.passed,
        markdown=result.markdown_summary,
    )


@router.post("/scan/gitlab", response_model=GitLabReportResponse)
async def run_scan_gitlab(
    request: ScanRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> GitLabReportResponse:
    """Run compliance scan and return GitLab Code Quality format.

    Returns results in GitLab Code Quality report format for
    integration with GitLab CI/CD.
    """
    from app.services.cicd.service import CICDScanRequest

    service = CICDComplianceService()

    scan_request = CICDScanRequest(
        files=[{"path": f.path, "content": f.content} for f in request.files],
        regulations=request.regulations,
        fail_on_severity=request.fail_on_severity,
        include_ai_fixes=False,
        incremental=request.incremental,
        diff=request.diff,
        repository=request.repository,
        commit_sha=request.commit_sha,
    )

    result = await service.run_scan(scan_request)
    gitlab_issues = service.generate_gitlab_report(result)

    return GitLabReportResponse(
        scan_id=result.scan_id,
        passed=result.passed,
        issues=gitlab_issues,
    )


@router.get("/regulations")
async def list_supported_regulations(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """List all supported regulations for CI/CD scanning."""
    return {
        "regulations": [
            {
                "code": "GDPR",
                "name": "General Data Protection Regulation",
                "jurisdiction": "EU",
                "categories": ["data_privacy", "consent", "data_transfer", "encryption"],
            },
            {
                "code": "CCPA",
                "name": "California Consumer Privacy Act",
                "jurisdiction": "US-CA",
                "categories": ["data_privacy", "consent", "data_sale"],
            },
            {
                "code": "HIPAA",
                "name": "Health Insurance Portability and Accountability Act",
                "jurisdiction": "US-Federal",
                "categories": ["data_privacy", "encryption", "audit_logging", "access_control"],
            },
            {
                "code": "EU AI Act",
                "name": "EU Artificial Intelligence Act",
                "jurisdiction": "EU",
                "categories": ["ai_transparency", "ai_documentation", "ai_testing"],
            },
            {
                "code": "SOX",
                "name": "Sarbanes-Oxley Act",
                "jurisdiction": "US-Federal",
                "categories": ["audit_logging", "access_control", "data_integrity"],
            },
            {
                "code": "PCI-DSS",
                "name": "Payment Card Industry Data Security Standard",
                "jurisdiction": "Global",
                "categories": ["encryption", "access_control", "audit_logging", "security"],
            },
            {
                "code": "NIS2",
                "name": "Network and Information Security Directive 2",
                "jurisdiction": "EU",
                "categories": ["security", "incident_response", "risk_management"],
            },
            {
                "code": "SOC 2",
                "name": "System and Organization Controls 2",
                "jurisdiction": "Global",
                "categories": ["security", "availability", "processing_integrity", "confidentiality"],
            },
        ],
    }
