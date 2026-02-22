"""Self-Service Audit Workspace service.

Complete audit preparation environment: gap analysis → evidence collection →
remediation tracking → auditor portal.  Guides teams through SOC 2 Type II
or ISO 27001 prep from zero to audit-ready.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession


logger = structlog.get_logger()


class AuditFramework(str, Enum):
    SOC2_TYPE_II = "soc2_type_ii"
    ISO_27001 = "iso_27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"


class GapStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    EVIDENCE_COLLECTED = "evidence_collected"
    REMEDIATED = "remediated"
    VERIFIED = "verified"


class WorkspacePhase(str, Enum):
    GAP_ANALYSIS = "gap_analysis"
    EVIDENCE_COLLECTION = "evidence_collection"
    REMEDIATION = "remediation"
    REVIEW = "review"
    AUDIT_READY = "audit_ready"


@dataclass
class ControlGap:
    control_id: str = ""
    control_name: str = ""
    description: str = ""
    status: GapStatus = GapStatus.NOT_STARTED
    severity: str = "medium"
    evidence_required: list[str] = field(default_factory=list)
    evidence_collected: list[str] = field(default_factory=list)
    remediation_notes: str = ""
    assignee: str = ""


@dataclass
class GapAnalysisResult:
    id: UUID = field(default_factory=uuid4)
    framework: AuditFramework = AuditFramework.SOC2_TYPE_II
    total_controls: int = 0
    gaps_found: int = 0
    fully_met: int = 0
    partially_met: int = 0
    not_met: int = 0
    readiness_pct: float = 0.0
    gaps: list[ControlGap] = field(default_factory=list)
    estimated_remediation_days: float = 0.0
    generated_at: datetime | None = None


@dataclass
class AuditWorkspace:
    id: UUID = field(default_factory=uuid4)
    org_id: str = ""
    framework: AuditFramework = AuditFramework.SOC2_TYPE_II
    phase: WorkspacePhase = WorkspacePhase.GAP_ANALYSIS
    gap_analysis: GapAnalysisResult | None = None
    evidence_coverage_pct: float = 0.0
    remediation_progress_pct: float = 0.0
    created_at: datetime | None = None
    target_audit_date: datetime | None = None


# SOC 2 Type II control framework (13 trust services criteria)
_SOC2_CONTROLS: list[dict[str, Any]] = [
    {
        "id": "CC1.1",
        "name": "COSO Principles",
        "evidence": ["Code of conduct", "Org chart", "Risk assessment"],
    },
    {
        "id": "CC2.1",
        "name": "Internal Communication",
        "evidence": ["Security policies", "Acceptable use policy"],
    },
    {
        "id": "CC3.1",
        "name": "Risk Assessment",
        "evidence": ["Risk register", "Risk treatment plan"],
    },
    {
        "id": "CC4.1",
        "name": "Monitoring Activities",
        "evidence": ["SOC metrics dashboard", "Management review minutes"],
    },
    {
        "id": "CC5.1",
        "name": "Control Activities",
        "evidence": ["Change management policy", "Approval workflows"],
    },
    {
        "id": "CC6.1",
        "name": "Logical Access",
        "evidence": ["Access control policy", "User provisioning logs", "MFA config"],
    },
    {
        "id": "CC6.2",
        "name": "User Lifecycle",
        "evidence": ["Onboarding/offboarding procedures", "Access reviews"],
    },
    {
        "id": "CC6.3",
        "name": "Role-Based Access",
        "evidence": ["RBAC matrix", "Privilege access reviews"],
    },
    {
        "id": "CC6.6",
        "name": "Encryption in Transit",
        "evidence": ["TLS configuration", "Certificate inventory"],
    },
    {
        "id": "CC6.7",
        "name": "Encryption at Rest",
        "evidence": ["Encryption configuration", "Key management policy"],
    },
    {
        "id": "CC7.1",
        "name": "Vulnerability Management",
        "evidence": ["Vulnerability scan reports", "Patching logs"],
    },
    {
        "id": "CC7.2",
        "name": "Security Monitoring",
        "evidence": ["SIEM configuration", "Alert rules", "Incident logs"],
    },
    {
        "id": "CC7.3",
        "name": "Incident Response",
        "evidence": ["IR plan", "IR test results", "Post-mortem reports"],
    },
    {
        "id": "CC8.1",
        "name": "Change Management",
        "evidence": ["PR review requirements", "Deployment logs", "Rollback procedures"],
    },
    {
        "id": "A1.1",
        "name": "System Availability",
        "evidence": ["SLA documentation", "Uptime reports", "Health checks"],
    },
    {
        "id": "A1.2",
        "name": "Disaster Recovery",
        "evidence": ["DR plan", "Backup configuration", "DR test results"],
    },
    {
        "id": "C1.1",
        "name": "Data Confidentiality",
        "evidence": ["Data classification policy", "Encryption evidence"],
    },
    {
        "id": "PI1.1",
        "name": "Processing Integrity",
        "evidence": ["Input validation evidence", "Data quality checks"],
    },
]


class AuditWorkspaceService:
    """Self-service audit preparation workspace."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._workspaces: dict[UUID, AuditWorkspace] = {}

    async def create_workspace(
        self,
        org_id: str,
        framework: AuditFramework,
        target_audit_date: datetime | None = None,
    ) -> AuditWorkspace:
        """Create a new audit preparation workspace."""
        workspace = AuditWorkspace(
            org_id=org_id,
            framework=framework,
            phase=WorkspacePhase.GAP_ANALYSIS,
            created_at=datetime.now(UTC),
            target_audit_date=target_audit_date,
        )
        self._workspaces[workspace.id] = workspace

        logger.info("audit_workspace_created", org_id=org_id, framework=framework.value)
        return workspace

    async def run_gap_analysis(self, workspace_id: UUID) -> GapAnalysisResult:
        """Run automated gap analysis against the framework controls."""
        workspace = self._workspaces.get(workspace_id)
        if not workspace:
            return GapAnalysisResult()

        controls = (
            _SOC2_CONTROLS
            if workspace.framework == AuditFramework.SOC2_TYPE_II
            else _SOC2_CONTROLS[:10]
        )
        gaps: list[ControlGap] = []

        # Simulate gap analysis (in production, checks real infrastructure)
        for i, ctrl in enumerate(controls):
            # Simulate varying compliance levels
            if i < len(controls) * 0.4:
                status = GapStatus.VERIFIED
                severity = "low"
            elif i < len(controls) * 0.7:
                status = GapStatus.IN_PROGRESS
                severity = "medium"
            else:
                status = GapStatus.NOT_STARTED
                severity = "high"

            gaps.append(
                ControlGap(
                    control_id=ctrl["id"],
                    control_name=ctrl["name"],
                    description=f"Gap analysis for {ctrl['name']}",
                    status=status,
                    severity=severity,
                    evidence_required=ctrl["evidence"],
                    evidence_collected=ctrl["evidence"][:1]
                    if status != GapStatus.NOT_STARTED
                    else [],
                )
            )

        fully_met = sum(1 for g in gaps if g.status == GapStatus.VERIFIED)
        partially_met = sum(
            1 for g in gaps if g.status in (GapStatus.IN_PROGRESS, GapStatus.EVIDENCE_COLLECTED)
        )
        not_met = sum(1 for g in gaps if g.status == GapStatus.NOT_STARTED)
        total = len(gaps)
        readiness = round((fully_met / total) * 100, 1) if total > 0 else 0.0

        result = GapAnalysisResult(
            framework=workspace.framework,
            total_controls=total,
            gaps_found=partially_met + not_met,
            fully_met=fully_met,
            partially_met=partially_met,
            not_met=not_met,
            readiness_pct=readiness,
            gaps=gaps,
            estimated_remediation_days=not_met * 5.0 + partially_met * 2.0,
            generated_at=datetime.now(UTC),
        )

        workspace.gap_analysis = result
        workspace.evidence_coverage_pct = (
            round((fully_met + partially_met * 0.5) / total * 100, 1) if total > 0 else 0.0
        )

        logger.info(
            "gap_analysis_complete",
            framework=workspace.framework.value,
            readiness=readiness,
            gaps=result.gaps_found,
        )
        return result

    async def advance_phase(self, workspace_id: UUID) -> AuditWorkspace | None:
        """Advance the workspace to the next phase."""
        workspace = self._workspaces.get(workspace_id)
        if not workspace:
            return None

        phase_order = [
            WorkspacePhase.GAP_ANALYSIS,
            WorkspacePhase.EVIDENCE_COLLECTION,
            WorkspacePhase.REMEDIATION,
            WorkspacePhase.REVIEW,
            WorkspacePhase.AUDIT_READY,
        ]
        current_idx = phase_order.index(workspace.phase)
        if current_idx < len(phase_order) - 1:
            workspace.phase = phase_order[current_idx + 1]
            logger.info("workspace_phase_advanced", phase=workspace.phase.value)

        return workspace

    async def get_workspace(self, workspace_id: UUID) -> AuditWorkspace | None:
        return self._workspaces.get(workspace_id)

    async def list_workspaces(self, org_id: str) -> list[AuditWorkspace]:
        return [w for w in self._workspaces.values() if w.org_id == org_id]
