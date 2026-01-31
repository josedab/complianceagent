"""Cloud Compliance API endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.v1.deps import DB, CurrentOrganization, OrgMember


router = APIRouter()


class CloudFinding(BaseModel):
    """A cloud compliance finding."""

    rule_id: str
    file_path: str
    line_number: int
    resource_name: str
    resource_type: str
    severity: str
    message: str
    regulation: str
    remediation: str


class CloudScanRequest(BaseModel):
    """Request to scan IaC code."""

    content: str
    file_path: str
    iac_type: str = "terraform"  # terraform, cloudformation, kubernetes
    regulations: list[str] | None = None


class CloudScanResponse(BaseModel):
    """Response from cloud compliance scan."""

    findings: list[CloudFinding]
    files_scanned: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


@router.post("/scan", response_model=CloudScanResponse)
async def scan_cloud_iac(
    request: CloudScanRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> CloudScanResponse:
    """Scan IaC code for cloud compliance issues."""
    from app.services.cloud import CloudComplianceAnalyzer

    analyzer = CloudComplianceAnalyzer()

    if request.iac_type == "terraform":
        findings = analyzer.analyze_terraform(
            content=request.content,
            file_path=request.file_path,
            regulations=request.regulations,
        )
    elif request.iac_type == "cloudformation":
        findings = analyzer.analyze_cloudformation(
            content=request.content,
            file_path=request.file_path,
            regulations=request.regulations,
        )
    elif request.iac_type == "kubernetes":
        findings = analyzer.analyze_kubernetes(
            content=request.content,
            file_path=request.file_path,
            regulations=request.regulations,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported IaC type: {request.iac_type}",
        )

    # Count by severity
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

    return CloudScanResponse(
        findings=[
            CloudFinding(
                rule_id=f.rule_id,
                file_path=f.file_path,
                line_number=f.line_number,
                resource_name=f.resource_name,
                resource_type=f.resource_type,
                severity=f.severity,
                message=f.message,
                regulation=f.regulation,
                remediation=f.remediation,
            )
            for f in findings
        ],
        files_scanned=1,
        critical_count=severity_counts["critical"],
        high_count=severity_counts["high"],
        medium_count=severity_counts["medium"],
        low_count=severity_counts["low"],
    )
