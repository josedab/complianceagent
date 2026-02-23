"""Multi-framework control mapping and readiness assessment.

Maps evidence items to controls across SOC 2, ISO 27001, HIPAA, PCI-DSS,
and NIST 800-53 — and generates gap analysis with readiness scores.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

import structlog


logger = structlog.get_logger()


class ControlStatus(str, Enum):
    """Implementation status of a control."""

    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    NOT_APPLICABLE = "not_applicable"


class EvidenceQuality(str, Enum):
    """Quality assessment of evidence for a control."""

    STRONG = "strong"
    ADEQUATE = "adequate"
    WEAK = "weak"
    MISSING = "missing"


@dataclass
class ControlDefinition:
    """A compliance control definition."""

    id: str = ""
    framework: str = ""
    category: str = ""
    title: str = ""
    description: str = ""
    required_evidence: list[str] = field(default_factory=list)


@dataclass
class ControlMapping:
    """Mapping of evidence to a specific control."""

    control_id: str = ""
    framework: str = ""
    status: ControlStatus = ControlStatus.NOT_IMPLEMENTED
    evidence_quality: EvidenceQuality = EvidenceQuality.MISSING
    evidence_ids: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class FrameworkReadiness:
    """Readiness assessment for a single framework."""

    framework: str = ""
    total_controls: int = 0
    implemented: int = 0
    partial: int = 0
    not_implemented: int = 0
    not_applicable: int = 0
    readiness_score: float = 0.0
    grade: str = "F"
    critical_gaps: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ReadinessReport:
    """Comprehensive readiness report across frameworks."""

    id: UUID = field(default_factory=uuid4)
    organization_id: str = ""
    frameworks: list[FrameworkReadiness] = field(default_factory=list)
    overall_readiness: float = 0.0
    overall_grade: str = "F"
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    estimated_prep_hours: float = 0.0


# Built-in control catalogs
_SOC2_CONTROLS: list[ControlDefinition] = [
    ControlDefinition(
        "CC1.1",
        "soc2",
        "Control Environment",
        "Commitment to Integrity",
        "Demonstrates commitment to integrity and ethical values",
        ["Code of conduct", "Ethics policy"],
    ),
    ControlDefinition(
        "CC2.1",
        "soc2",
        "Communication",
        "Internal Communication",
        "Communicates information internally",
        ["Security awareness training records", "Policy acknowledgments"],
    ),
    ControlDefinition(
        "CC3.1",
        "soc2",
        "Risk Assessment",
        "Risk Identification",
        "Identifies and assesses risks",
        ["Risk assessment report", "Risk register"],
    ),
    ControlDefinition(
        "CC5.1",
        "soc2",
        "Control Activities",
        "Logical Access Controls",
        "Selects and develops control activities",
        ["Access control policy", "Access review logs"],
    ),
    ControlDefinition(
        "CC6.1",
        "soc2",
        "Logical Access",
        "Access Management",
        "Implements logical access security",
        ["SSO configuration", "MFA enrollment", "Access logs"],
    ),
    ControlDefinition(
        "CC6.2",
        "soc2",
        "Logical Access",
        "User Provisioning",
        "Prior to issuing system credentials, registers and authorizes",
        ["User provisioning procedures", "Onboarding checklists"],
    ),
    ControlDefinition(
        "CC6.3",
        "soc2",
        "Logical Access",
        "Access Revocation",
        "Removes access when no longer needed",
        ["Offboarding procedures", "Access revocation logs"],
    ),
    ControlDefinition(
        "CC7.1",
        "soc2",
        "System Operations",
        "Infrastructure Monitoring",
        "Detects and monitors security events",
        ["SIEM configuration", "Alert rules", "Incident logs"],
    ),
    ControlDefinition(
        "CC7.2",
        "soc2",
        "System Operations",
        "Anomaly Detection",
        "Monitors for anomalies indicative of threats",
        ["IDS/IPS configuration", "Anomaly detection rules"],
    ),
    ControlDefinition(
        "CC8.1",
        "soc2",
        "Change Management",
        "Change Control",
        "Authorizes, designs, develops changes",
        ["Change management policy", "PR review evidence", "Deploy logs"],
    ),
    ControlDefinition(
        "CC9.1",
        "soc2",
        "Risk Mitigation",
        "Risk Mitigation Activities",
        "Identifies and assesses vendor risks",
        ["Vendor assessment reports", "Third-party audit reports"],
    ),
]

_ISO27001_CONTROLS: list[ControlDefinition] = [
    ControlDefinition(
        "A.5.1",
        "iso27001",
        "Organizational",
        "Policies for InfoSec",
        "Information security policies shall be defined",
        ["Security policy document", "Policy review records"],
    ),
    ControlDefinition(
        "A.6.1",
        "iso27001",
        "Organizational",
        "Internal Organization",
        "Management framework for information security",
        ["RACI matrix", "Security committee meeting minutes"],
    ),
    ControlDefinition(
        "A.8.1",
        "iso27001",
        "Asset Management",
        "Asset Inventory",
        "Assets shall be identified and inventoried",
        ["Asset register", "CMDB export"],
    ),
    ControlDefinition(
        "A.8.2",
        "iso27001",
        "Asset Management",
        "Classification",
        "Information shall be classified",
        ["Data classification policy", "Classification labels"],
    ),
    ControlDefinition(
        "A.9.1",
        "iso27001",
        "Access Control",
        "Access Control Policy",
        "Access control policy shall be established",
        ["Access control policy", "RBAC matrix"],
    ),
    ControlDefinition(
        "A.10.1",
        "iso27001",
        "Cryptography",
        "Encryption Policy",
        "Cryptographic controls shall be documented",
        ["Encryption policy", "Key management procedures", "TLS config"],
    ),
    ControlDefinition(
        "A.12.1",
        "iso27001",
        "Operations Security",
        "Operating Procedures",
        "Operating procedures shall be documented",
        ["Runbooks", "SOPs", "Incident response plan"],
    ),
    ControlDefinition(
        "A.12.4",
        "iso27001",
        "Operations Security",
        "Logging & Monitoring",
        "Event logs shall be recorded and protected",
        ["Logging configuration", "Log retention policy", "SIEM setup"],
    ),
    ControlDefinition(
        "A.14.2",
        "iso27001",
        "System Development",
        "Secure Development",
        "Rules for development of software shall be established",
        ["Secure SDLC policy", "Code review process", "SAST results"],
    ),
    ControlDefinition(
        "A.18.1",
        "iso27001",
        "Compliance",
        "Legal Requirements",
        "Applicable legal requirements shall be identified",
        ["Legal requirements register", "Compliance tracking"],
    ),
]

_HIPAA_CONTROLS: list[ControlDefinition] = [
    ControlDefinition(
        "164.308(a)(1)",
        "hipaa",
        "Administrative",
        "Security Management",
        "Implement policies to prevent, detect, contain security violations",
        ["Security management policy", "Risk analysis"],
    ),
    ControlDefinition(
        "164.308(a)(3)",
        "hipaa",
        "Administrative",
        "Workforce Security",
        "Implement policies for workforce access to ePHI",
        ["Workforce clearance procedures", "Access authorization"],
    ),
    ControlDefinition(
        "164.308(a)(5)",
        "hipaa",
        "Administrative",
        "Security Awareness",
        "Implement security awareness and training program",
        ["Training records", "Phishing test results"],
    ),
    ControlDefinition(
        "164.310(a)",
        "hipaa",
        "Physical",
        "Facility Access Controls",
        "Limit physical access to electronic information systems",
        ["Facility access policy", "Visitor logs"],
    ),
    ControlDefinition(
        "164.310(d)",
        "hipaa",
        "Physical",
        "Device & Media Controls",
        "Govern receipt and removal of hardware and media",
        ["Device inventory", "Media disposal records"],
    ),
    ControlDefinition(
        "164.312(a)",
        "hipaa",
        "Technical",
        "Access Control",
        "Allow access only to authorized persons/software",
        ["Unique user IDs", "Emergency access procedure", "Auto-logoff"],
    ),
    ControlDefinition(
        "164.312(b)",
        "hipaa",
        "Technical",
        "Audit Controls",
        "Record and examine activity in information systems with ePHI",
        ["Audit log configuration", "Log review procedures"],
    ),
    ControlDefinition(
        "164.312(c)",
        "hipaa",
        "Technical",
        "Integrity",
        "Protect ePHI from improper alteration or destruction",
        ["Integrity verification mechanisms", "Hash validation"],
    ),
    ControlDefinition(
        "164.312(e)",
        "hipaa",
        "Technical",
        "Transmission Security",
        "Guard against unauthorized access to ePHI during transmission",
        ["TLS configuration", "Encryption policies"],
    ),
]

_PCI_DSS_CONTROLS: list[ControlDefinition] = [
    ControlDefinition(
        "1.1",
        "pci-dss",
        "Network Security",
        "Firewall Configuration",
        "Install and maintain network security controls",
        ["Firewall rules", "Network diagram"],
    ),
    ControlDefinition(
        "2.1",
        "pci-dss",
        "Secure Defaults",
        "System Hardening",
        "Apply secure configurations to all system components",
        ["Hardening standards", "Configuration baselines"],
    ),
    ControlDefinition(
        "3.4",
        "pci-dss",
        "Data Protection",
        "Render PAN Unreadable",
        "Render PAN unreadable anywhere it is stored",
        ["Encryption/tokenization configuration", "Key management"],
    ),
    ControlDefinition(
        "6.2",
        "pci-dss",
        "Secure Development",
        "Secure Coding",
        "Develop software securely",
        ["Secure coding guidelines", "Code review process", "SAST results"],
    ),
    ControlDefinition(
        "8.3",
        "pci-dss",
        "Authentication",
        "MFA",
        "Secure all individual non-console administrative access with MFA",
        ["MFA configuration", "Authentication logs"],
    ),
    ControlDefinition(
        "10.1",
        "pci-dss",
        "Logging",
        "Audit Trails",
        "Log and monitor all access to system components and cardholder data",
        ["Audit log configuration", "Log retention policy"],
    ),
    ControlDefinition(
        "11.3",
        "pci-dss",
        "Testing",
        "Penetration Testing",
        "Test security of systems and networks regularly",
        ["Penetration test reports", "Remediation evidence"],
    ),
    ControlDefinition(
        "12.1",
        "pci-dss",
        "Policy",
        "Security Policy",
        "Maintain an information security policy",
        ["Security policy document", "Annual review records"],
    ),
]


CONTROL_CATALOGS: dict[str, list[ControlDefinition]] = {
    "soc2": _SOC2_CONTROLS,
    "iso27001": _ISO27001_CONTROLS,
    "hipaa": _HIPAA_CONTROLS,
    "pci-dss": _PCI_DSS_CONTROLS,
}


class ControlMappingEngine:
    """Maps evidence to compliance controls and generates readiness reports."""

    def __init__(self):
        self._mappings: dict[str, list[ControlMapping]] = {}

    def assess_framework(
        self,
        framework: str,
        available_evidence: list[str] | None = None,
    ) -> FrameworkReadiness:
        """Assess readiness for a specific framework."""
        controls = CONTROL_CATALOGS.get(framework.lower(), [])
        if not controls:
            return FrameworkReadiness(framework=framework)

        evidence_set = {e.lower() for e in (available_evidence or [])}
        mappings: list[ControlMapping] = []

        for ctrl in controls:
            required = {e.lower() for e in ctrl.required_evidence}
            matched = required & evidence_set
            coverage = len(matched) / len(required) if required else 0

            if coverage >= 0.8:
                status = ControlStatus.IMPLEMENTED
                quality = EvidenceQuality.STRONG if coverage == 1.0 else EvidenceQuality.ADEQUATE
            elif coverage >= 0.4:
                status = ControlStatus.PARTIAL
                quality = EvidenceQuality.WEAK
            else:
                status = ControlStatus.NOT_IMPLEMENTED
                quality = EvidenceQuality.MISSING

            gaps = [e for e in ctrl.required_evidence if e.lower() not in evidence_set]
            mappings.append(
                ControlMapping(
                    control_id=ctrl.id,
                    framework=framework,
                    status=status,
                    evidence_quality=quality,
                    evidence_ids=list(matched),
                    gaps=gaps,
                )
            )

        self._mappings[framework] = mappings

        implemented = sum(1 for m in mappings if m.status == ControlStatus.IMPLEMENTED)
        partial = sum(1 for m in mappings if m.status == ControlStatus.PARTIAL)
        not_impl = sum(1 for m in mappings if m.status == ControlStatus.NOT_IMPLEMENTED)
        total = len(mappings)

        score = (implemented + partial * 0.5) / max(total, 1) * 100
        grade = _score_to_grade(score)

        critical_gaps = [
            f"{m.control_id}: {', '.join(m.gaps)}"
            for m in mappings
            if m.status == ControlStatus.NOT_IMPLEMENTED and m.gaps
        ][:5]

        recommendations = []
        if not_impl > 0:
            recommendations.append(f"Implement {not_impl} missing controls before audit")
        if partial > 0:
            recommendations.append(f"Complete evidence for {partial} partially-covered controls")
        if score < 80:
            recommendations.append("Score below 80% — not audit-ready")

        readiness = FrameworkReadiness(
            framework=framework,
            total_controls=total,
            implemented=implemented,
            partial=partial,
            not_implemented=not_impl,
            readiness_score=round(score, 1),
            grade=grade,
            critical_gaps=critical_gaps,
            recommendations=recommendations,
        )

        logger.info(
            "Framework assessed",
            framework=framework,
            score=round(score, 1),
            grade=grade,
            implemented=implemented,
            gaps=not_impl,
        )
        return readiness

    def generate_readiness_report(
        self,
        organization_id: str,
        frameworks: list[str] | None = None,
        available_evidence: list[str] | None = None,
    ) -> ReadinessReport:
        """Generate a comprehensive readiness report across frameworks."""
        target_frameworks = frameworks or list(CONTROL_CATALOGS.keys())
        framework_results = []

        for fw in target_frameworks:
            result = self.assess_framework(fw, available_evidence)
            framework_results.append(result)

        overall = sum(f.readiness_score for f in framework_results) / max(len(framework_results), 1)

        total_gaps = sum(f.not_implemented for f in framework_results)
        estimated_hours = total_gaps * 8.0  # ~8 hours per missing control

        report = ReadinessReport(
            organization_id=organization_id,
            frameworks=framework_results,
            overall_readiness=round(overall, 1),
            overall_grade=_score_to_grade(overall),
            estimated_prep_hours=estimated_hours,
        )

        logger.info(
            "Readiness report generated",
            org=organization_id,
            frameworks=len(framework_results),
            overall=round(overall, 1),
        )
        return report

    def get_control_mappings(self, framework: str) -> list[ControlMapping]:
        """Get control mappings for a framework."""
        return self._mappings.get(framework, [])


def _score_to_grade(score: float) -> str:
    if score >= 95:
        return "A+"
    if score >= 90:
        return "A"
    if score >= 85:
        return "B+"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"
