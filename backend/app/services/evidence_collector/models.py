"""Evidence collection data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class EvidenceType(str, Enum):
    """Types of compliance evidence."""
    CODE_ARTIFACT = "code_artifact"
    CONFIGURATION = "configuration"
    LOG_SAMPLE = "log_sample"
    POLICY_DOCUMENT = "policy_document"
    TEST_RESULT = "test_result"
    AUDIT_LOG = "audit_log"
    SCREENSHOT = "screenshot"
    API_RESPONSE = "api_response"
    COMMIT_HISTORY = "commit_history"
    ACCESS_REVIEW = "access_review"
    ENCRYPTION_PROOF = "encryption_proof"
    VULNERABILITY_SCAN = "vulnerability_scan"
    TRAINING_RECORD = "training_record"
    INCIDENT_REPORT = "incident_report"
    VENDOR_ASSESSMENT = "vendor_assessment"


class EvidenceSource(str, Enum):
    """Sources of evidence collection."""
    GITHUB = "github"
    CODE_SCAN = "code_scan"
    CONFIG_FILE = "config_file"
    CI_CD = "ci_cd"
    CLOUD_PROVIDER = "cloud_provider"
    LOG_AGGREGATOR = "log_aggregator"
    SECURITY_SCANNER = "security_scanner"
    MANUAL_UPLOAD = "manual_upload"
    API_INTEGRATION = "api_integration"
    TRAINING_SYSTEM = "training_system"


class AuditPackageStatus(str, Enum):
    """Status of audit package generation."""
    PENDING = "pending"
    COLLECTING = "collecting"
    VALIDATING = "validating"
    READY = "ready"
    EXPORTED = "exported"
    FAILED = "failed"


@dataclass
class EvidenceItem:
    """Individual evidence item."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    evidence_type: EvidenceType = EvidenceType.CODE_ARTIFACT
    source: EvidenceSource = EvidenceSource.CODE_SCAN
    title: str = ""
    description: str = ""
    content: str = ""
    content_hash: str = ""
    file_path: str | None = None
    file_size: int = 0
    mime_type: str = "text/plain"
    collected_at: datetime = field(default_factory=datetime.utcnow)
    collected_by: str = "system"
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    verification_status: str = "unverified"
    verification_method: str | None = None
    verified_at: datetime | None = None
    verified_by: str | None = None


@dataclass
class ControlMapping:
    """Mapping between regulatory control and evidence requirements."""
    id: UUID = field(default_factory=uuid4)
    framework: str = ""
    control_id: str = ""
    control_name: str = ""
    control_description: str = ""
    required_evidence_types: list[EvidenceType] = field(default_factory=list)
    collection_frequency: str = "quarterly"
    automation_level: str = "full"  # full, partial, manual
    collection_instructions: str = ""
    validation_rules: list[dict] = field(default_factory=list)


@dataclass
class ControlEvidence:
    """Evidence collected for a specific control."""
    id: UUID = field(default_factory=uuid4)
    control_mapping_id: UUID | None = None
    control_id: str = ""
    framework: str = ""
    evidence_items: list[EvidenceItem] = field(default_factory=list)
    coverage_percentage: float = 0.0
    status: str = "incomplete"  # complete, incomplete, partial, expired
    gaps: list[str] = field(default_factory=list)
    last_collected: datetime | None = None
    next_collection_due: datetime | None = None
    reviewer_notes: str = ""


