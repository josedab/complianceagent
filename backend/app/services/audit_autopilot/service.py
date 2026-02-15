"""Audit Preparation Autopilot Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit_autopilot.models import (
    AuditFramework,
    AuditReadinessReport,
    ControlMapping,
    EvidencePackage,
    EvidenceStatus,
    EvidenceTimelineEntry,
    GapAnalysis,
    GapSeverity,
    RemediationStatus,
    RemediationTracker,
)

logger = structlog.get_logger()

# Control mappings per audit framework
_FRAMEWORK_CONTROLS: dict[AuditFramework, list[dict]] = {
    AuditFramework.SOC2_TYPE2: [
        {"id": "CC1.1", "name": "Control Environment", "desc": "Commitment to integrity and ethical values"},
        {"id": "CC2.1", "name": "Information & Communication", "desc": "Internal communication of policies"},
        {"id": "CC3.1", "name": "Risk Assessment", "desc": "Identification of risks to objectives"},
        {"id": "CC4.1", "name": "Monitoring", "desc": "Ongoing monitoring of control effectiveness"},
        {"id": "CC5.1", "name": "Control Activities", "desc": "Selection and development of controls"},
        {"id": "CC6.1", "name": "Logical Access", "desc": "Logical and physical access controls"},
        {"id": "CC6.2", "name": "Access Provisioning", "desc": "User provisioning and deprovisioning"},
        {"id": "CC6.3", "name": "Access Modification", "desc": "Access rights modification procedures"},
        {"id": "CC7.1", "name": "System Operations", "desc": "Detection of anomalies and vulnerabilities"},
        {"id": "CC7.2", "name": "Change Detection", "desc": "Monitoring for unauthorized changes"},
        {"id": "CC8.1", "name": "Change Management", "desc": "Change management processes"},
        {"id": "CC9.1", "name": "Risk Mitigation", "desc": "Risk mitigation activities"},
    ],
    AuditFramework.ISO_27001: [
        {"id": "A.5", "name": "Information Security Policies", "desc": "Management direction for infosec"},
        {"id": "A.6", "name": "Organization of InfoSec", "desc": "Internal organization and mobile devices"},
        {"id": "A.7", "name": "Human Resource Security", "desc": "Prior, during, termination of employment"},
        {"id": "A.8", "name": "Asset Management", "desc": "Responsibility for assets, classification"},
        {"id": "A.9", "name": "Access Control", "desc": "Business requirements, user access management"},
        {"id": "A.10", "name": "Cryptography", "desc": "Cryptographic controls"},
        {"id": "A.12", "name": "Operations Security", "desc": "Operational procedures and responsibilities"},
        {"id": "A.14", "name": "System Development", "desc": "Security requirements in development"},
        {"id": "A.16", "name": "Incident Management", "desc": "Management of information security incidents"},
        {"id": "A.18", "name": "Compliance", "desc": "Compliance with legal requirements"},
    ],
    AuditFramework.HIPAA: [
        {"id": "164.308(a)(1)", "name": "Security Management", "desc": "Risk analysis and management"},
        {"id": "164.308(a)(3)", "name": "Workforce Security", "desc": "Authorization and supervision"},
        {"id": "164.308(a)(4)", "name": "Information Access", "desc": "Access management"},
        {"id": "164.310(a)(1)", "name": "Facility Access", "desc": "Physical safeguards"},
        {"id": "164.310(d)(1)", "name": "Device Controls", "desc": "Device and media controls"},
        {"id": "164.312(a)(1)", "name": "Access Control", "desc": "Technical access controls"},
        {"id": "164.312(b)", "name": "Audit Controls", "desc": "Hardware, software, procedural mechanisms"},
        {"id": "164.312(c)(1)", "name": "Integrity", "desc": "PHI integrity mechanisms"},
        {"id": "164.312(d)", "name": "Authentication", "desc": "Person or entity authentication"},
        {"id": "164.312(e)(1)", "name": "Transmission Security", "desc": "PHI transmission guards"},
    ],
    AuditFramework.PCI_DSS: [
        {"id": "Req 1", "name": "Firewall Configuration", "desc": "Install and maintain firewall"},
        {"id": "Req 2", "name": "Default Passwords", "desc": "Don't use vendor defaults"},
        {"id": "Req 3", "name": "Stored Data", "desc": "Protect stored cardholder data"},
        {"id": "Req 6", "name": "Secure Systems", "desc": "Develop and maintain secure systems"},
        {"id": "Req 7", "name": "Access Restriction", "desc": "Restrict access by business need"},
        {"id": "Req 8", "name": "User Access", "desc": "Identify and authenticate access"},
        {"id": "Req 10", "name": "Monitoring", "desc": "Track and monitor all access"},
        {"id": "Req 11", "name": "Testing", "desc": "Regularly test security systems"},
        {"id": "Req 12", "name": "InfoSec Policy", "desc": "Maintain information security policy"},
    ],
}


class AuditAutopilotService:
    """Automated audit preparation and gap analysis."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._gap_analyses: dict[UUID, GapAnalysis] = {}
        self._reports: dict[UUID, AuditReadinessReport] = {}

    async def run_gap_analysis(self, framework: AuditFramework) -> GapAnalysis:
        """Run gap analysis for an audit framework."""
        controls_def = _FRAMEWORK_CONTROLS.get(framework, [])
        if not controls_def:
            raise ValueError(f"Unsupported framework: {framework.value}")

        mappings = []
        met = partial = missing = 0

        for i, ctrl in enumerate(controls_def):
            # Simulate evidence collection status
            if i % 4 == 0:
                status = EvidenceStatus.COLLECTED
                met += 1
                gap = None
                gap_sev = None
            elif i % 4 == 1:
                status = EvidenceStatus.COLLECTED
                met += 1
                gap = None
                gap_sev = None
            elif i % 4 == 2:
                status = EvidenceStatus.PARTIAL
                partial += 1
                gap = f"Incomplete evidence for {ctrl['name']}"
                gap_sev = GapSeverity.MEDIUM
            else:
                status = EvidenceStatus.MISSING
                missing += 1
                gap = f"No evidence collected for {ctrl['name']}"
                gap_sev = GapSeverity.HIGH

            mappings.append(ControlMapping(
                control_id=ctrl["id"],
                control_name=ctrl["name"],
                description=ctrl["desc"],
                evidence_status=status,
                evidence_items=[f"evidence_{ctrl['id']}"] if status != EvidenceStatus.MISSING else [],
                gap_description=gap,
                gap_severity=gap_sev,
                remediation_task=f"Collect evidence for {ctrl['name']}" if gap else None,
            ))

        total = len(controls_def)
        critical_gaps = [m.gap_description for m in mappings
                         if m.gap_severity in (GapSeverity.CRITICAL, GapSeverity.HIGH) and m.gap_description]

        analysis = GapAnalysis(
            framework=framework,
            total_controls=total,
            controls_met=met,
            controls_partial=partial,
            controls_missing=missing,
            readiness_score=round((met / total) * 100 if total else 0, 1),
            control_mappings=mappings,
            critical_gaps=critical_gaps,
            estimated_remediation_hours=missing * 8.0 + partial * 4.0,
            analyzed_at=datetime.now(UTC),
        )
        self._gap_analyses[analysis.id] = analysis
        logger.info("Gap analysis completed", framework=framework.value, readiness=analysis.readiness_score)
        return analysis

    async def generate_evidence_package(self, framework: AuditFramework) -> EvidencePackage:
        """Generate evidence package for auditor review."""
        analysis = None
        for ga in self._gap_analyses.values():
            if ga.framework == framework:
                analysis = ga
                break

        if not analysis:
            analysis = await self.run_gap_analysis(framework)

        sections = []
        for mapping in analysis.control_mappings:
            if mapping.evidence_status != EvidenceStatus.MISSING:
                sections.append({
                    "control_id": mapping.control_id,
                    "control_name": mapping.control_name,
                    "evidence_items": mapping.evidence_items,
                    "status": mapping.evidence_status.value,
                    "narrative": f"Evidence collected for {mapping.control_name}: {mapping.description}",
                })

        covered = len([s for s in sections if s["status"] == EvidenceStatus.COLLECTED.value])
        package = EvidencePackage(
            framework=framework,
            title=f"{framework.value.upper()} Evidence Package",
            total_items=sum(len(s["evidence_items"]) for s in sections),
            controls_covered=covered,
            total_controls=analysis.total_controls,
            coverage_percent=round((covered / analysis.total_controls) * 100 if analysis.total_controls else 0, 1),
            sections=sections,
            generated_at=datetime.now(UTC),
        )
        return package

    async def generate_readiness_report(self, framework: AuditFramework) -> AuditReadinessReport:
        """Generate complete audit readiness report."""
        analysis = await self.run_gap_analysis(framework)
        package = await self.generate_evidence_package(framework)

        recommendations = []
        if analysis.controls_missing > 0:
            recommendations.append(f"Collect evidence for {analysis.controls_missing} missing controls")
        if analysis.controls_partial > 0:
            recommendations.append(f"Complete partial evidence for {analysis.controls_partial} controls")
        if analysis.readiness_score < 80:
            recommendations.append("Consider engaging external auditor for pre-assessment")
        recommendations.append("Schedule internal audit review meeting")

        prep_weeks = analysis.estimated_remediation_hours / 40.0

        report = AuditReadinessReport(
            framework=framework,
            gap_analysis=analysis,
            evidence_package=package,
            overall_readiness=analysis.readiness_score,
            recommendations=recommendations,
            estimated_prep_weeks=round(prep_weeks, 1),
            generated_at=datetime.now(UTC),
        )
        self._reports[report.id] = report
        logger.info("Readiness report generated", framework=framework.value, readiness=report.overall_readiness)
        return report

    async def list_supported_frameworks(self) -> list[dict]:
        return [
            {"framework": fw.value, "control_count": len(ctrls)}
            for fw, ctrls in _FRAMEWORK_CONTROLS.items()
        ]

    async def get_evidence_timeline(
        self,
        framework: AuditFramework,
        limit: int = 50,
    ) -> list[EvidenceTimelineEntry]:
        """Get evidence collection timeline for a framework."""
        analysis = await self.run_gap_analysis(framework)
        timeline: list[EvidenceTimelineEntry] = []

        for mapping in analysis.control_mappings:
            if mapping.evidence_status == EvidenceStatus.COLLECTED:
                timeline.append(EvidenceTimelineEntry(
                    framework=framework,
                    control_id=mapping.control_id,
                    control_name=mapping.control_name,
                    event_type="collected",
                    description=f"Evidence collected for {mapping.control_name}",
                    evidence_items=mapping.evidence_items,
                    actor="autopilot",
                    timestamp=datetime.now(UTC),
                ))
            elif mapping.evidence_status == EvidenceStatus.PARTIAL:
                timeline.append(EvidenceTimelineEntry(
                    framework=framework,
                    control_id=mapping.control_id,
                    control_name=mapping.control_name,
                    event_type="partial",
                    description=f"Partial evidence for {mapping.control_name} — additional items needed",
                    evidence_items=mapping.evidence_items,
                    actor="autopilot",
                    timestamp=datetime.now(UTC),
                ))
            elif mapping.evidence_status == EvidenceStatus.MISSING:
                timeline.append(EvidenceTimelineEntry(
                    framework=framework,
                    control_id=mapping.control_id,
                    control_name=mapping.control_name,
                    event_type="gap_identified",
                    description=f"No evidence found for {mapping.control_name}",
                    actor="autopilot",
                    timestamp=datetime.now(UTC),
                ))

        return sorted(timeline, key=lambda e: e.timestamp or datetime.min, reverse=True)[:limit]

    async def get_remediation_tasks(
        self,
        framework: AuditFramework,
    ) -> list[RemediationTracker]:
        """Get remediation tasks for control gaps."""
        analysis = await self.run_gap_analysis(framework)
        tasks: list[RemediationTracker] = []

        for mapping in analysis.control_mappings:
            if mapping.evidence_status in (EvidenceStatus.MISSING, EvidenceStatus.PARTIAL):
                severity = mapping.gap_severity or GapSeverity.MEDIUM
                hours = {"critical": 16.0, "high": 12.0, "medium": 8.0, "low": 4.0}

                tasks.append(RemediationTracker(
                    framework=framework,
                    control_id=mapping.control_id,
                    control_name=mapping.control_name,
                    gap_description=mapping.gap_description or f"Evidence gap for {mapping.control_name}",
                    severity=severity,
                    status=RemediationStatus.NOT_STARTED,
                    estimated_hours=hours.get(severity.value, 8.0),
                ))

        return sorted(tasks, key=lambda t: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(t.severity.value, 4))
