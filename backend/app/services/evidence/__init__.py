"""Automated compliance evidence collection and multi-framework support."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog

# Import new extended functionality
from app.services.evidence.models import (
    CollectionConfig,
    Control,
    ControlMapping as ExtendedControlMapping,
    EvidenceCollection,
    EvidenceItem,
    EvidenceReport,
    EvidenceStatus as ExtendedEvidenceStatus,
    EvidenceType as ExtendedEvidenceType,
    Framework,
)
from app.services.evidence.collector import (
    EvidenceCollector as ExtendedEvidenceCollector,
    get_evidence_collector as get_extended_collector,
)
from app.services.evidence.mapping import ControlMapper, get_control_mapper
from app.services.evidence.report import ReportGenerator, get_report_generator


logger = structlog.get_logger()


# Re-export extended functionality
__all__ = [
    # Legacy exports
    "ControlFramework",
    "EvidenceType",
    "EvidenceStatus",
    "ControlMapping",
    "Evidence",
    "EvidenceCollector",
    "get_evidence_collector",
    "CONTROL_MAPPINGS",
    # Extended exports
    "Framework",
    "ExtendedEvidenceType",
    "ExtendedEvidenceStatus",
    "ExtendedControlMapping",
    "Control",
    "CollectionConfig",
    "EvidenceItem",
    "EvidenceCollection",
    "EvidenceReport",
    "ExtendedEvidenceCollector",
    "get_extended_collector",
    "ControlMapper",
    "get_control_mapper",
    "ReportGenerator",
    "get_report_generator",
]


class ControlFramework(str, Enum):
    """Supported control frameworks."""

    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    NIST_CSF = "nist_csf"


class EvidenceType(str, Enum):
    """Types of compliance evidence."""

    POLICY = "policy"
    PROCEDURE = "procedure"
    SCREENSHOT = "screenshot"
    LOG = "log"
    CONFIGURATION = "configuration"
    REPORT = "report"
    CERTIFICATE = "certificate"
    ATTESTATION = "attestation"
    TEST_RESULT = "test_result"
    CODE_REVIEW = "code_review"


class EvidenceStatus(str, Enum):
    """Status of evidence."""

    DRAFT = "draft"
    COLLECTED = "collected"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    EXPIRED = "expired"


@dataclass
class ControlMapping:
    """Mapping of a control to frameworks."""

    control_id: str
    control_name: str
    description: str
    frameworks: dict[ControlFramework, str]  # Framework -> Control ID in that framework
    evidence_types: list[EvidenceType]
    collection_frequency: str  # daily, weekly, monthly, quarterly, annual
    automated: bool = False


@dataclass
class Evidence:
    """A piece of compliance evidence."""

    id: UUID = field(default_factory=uuid4)
    control_id: str = ""
    evidence_type: EvidenceType = EvidenceType.CONFIGURATION
    title: str = ""
    description: str = ""
    content: str | bytes = ""
    content_type: str = "text/plain"
    file_path: str | None = None
    source: str = ""  # Where the evidence came from
    collected_at: datetime = field(default_factory=datetime.utcnow)
    collected_by: str = ""
    valid_from: datetime = field(default_factory=datetime.utcnow)
    valid_until: datetime | None = None
    status: EvidenceStatus = EvidenceStatus.COLLECTED
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Control mappings across frameworks
CONTROL_MAPPINGS: list[ControlMapping] = [
    ControlMapping(
        control_id="AC-001",
        control_name="Access Control Policy",
        description="Organization has documented access control policies",
        frameworks={
            ControlFramework.SOC2: "CC6.1",
            ControlFramework.ISO27001: "A.9.1.1",
            ControlFramework.HIPAA: "164.312(a)(1)",
            ControlFramework.PCI_DSS: "7.1",
            ControlFramework.NIST_CSF: "PR.AC-1",
        },
        evidence_types=[EvidenceType.POLICY, EvidenceType.PROCEDURE],
        collection_frequency="annual",
    ),
    ControlMapping(
        control_id="AC-002",
        control_name="User Authentication",
        description="Systems require user authentication",
        frameworks={
            ControlFramework.SOC2: "CC6.1",
            ControlFramework.ISO27001: "A.9.4.2",
            ControlFramework.HIPAA: "164.312(d)",
            ControlFramework.PCI_DSS: "8.2",
            ControlFramework.NIST_CSF: "PR.AC-7",
        },
        evidence_types=[EvidenceType.CONFIGURATION, EvidenceType.SCREENSHOT],
        collection_frequency="quarterly",
        automated=True,
    ),
    ControlMapping(
        control_id="AC-003",
        control_name="MFA Enforcement",
        description="Multi-factor authentication is required for privileged access",
        frameworks={
            ControlFramework.SOC2: "CC6.1",
            ControlFramework.ISO27001: "A.9.4.2",
            ControlFramework.PCI_DSS: "8.3",
            ControlFramework.NIST_CSF: "PR.AC-7",
        },
        evidence_types=[EvidenceType.CONFIGURATION, EvidenceType.LOG],
        collection_frequency="monthly",
        automated=True,
    ),
    ControlMapping(
        control_id="ENC-001",
        control_name="Encryption at Rest",
        description="Sensitive data is encrypted at rest",
        frameworks={
            ControlFramework.SOC2: "CC6.7",
            ControlFramework.ISO27001: "A.10.1.1",
            ControlFramework.HIPAA: "164.312(a)(2)(iv)",
            ControlFramework.PCI_DSS: "3.4",
            ControlFramework.GDPR: "Art. 32",
        },
        evidence_types=[EvidenceType.CONFIGURATION, EvidenceType.SCREENSHOT],
        collection_frequency="quarterly",
        automated=True,
    ),
    ControlMapping(
        control_id="ENC-002",
        control_name="Encryption in Transit",
        description="Data is encrypted during transmission",
        frameworks={
            ControlFramework.SOC2: "CC6.7",
            ControlFramework.ISO27001: "A.13.2.3",
            ControlFramework.HIPAA: "164.312(e)(1)",
            ControlFramework.PCI_DSS: "4.1",
            ControlFramework.GDPR: "Art. 32",
        },
        evidence_types=[EvidenceType.CONFIGURATION, EvidenceType.TEST_RESULT],
        collection_frequency="quarterly",
        automated=True,
    ),
    ControlMapping(
        control_id="LOG-001",
        control_name="Audit Logging",
        description="Security events are logged and retained",
        frameworks={
            ControlFramework.SOC2: "CC7.2",
            ControlFramework.ISO27001: "A.12.4.1",
            ControlFramework.HIPAA: "164.312(b)",
            ControlFramework.PCI_DSS: "10.2",
            ControlFramework.NIST_CSF: "DE.CM-1",
        },
        evidence_types=[EvidenceType.LOG, EvidenceType.CONFIGURATION],
        collection_frequency="monthly",
        automated=True,
    ),
    ControlMapping(
        control_id="BCP-001",
        control_name="Backup Procedures",
        description="Regular backups are performed and tested",
        frameworks={
            ControlFramework.SOC2: "CC9.1",
            ControlFramework.ISO27001: "A.12.3.1",
            ControlFramework.HIPAA: "164.308(a)(7)(ii)(A)",
            ControlFramework.NIST_CSF: "PR.IP-4",
        },
        evidence_types=[EvidenceType.LOG, EvidenceType.TEST_RESULT],
        collection_frequency="monthly",
        automated=True,
    ),
    ControlMapping(
        control_id="CHG-001",
        control_name="Change Management",
        description="Changes follow documented procedures",
        frameworks={
            ControlFramework.SOC2: "CC8.1",
            ControlFramework.ISO27001: "A.12.1.2",
            ControlFramework.PCI_DSS: "6.4",
            ControlFramework.NIST_CSF: "PR.IP-3",
        },
        evidence_types=[EvidenceType.PROCEDURE, EvidenceType.LOG, EvidenceType.CODE_REVIEW],
        collection_frequency="monthly",
    ),
    ControlMapping(
        control_id="VUL-001",
        control_name="Vulnerability Management",
        description="Systems are scanned for vulnerabilities",
        frameworks={
            ControlFramework.SOC2: "CC7.1",
            ControlFramework.ISO27001: "A.12.6.1",
            ControlFramework.PCI_DSS: "11.2",
            ControlFramework.NIST_CSF: "ID.RA-1",
        },
        evidence_types=[EvidenceType.REPORT, EvidenceType.LOG],
        collection_frequency="quarterly",
        automated=True,
    ),
    ControlMapping(
        control_id="INC-001",
        control_name="Incident Response",
        description="Security incidents are detected and responded to",
        frameworks={
            ControlFramework.SOC2: "CC7.3",
            ControlFramework.ISO27001: "A.16.1.1",
            ControlFramework.HIPAA: "164.308(a)(6)",
            ControlFramework.PCI_DSS: "12.10",
            ControlFramework.NIST_CSF: "RS.RP-1",
        },
        evidence_types=[EvidenceType.PROCEDURE, EvidenceType.LOG, EvidenceType.REPORT],
        collection_frequency="annual",
    ),
]


class EvidenceCollector:
    """Automated evidence collector for compliance frameworks."""

    def __init__(self):
        self._control_mappings = {m.control_id: m for m in CONTROL_MAPPINGS}
        self._evidence_store: dict[UUID, Evidence] = {}

    def get_controls_for_framework(
        self,
        framework: ControlFramework,
    ) -> list[ControlMapping]:
        """Get all controls mapped to a framework."""
        return [
            m for m in CONTROL_MAPPINGS
            if framework in m.frameworks
        ]

    def get_control_mapping(self, control_id: str) -> ControlMapping | None:
        """Get control mapping by ID."""
        return self._control_mappings.get(control_id)

    async def collect_evidence(
        self,
        control_id: str,
        evidence_type: EvidenceType,
        content: str | bytes,
        title: str,
        source: str,
        collected_by: str,
        content_type: str = "text/plain",
        metadata: dict[str, Any] | None = None,
    ) -> Evidence:
        """Collect and store evidence for a control."""
        evidence = Evidence(
            control_id=control_id,
            evidence_type=evidence_type,
            title=title,
            content=content,
            content_type=content_type,
            source=source,
            collected_by=collected_by,
            metadata=metadata or {},
        )

        self._evidence_store[evidence.id] = evidence
        return evidence

    async def collect_automated_evidence(
        self,
        control_id: str,
        organization_id: str,
    ) -> list[Evidence]:
        """Collect automated evidence for a control."""
        mapping = self._control_mappings.get(control_id)
        if not mapping or not mapping.automated:
            return []

        collected = []

        # Simulate automated evidence collection based on control type
        if control_id == "AC-002":
            # User authentication configuration
            evidence = await self.collect_evidence(
                control_id=control_id,
                evidence_type=EvidenceType.CONFIGURATION,
                content="Authentication Configuration:\n- Password policy: 12+ chars, complexity\n- Session timeout: 15 minutes\n- Account lockout: 5 attempts",
                title="Authentication System Configuration",
                source="identity_provider",
                collected_by="system",
            )
            collected.append(evidence)

        elif control_id == "AC-003":
            # MFA configuration
            evidence = await self.collect_evidence(
                control_id=control_id,
                evidence_type=EvidenceType.CONFIGURATION,
                content="MFA Configuration:\n- Enforced for all admin users\n- Methods: TOTP, WebAuthn\n- Backup codes enabled",
                title="MFA Enforcement Configuration",
                source="identity_provider",
                collected_by="system",
            )
            collected.append(evidence)

        elif control_id in ("ENC-001", "ENC-002"):
            # Encryption configuration
            evidence = await self.collect_evidence(
                control_id=control_id,
                evidence_type=EvidenceType.CONFIGURATION,
                content="Encryption Configuration:\n- Algorithm: AES-256-GCM\n- Key rotation: 90 days\n- TLS 1.3 enforced",
                title="Encryption Configuration",
                source="infrastructure",
                collected_by="system",
            )
            collected.append(evidence)

        elif control_id == "LOG-001":
            # Audit log sample
            evidence = await self.collect_evidence(
                control_id=control_id,
                evidence_type=EvidenceType.LOG,
                content="Sample audit log entries from the past 30 days...",
                title="Audit Log Sample",
                source="logging_system",
                collected_by="system",
            )
            collected.append(evidence)

        return collected

    async def review_evidence(
        self,
        evidence_id: UUID,
        reviewer: str,
        approved: bool,
        notes: str | None = None,
    ) -> Evidence:
        """Review and approve/reject evidence."""
        evidence = self._evidence_store.get(evidence_id)
        if not evidence:
            raise ValueError(f"Evidence {evidence_id} not found")

        evidence.reviewed_by = reviewer
        evidence.reviewed_at = datetime.utcnow()
        evidence.status = EvidenceStatus.APPROVED if approved else EvidenceStatus.DRAFT

        if notes:
            evidence.metadata["review_notes"] = notes

        return evidence

    def get_evidence_for_control(
        self,
        control_id: str,
        status: EvidenceStatus | None = None,
    ) -> list[Evidence]:
        """Get all evidence for a control."""
        evidence = [
            e for e in self._evidence_store.values()
            if e.control_id == control_id
        ]
        if status:
            evidence = [e for e in evidence if e.status == status]
        return sorted(evidence, key=lambda e: e.collected_at, reverse=True)

    def export_for_audit(
        self,
        framework: ControlFramework,
        format: str = "json",
    ) -> dict[str, Any]:
        """Export evidence package for external audit."""
        controls = self.get_controls_for_framework(framework)

        export = {
            "framework": framework.value,
            "exported_at": datetime.utcnow().isoformat(),
            "controls": [],
        }

        for mapping in controls:
            control_evidence = self.get_evidence_for_control(
                mapping.control_id,
                status=EvidenceStatus.APPROVED,
            )

            export["controls"].append({
                "control_id": mapping.control_id,
                "control_name": mapping.control_name,
                "framework_control": mapping.frameworks.get(framework),
                "description": mapping.description,
                "evidence_count": len(control_evidence),
                "evidence": [
                    {
                        "id": str(e.id),
                        "type": e.evidence_type.value,
                        "title": e.title,
                        "collected_at": e.collected_at.isoformat(),
                        "status": e.status.value,
                        "source": e.source,
                    }
                    for e in control_evidence
                ],
            })

        return export

    def get_compliance_coverage(
        self,
        framework: ControlFramework,
    ) -> dict[str, Any]:
        """Get compliance coverage statistics for a framework."""
        controls = self.get_controls_for_framework(framework)
        total = len(controls)
        covered = 0
        partial = 0
        missing = 0

        for mapping in controls:
            evidence = self.get_evidence_for_control(
                mapping.control_id,
                status=EvidenceStatus.APPROVED,
            )
            if evidence:
                covered += 1
            elif self.get_evidence_for_control(mapping.control_id):
                partial += 1
            else:
                missing += 1

        return {
            "framework": framework.value,
            "total_controls": total,
            "covered": covered,
            "partial": partial,
            "missing": missing,
            "coverage_percentage": round(covered / total * 100, 1) if total else 0,
        }


# Global collector instance
_collector: EvidenceCollector | None = None


def get_evidence_collector() -> EvidenceCollector:
    """Get or create the global evidence collector."""
    global _collector
    if _collector is None:
        _collector = EvidenceCollector()
    return _collector