@dataclass
class AuditPackage:
    """Complete audit evidence package."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    name: str = ""
    description: str = ""
    frameworks: list[str] = field(default_factory=list)
    audit_period_start: datetime | None = None
    audit_period_end: datetime | None = None
    status: AuditPackageStatus = AuditPackageStatus.PENDING
    control_evidence: list[ControlEvidence] = field(default_factory=list)
    total_controls: int = 0
    controls_with_evidence: int = 0
    coverage_percentage: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: UUID | None = None
    completed_at: datetime | None = None
    exported_at: datetime | None = None
    export_format: str | None = None
    export_url: str | None = None
    notes: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class CollectionTask:
    """Background task for evidence collection."""
    id: UUID = field(default_factory=uuid4)
    audit_package_id: UUID | None = None
    control_id: str = ""
    evidence_type: EvidenceType = EvidenceType.CODE_ARTIFACT
    source: EvidenceSource = EvidenceSource.CODE_SCAN
    status: str = "pending"  # pending, running, completed, failed
    progress: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    result: dict = field(default_factory=dict)


# Control frameworks and their evidence requirements
CONTROL_FRAMEWORKS: dict[str, list[ControlMapping]] = {
    "SOC2": [
        ControlMapping(
            framework="SOC2",
            control_id="CC1.1",
            control_name="Control Environment",
            control_description="Organization demonstrates commitment to integrity and ethical values",
            required_evidence_types=[EvidenceType.POLICY_DOCUMENT, EvidenceType.TRAINING_RECORD],
            collection_frequency="annually",
            automation_level="partial",
        ),
        ControlMapping(
            framework="SOC2",
            control_id="CC6.1",
            control_name="Logical Access Security",
            control_description="Logical access security software, infrastructure, and architectures are implemented",
            required_evidence_types=[EvidenceType.CONFIGURATION, EvidenceType.ACCESS_REVIEW, EvidenceType.AUDIT_LOG],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="SOC2",
            control_id="CC6.6",
            control_name="Access Controls",
            control_description="Users are authenticated before accessing sensitive data",
            required_evidence_types=[EvidenceType.CODE_ARTIFACT, EvidenceType.CONFIGURATION, EvidenceType.TEST_RESULT],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="SOC2",
            control_id="CC6.7",
            control_name="Encryption",
            control_description="Encryption is implemented to protect data at rest and in transit",
            required_evidence_types=[EvidenceType.ENCRYPTION_PROOF, EvidenceType.CONFIGURATION],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="SOC2",
            control_id="CC7.1",
            control_name="Vulnerability Management",
            control_description="Vulnerabilities are identified, analyzed, and remediated timely",
            required_evidence_types=[EvidenceType.VULNERABILITY_SCAN, EvidenceType.INCIDENT_REPORT],
            collection_frequency="continuous",
            automation_level="full",
        ),
        ControlMapping(
            framework="SOC2",
            control_id="CC8.1",
            control_name="Change Management",
            control_description="Changes are authorized, tested, and approved before implementation",
            required_evidence_types=[EvidenceType.COMMIT_HISTORY, EvidenceType.TEST_RESULT, EvidenceType.AUDIT_LOG],
            collection_frequency="continuous",
            automation_level="full",
        ),
    ],
    "GDPR": [
        ControlMapping(
            framework="GDPR",
            control_id="Art5",
            control_name="Data Processing Principles",
            control_description="Personal data processing adheres to lawfulness, fairness, and transparency",
            required_evidence_types=[EvidenceType.POLICY_DOCUMENT, EvidenceType.CODE_ARTIFACT],
            collection_frequency="annually",
            automation_level="partial",
        ),
        ControlMapping(
            framework="GDPR",
            control_id="Art6",
            control_name="Lawful Basis",
            control_description="Processing has valid legal basis such as consent or contract",
            required_evidence_types=[EvidenceType.CODE_ARTIFACT, EvidenceType.CONFIGURATION, EvidenceType.AUDIT_LOG],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="GDPR",
            control_id="Art17",
            control_name="Right to Erasure",
            control_description="Data subjects can request deletion of their personal data",
            required_evidence_types=[EvidenceType.CODE_ARTIFACT, EvidenceType.API_RESPONSE, EvidenceType.TEST_RESULT],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="GDPR",
            control_id="Art32",
            control_name="Security of Processing",
            control_description="Appropriate technical and organizational measures are implemented",
            required_evidence_types=[EvidenceType.ENCRYPTION_PROOF, EvidenceType.VULNERABILITY_SCAN, EvidenceType.ACCESS_REVIEW],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="GDPR",
            control_id="Art33",
            control_name="Breach Notification",
            control_description="Supervisory authority notified within 72 hours of breach discovery",
            required_evidence_types=[EvidenceType.POLICY_DOCUMENT, EvidenceType.INCIDENT_REPORT],
            collection_frequency="annually",
            automation_level="manual",
        ),
    ],
    "HIPAA": [
        ControlMapping(
            framework="HIPAA",
            control_id="164.312(a)",
            control_name="Access Control",
            control_description="Implement technical policies to limit access to ePHI",
            required_evidence_types=[EvidenceType.CONFIGURATION, EvidenceType.ACCESS_REVIEW, EvidenceType.AUDIT_LOG],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="HIPAA",
            control_id="164.312(b)",
            control_name="Audit Controls",
            control_description="Hardware, software, and procedures to record and examine access",
            required_evidence_types=[EvidenceType.AUDIT_LOG, EvidenceType.LOG_SAMPLE, EvidenceType.CONFIGURATION],
            collection_frequency="continuous",
            automation_level="full",
        ),
        ControlMapping(
            framework="HIPAA",
            control_id="164.312(c)",
            control_name="Integrity Controls",
            control_description="Mechanisms to ensure ePHI is not improperly altered or destroyed",
            required_evidence_types=[EvidenceType.CODE_ARTIFACT, EvidenceType.TEST_RESULT],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="HIPAA",
            control_id="164.312(d)",
            control_name="Person Authentication",
            control_description="Verify person seeking access is the one claimed",
            required_evidence_types=[EvidenceType.CODE_ARTIFACT, EvidenceType.CONFIGURATION, EvidenceType.TEST_RESULT],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="HIPAA",
            control_id="164.312(e)",
            control_name="Transmission Security",
            control_description="Guard against unauthorized access to ePHI in transit",
            required_evidence_types=[EvidenceType.ENCRYPTION_PROOF, EvidenceType.CONFIGURATION],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="HIPAA",
            control_id="164.308(a)(5)",
            control_name="Security Awareness Training",
            control_description="Implement security awareness and training program",
            required_evidence_types=[EvidenceType.TRAINING_RECORD, EvidenceType.POLICY_DOCUMENT],
            collection_frequency="annually",
            automation_level="partial",
        ),
    ],
    "PCI_DSS": [
        ControlMapping(
            framework="PCI_DSS",
            control_id="1.1",
            control_name="Network Segmentation",
            control_description="Install and maintain firewall/router configuration",
            required_evidence_types=[EvidenceType.CONFIGURATION, EvidenceType.SCREENSHOT],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="PCI_DSS",
            control_id="3.4",
            control_name="PAN Protection",
            control_description="Render PAN unreadable anywhere it is stored",
            required_evidence_types=[EvidenceType.ENCRYPTION_PROOF, EvidenceType.CODE_ARTIFACT],
            collection_frequency="quarterly",
            automation_level="full",
        ),
        ControlMapping(
            framework="PCI_DSS",
            control_id="6.5",
            control_name="Secure Development",
            control_description="Address common coding vulnerabilities in software development",
            required_evidence_types=[EvidenceType.VULNERABILITY_SCAN, EvidenceType.TEST_RESULT, EvidenceType.COMMIT_HISTORY],
            collection_frequency="continuous",
            automation_level="full",
        ),
        ControlMapping(
            framework="PCI_DSS",
            control_id="10.1",
            control_name="Audit Trail",
            control_description="Implement audit trails linking all access to cardholder data",
            required_evidence_types=[EvidenceType.AUDIT_LOG, EvidenceType.LOG_SAMPLE],
            collection_frequency="continuous",
            automation_level="full",
        ),
    ],
}
