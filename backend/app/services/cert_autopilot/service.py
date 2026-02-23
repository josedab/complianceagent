"""Compliance Certification Autopilot Service."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cert_autopilot.models import (
    CertificationFramework,
    CertificationJourney,
    CertificationPhase,
    ControlGap,
)


logger = structlog.get_logger()

_SOC2_CONTROLS = [
    ControlGap(
        control_id="CC1.1",
        control_name="Control Environment",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Org chart", "Code of conduct"],
        remediation_steps=["Document control environment policies"],
        estimated_hours=8.0,
    ),
    ControlGap(
        control_id="CC2.1",
        control_name="Information and Communication",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Communication policies", "Incident response plan"],
        remediation_steps=["Establish communication channels"],
        estimated_hours=6.0,
    ),
    ControlGap(
        control_id="CC3.1",
        control_name="Risk Assessment",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Risk register", "Risk assessment report"],
        remediation_steps=["Conduct annual risk assessment"],
        estimated_hours=16.0,
    ),
    ControlGap(
        control_id="CC4.1",
        control_name="Monitoring Activities",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Monitoring dashboards", "Alert configurations"],
        remediation_steps=["Implement continuous monitoring"],
        estimated_hours=20.0,
    ),
    ControlGap(
        control_id="CC5.1",
        control_name="Control Activities",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Access control matrix", "Change management log"],
        remediation_steps=["Review and document control activities"],
        estimated_hours=12.0,
    ),
    ControlGap(
        control_id="CC6.1",
        control_name="Logical and Physical Access",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Access reviews", "MFA configuration"],
        remediation_steps=["Enforce MFA for all systems", "Quarterly access reviews"],
        estimated_hours=24.0,
    ),
    ControlGap(
        control_id="CC7.1",
        control_name="System Operations",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Incident logs", "Runbooks"],
        remediation_steps=["Document operational procedures"],
        estimated_hours=10.0,
    ),
    ControlGap(
        control_id="CC8.1",
        control_name="Change Management",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Change request logs", "Approval workflows"],
        remediation_steps=["Implement change advisory board process"],
        estimated_hours=14.0,
    ),
    ControlGap(
        control_id="CC9.1",
        control_name="Risk Mitigation",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Vendor assessments", "Insurance policies"],
        remediation_steps=["Complete vendor risk assessments"],
        estimated_hours=18.0,
    ),
    ControlGap(
        control_id="A1.1",
        control_name="Availability",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["SLA documentation", "Uptime reports"],
        remediation_steps=["Define and monitor SLAs"],
        estimated_hours=8.0,
    ),
    ControlGap(
        control_id="C1.1",
        control_name="Confidentiality",
        framework=CertificationFramework.SOC2_TYPE2,
        evidence_needed=["Encryption policies", "Data classification"],
        remediation_steps=["Encrypt data at rest and in transit"],
        estimated_hours=16.0,
    ),
]

_ISO27001_CONTROLS = [
    ControlGap(
        control_id="A.5",
        control_name="Information Security Policies",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["ISMS policy document"],
        remediation_steps=["Draft and approve ISMS policy"],
        estimated_hours=12.0,
    ),
    ControlGap(
        control_id="A.6",
        control_name="Organization of Information Security",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Roles and responsibilities matrix"],
        remediation_steps=["Define security roles"],
        estimated_hours=8.0,
    ),
    ControlGap(
        control_id="A.7",
        control_name="Human Resource Security",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Background check policy", "Security training records"],
        remediation_steps=["Implement security awareness training"],
        estimated_hours=10.0,
    ),
    ControlGap(
        control_id="A.8",
        control_name="Asset Management",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Asset inventory", "Data classification policy"],
        remediation_steps=["Create and maintain asset register"],
        estimated_hours=14.0,
    ),
    ControlGap(
        control_id="A.9",
        control_name="Access Control",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Access control policy", "User access reviews"],
        remediation_steps=["Implement least privilege access"],
        estimated_hours=20.0,
    ),
    ControlGap(
        control_id="A.10",
        control_name="Cryptography",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Encryption standards document", "Key management procedure"],
        remediation_steps=["Define cryptographic controls"],
        estimated_hours=12.0,
    ),
    ControlGap(
        control_id="A.12",
        control_name="Operations Security",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Change management procedures", "Capacity plans"],
        remediation_steps=["Document operational procedures"],
        estimated_hours=16.0,
    ),
    ControlGap(
        control_id="A.13",
        control_name="Communications Security",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Network security policy", "Firewall rules"],
        remediation_steps=["Implement network segmentation"],
        estimated_hours=18.0,
    ),
    ControlGap(
        control_id="A.16",
        control_name="Incident Management",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Incident response plan", "Incident log"],
        remediation_steps=["Establish incident response team"],
        estimated_hours=14.0,
    ),
    ControlGap(
        control_id="A.18",
        control_name="Compliance",
        framework=CertificationFramework.ISO27001,
        evidence_needed=["Legal requirements register", "Audit reports"],
        remediation_steps=["Identify applicable legal requirements"],
        estimated_hours=10.0,
    ),
]

_CONTROL_REGISTRY: dict[CertificationFramework, list[ControlGap]] = {
    CertificationFramework.SOC2_TYPE2: _SOC2_CONTROLS,
    CertificationFramework.ISO27001: _ISO27001_CONTROLS,
}

_PHASE_ORDER = list(CertificationPhase)


class CertificationAutopilotService:
    """Service for managing compliance certification journeys."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._journeys: list[CertificationJourney] = []
        self._gaps: dict[str, list[ControlGap]] = {}

    async def start_journey(
        self,
        framework: CertificationFramework,
        organization_id: str,
    ) -> CertificationJourney:
        """Start a new certification journey."""
        controls = _CONTROL_REGISTRY.get(framework, [])
        journey = CertificationJourney(
            framework=framework,
            organization_id=organization_id,
            current_phase=CertificationPhase.GAP_ANALYSIS,
            controls_total=len(controls),
            controls_met=0,
            evidence_collected=0,
            readiness_score=0.0,
            estimated_completion=datetime.now(UTC) + timedelta(days=180),
        )
        self._journeys.append(journey)
        logger.info(
            "Certification journey started",
            framework=framework.value,
            organization_id=organization_id,
        )
        return journey

    async def get_journey(self, journey_id: UUID) -> CertificationJourney | None:
        """Get a certification journey by ID."""
        return next((j for j in self._journeys if j.id == journey_id), None)

    async def list_journeys(self, organization_id: str | None = None) -> list[CertificationJourney]:
        """List all certification journeys."""
        results = list(self._journeys)
        if organization_id:
            results = [j for j in results if j.organization_id == organization_id]
        return results

    async def run_gap_analysis(self, journey_id: UUID) -> list[ControlGap]:
        """Run a gap analysis for a certification journey."""
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return []

        controls = _CONTROL_REGISTRY.get(journey.framework, [])
        # Deterministic: first third are met, rest are gaps
        gaps: list[ControlGap] = []
        met_count = len(controls) // 3
        for i, control in enumerate(controls):
            gap = ControlGap(
                control_id=control.control_id,
                control_name=control.control_name,
                framework=control.framework,
                status="met" if i < met_count else "not_met",
                evidence_needed=control.evidence_needed,
                remediation_steps=control.remediation_steps,
                estimated_hours=control.estimated_hours,
            )
            gaps.append(gap)

        journey.controls_met = met_count
        journey.readiness_score = round((met_count / len(controls)) * 100, 1) if controls else 0.0
        self._gaps[str(journey_id)] = gaps

        logger.info(
            "Gap analysis complete", journey_id=str(journey_id), gaps=len(controls) - met_count
        )
        return gaps

    async def collect_evidence(self, journey_id: UUID, control_id: str, evidence: str) -> bool:
        """Record evidence collection for a control."""
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return False

        gaps = self._gaps.get(str(journey_id), [])
        gap = next((g for g in gaps if g.control_id == control_id), None)
        if gap and gap.status == "not_met":
            gap.status = "evidence_collected"
            journey.evidence_collected += 1
            logger.info("Evidence collected", journey_id=str(journey_id), control_id=control_id)
            return True
        return False

    async def advance_phase(self, journey_id: UUID) -> CertificationJourney | None:
        """Advance a journey to the next phase."""
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return None

        current_idx = _PHASE_ORDER.index(journey.current_phase)
        if current_idx < len(_PHASE_ORDER) - 1:
            journey.phases_completed.append(journey.current_phase.value)
            journey.current_phase = _PHASE_ORDER[current_idx + 1]
            # Update readiness score based on phase progress
            journey.readiness_score = round(((current_idx + 1) / len(_PHASE_ORDER)) * 100, 1)
            logger.info(
                "Phase advanced", journey_id=str(journey_id), new_phase=journey.current_phase.value
            )
        return journey

    async def get_readiness_dashboard(self, journey_id: UUID) -> dict:
        """Get a readiness dashboard for a certification journey."""
        journey = next((j for j in self._journeys if j.id == journey_id), None)
        if not journey:
            return {}

        gaps = self._gaps.get(str(journey_id), [])
        met = sum(1 for g in gaps if g.status == "met")
        evidence = sum(1 for g in gaps if g.status == "evidence_collected")
        not_met = sum(1 for g in gaps if g.status == "not_met")
        total_hours = sum(g.estimated_hours for g in gaps if g.status == "not_met")

        return {
            "journey_id": str(journey_id),
            "framework": journey.framework.value,
            "current_phase": journey.current_phase.value,
            "readiness_score": journey.readiness_score,
            "controls_total": journey.controls_total,
            "controls_met": met,
            "controls_evidence_collected": evidence,
            "controls_not_met": not_met,
            "remaining_hours": round(total_hours, 1),
            "estimated_completion": journey.estimated_completion.isoformat()
            if journey.estimated_completion
            else None,
        }
