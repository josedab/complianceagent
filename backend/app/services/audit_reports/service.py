"""Audit Report Generation service."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import structlog

from app.services.audit_reports.models import (
    AuditFramework,
    AuditorComment,
    AuditorPortalSession,
    AuditorRole,
    AuditReport,
    ControlGap,
    ControlResult,
    ControlStatus,
    EvidenceItem,
    EvidenceSummary,
    EvidenceType,
    FrameworkDefinition,
    ReportFormat,
)


logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

_reports: dict[UUID, AuditReport] = {}
_auditor_sessions: dict[UUID, AuditorPortalSession] = {}
_auditor_comments: list[AuditorComment] = []

# ---------------------------------------------------------------------------
# Framework control definitions
# ---------------------------------------------------------------------------

_SOC2_CONTROLS: list[dict] = [
    {"id": "CC1.1", "name": "COSO Principle 1 – Integrity and Ethics", "description": "The entity demonstrates commitment to integrity and ethical values.", "category": "Control Environment"},
    {"id": "CC1.2", "name": "COSO Principle 2 – Board Oversight", "description": "The board demonstrates independence from management and exercises oversight.", "category": "Control Environment"},
    {"id": "CC1.3", "name": "COSO Principle 3 – Management Structure", "description": "Management establishes structures, reporting lines, and appropriate authorities.", "category": "Control Environment"},
    {"id": "CC1.4", "name": "COSO Principle 4 – Competence Commitment", "description": "The entity demonstrates commitment to attract, develop, and retain competent individuals.", "category": "Control Environment"},
    {"id": "CC1.5", "name": "COSO Principle 5 – Accountability", "description": "The entity holds individuals accountable for internal control responsibilities.", "category": "Control Environment"},
    {"id": "CC2.1", "name": "Information for Internal Control", "description": "The entity obtains or generates relevant, quality information to support internal control.", "category": "Communication and Information"},
    {"id": "CC2.2", "name": "Internal Communication", "description": "The entity internally communicates information necessary to support internal control.", "category": "Communication and Information"},
    {"id": "CC2.3", "name": "External Communication", "description": "The entity communicates with external parties regarding internal control matters.", "category": "Communication and Information"},
    {"id": "CC3.1", "name": "Risk Identification", "description": "The entity specifies objectives to identify and assess risks.", "category": "Risk Assessment"},
    {"id": "CC3.2", "name": "Risk Analysis", "description": "The entity identifies and analyses risks to the achievement of objectives.", "category": "Risk Assessment"},
    {"id": "CC3.3", "name": "Fraud Risk", "description": "The entity considers the potential for fraud in assessing risks.", "category": "Risk Assessment"},
    {"id": "CC3.4", "name": "Change Management", "description": "The entity identifies and assesses changes that could significantly impact internal control.", "category": "Risk Assessment"},
    {"id": "CC4.1", "name": "Monitoring Activities", "description": "The entity selects, develops, and performs ongoing evaluations.", "category": "Monitoring Activities"},
    {"id": "CC4.2", "name": "Deficiency Communication", "description": "The entity evaluates and communicates internal control deficiencies.", "category": "Monitoring Activities"},
    {"id": "CC5.1", "name": "Control Activity Selection", "description": "The entity selects and develops control activities that mitigate risks.", "category": "Control Activities"},
    {"id": "CC5.2", "name": "Technology General Controls", "description": "The entity selects and develops general control activities over technology.", "category": "Control Activities"},
    {"id": "CC5.3", "name": "Policy Deployment", "description": "The entity deploys control activities through policies and procedures.", "category": "Control Activities"},
    {"id": "CC6.1", "name": "Logical and Physical Access", "description": "The entity implements logical and physical access controls over information assets.", "category": "Logical and Physical Access Controls"},
    {"id": "CC6.2", "name": "User Registration and Authorization", "description": "The entity registers and authorizes new users before granting access.", "category": "Logical and Physical Access Controls"},
    {"id": "CC6.3", "name": "Access Removal", "description": "The entity removes access to information assets when no longer needed.", "category": "Logical and Physical Access Controls"},
    {"id": "CC6.6", "name": "Threat Management", "description": "The entity implements controls to prevent or detect and respond to threats.", "category": "Logical and Physical Access Controls"},
    {"id": "CC6.7", "name": "Data Transmission Protection", "description": "The entity restricts transmission of data to authorized parties.", "category": "Logical and Physical Access Controls"},
    {"id": "CC6.8", "name": "Malicious Software Prevention", "description": "The entity implements controls to prevent or detect malicious software.", "category": "Logical and Physical Access Controls"},
    {"id": "CC7.1", "name": "Infrastructure Monitoring", "description": "The entity monitors system components and detects anomalies.", "category": "System Operations"},
    {"id": "CC7.2", "name": "Incident Detection", "description": "The entity monitors for anomalies that are indicative of incidents.", "category": "System Operations"},
    {"id": "CC7.3", "name": "Incident Response", "description": "The entity evaluates events to determine whether they constitute incidents.", "category": "System Operations"},
    {"id": "CC7.4", "name": "Incident Recovery", "description": "The entity responds to identified incidents by executing defined response procedures.", "category": "System Operations"},
    {"id": "CC8.1", "name": "Change Authorization", "description": "The entity authorizes, designs, develops, tests, and implements changes.", "category": "Change Management"},
    {"id": "CC9.1", "name": "Risk Mitigation", "description": "The entity identifies and assesses risk mitigation activities.", "category": "Risk Mitigation"},
    {"id": "CC9.2", "name": "Vendor Risk Management", "description": "The entity assesses and manages risks from vendors and business partners.", "category": "Risk Mitigation"},
]

_ISO27001_CONTROLS: list[dict] = [
    {"id": "A.5.1", "name": "Policies for Information Security", "description": "Management direction for information security in accordance with business requirements.", "category": "Information Security Policies"},
    {"id": "A.5.2", "name": "Review of Policies", "description": "Policies shall be reviewed at planned intervals or when significant changes occur.", "category": "Information Security Policies"},
    {"id": "A.6.1", "name": "Internal Organization", "description": "A management framework to initiate and control implementation of information security.", "category": "Organization of Information Security"},
    {"id": "A.6.2", "name": "Mobile Devices and Teleworking", "description": "Security for mobile devices and teleworking arrangements.", "category": "Organization of Information Security"},
    {"id": "A.7.1", "name": "Prior to Employment Screening", "description": "Background verification checks on candidates for employment.", "category": "Human Resource Security"},
    {"id": "A.7.2", "name": "During Employment", "description": "Employees and contractors are made aware of information security responsibilities.", "category": "Human Resource Security"},
    {"id": "A.7.3", "name": "Termination and Change", "description": "Information security responsibilities that remain valid after termination.", "category": "Human Resource Security"},
    {"id": "A.8.1", "name": "Responsibility for Assets", "description": "Assets are identified and an inventory of assets is maintained.", "category": "Asset Management"},
    {"id": "A.8.2", "name": "Information Classification", "description": "Information shall be classified in terms of value, sensitivity, and criticality.", "category": "Asset Management"},
    {"id": "A.8.3", "name": "Media Handling", "description": "Procedures for management of removable media.", "category": "Asset Management"},
    {"id": "A.9.1", "name": "Business Requirements of Access Control", "description": "Access control policy established based on business and security requirements.", "category": "Access Control"},
    {"id": "A.9.2", "name": "User Access Management", "description": "Formal user access provisioning and de-provisioning processes.", "category": "Access Control"},
    {"id": "A.9.3", "name": "User Responsibilities", "description": "Users are accountable for safeguarding their authentication information.", "category": "Access Control"},
    {"id": "A.9.4", "name": "System and Application Access Control", "description": "Access to systems and applications is controlled via secure log-on procedures.", "category": "Access Control"},
    {"id": "A.10.1", "name": "Cryptographic Controls", "description": "Policy on the use of cryptographic controls for protection of information.", "category": "Cryptography"},
    {"id": "A.11.1", "name": "Secure Areas", "description": "Physical security perimeters and entry controls.", "category": "Physical and Environmental Security"},
    {"id": "A.11.2", "name": "Equipment Security", "description": "Equipment protection from environmental threats and unauthorized access.", "category": "Physical and Environmental Security"},
    {"id": "A.12.1", "name": "Operational Procedures", "description": "Documented operating procedures available to all users.", "category": "Operations Security"},
    {"id": "A.12.2", "name": "Protection from Malware", "description": "Detection, prevention, and recovery controls for malware.", "category": "Operations Security"},
    {"id": "A.12.3", "name": "Backup", "description": "Backup copies of information and software are taken and tested regularly.", "category": "Operations Security"},
    {"id": "A.12.4", "name": "Logging and Monitoring", "description": "Event logs are produced and regularly reviewed.", "category": "Operations Security"},
    {"id": "A.13.1", "name": "Network Security Management", "description": "Networks are managed and controlled to protect information.", "category": "Communications Security"},
    {"id": "A.13.2", "name": "Information Transfer", "description": "Policies and procedures protect information transfer.", "category": "Communications Security"},
    {"id": "A.14.1", "name": "Security Requirements of Information Systems", "description": "Information security requirements included in new systems requirements.", "category": "System Acquisition, Development and Maintenance"},
    {"id": "A.14.2", "name": "Security in Development and Support Processes", "description": "Rules for the development of software and systems are established.", "category": "System Acquisition, Development and Maintenance"},
    {"id": "A.15.1", "name": "Supplier Relationships", "description": "Information security requirements for mitigating risks with suppliers.", "category": "Supplier Relationships"},
    {"id": "A.16.1", "name": "Incident Management", "description": "Consistent approach to management of information security incidents.", "category": "Information Security Incident Management"},
    {"id": "A.17.1", "name": "Business Continuity Planning", "description": "Information security continuity is embedded in the BCM process.", "category": "Business Continuity Management"},
    {"id": "A.18.1", "name": "Compliance with Legal Requirements", "description": "Identification of applicable legislation, regulations, and contractual requirements.", "category": "Compliance"},
    {"id": "A.18.2", "name": "Information Security Reviews", "description": "Independent review of the organization's approach to information security.", "category": "Compliance"},
]

_HIPAA_CONTROLS: list[dict] = [
    {"id": "164.308(a)(1)", "name": "Security Management Process", "description": "Implement policies and procedures to prevent, detect, contain, and correct security violations.", "category": "Administrative Safeguards"},
    {"id": "164.308(a)(2)", "name": "Assigned Security Responsibility", "description": "Identify the security official responsible for developing and implementing security policies.", "category": "Administrative Safeguards"},
    {"id": "164.308(a)(3)", "name": "Workforce Security", "description": "Implement policies and procedures to ensure appropriate access to ePHI by workforce members.", "category": "Administrative Safeguards"},
    {"id": "164.308(a)(4)", "name": "Information Access Management", "description": "Implement policies and procedures for authorizing access to ePHI.", "category": "Administrative Safeguards"},
    {"id": "164.308(a)(5)", "name": "Security Awareness and Training", "description": "Implement a security awareness and training program for all workforce members.", "category": "Administrative Safeguards"},
    {"id": "164.308(a)(6)", "name": "Security Incident Procedures", "description": "Implement policies and procedures to address security incidents.", "category": "Administrative Safeguards"},
    {"id": "164.308(a)(7)", "name": "Contingency Plan", "description": "Establish policies and procedures for responding to emergencies affecting ePHI.", "category": "Administrative Safeguards"},
    {"id": "164.308(a)(8)", "name": "Evaluation", "description": "Perform periodic technical and non-technical evaluations.", "category": "Administrative Safeguards"},
    {"id": "164.310(a)(1)", "name": "Facility Access Controls", "description": "Implement policies and procedures to limit physical access to electronic information systems.", "category": "Physical Safeguards"},
    {"id": "164.310(b)", "name": "Workstation Use", "description": "Implement policies and procedures for proper workstation use.", "category": "Physical Safeguards"},
    {"id": "164.310(c)", "name": "Workstation Security", "description": "Implement physical safeguards for workstations that access ePHI.", "category": "Physical Safeguards"},
    {"id": "164.310(d)(1)", "name": "Device and Media Controls", "description": "Implement policies and procedures for the receipt and removal of hardware and media containing ePHI.", "category": "Physical Safeguards"},
    {"id": "164.312(a)(1)", "name": "Access Control", "description": "Implement technical policies and procedures for access to ePHI.", "category": "Technical Safeguards"},
    {"id": "164.312(b)", "name": "Audit Controls", "description": "Implement mechanisms to record and examine access and activity in systems containing ePHI.", "category": "Technical Safeguards"},
    {"id": "164.312(c)(1)", "name": "Integrity", "description": "Implement policies and procedures to protect ePHI from improper alteration or destruction.", "category": "Technical Safeguards"},
    {"id": "164.312(d)", "name": "Person or Entity Authentication", "description": "Implement procedures to verify the identity of persons or entities seeking access to ePHI.", "category": "Technical Safeguards"},
    {"id": "164.312(e)(1)", "name": "Transmission Security", "description": "Implement technical security measures to guard against unauthorized access to ePHI during transmission.", "category": "Technical Safeguards"},
]

# ---------------------------------------------------------------------------
# Framework definitions
# ---------------------------------------------------------------------------

_FRAMEWORK_DEFINITIONS: dict[AuditFramework, FrameworkDefinition] = {
    AuditFramework.SOC2_TYPE2: FrameworkDefinition(
        framework=AuditFramework.SOC2_TYPE2,
        version="2017",
        total_controls=len(_SOC2_CONTROLS),
        categories=sorted({c["category"] for c in _SOC2_CONTROLS}),
        description="SOC 2 Type II evaluates the operating effectiveness of controls relevant to security, availability, processing integrity, confidentiality, and privacy over a period of time.",
    ),
    AuditFramework.ISO_27001: FrameworkDefinition(
        framework=AuditFramework.ISO_27001,
        version="2022",
        total_controls=len(_ISO27001_CONTROLS),
        categories=sorted({c["category"] for c in _ISO27001_CONTROLS}),
        description="ISO/IEC 27001 specifies requirements for establishing, implementing, maintaining, and continually improving an information security management system (ISMS).",
    ),
    AuditFramework.HIPAA: FrameworkDefinition(
        framework=AuditFramework.HIPAA,
        version="2013",
        total_controls=len(_HIPAA_CONTROLS),
        categories=sorted({c["category"] for c in _HIPAA_CONTROLS}),
        description="HIPAA Security Rule establishes national standards to protect electronic personal health information (ePHI) through administrative, physical, and technical safeguards.",
    ),
    AuditFramework.PCI_DSS: FrameworkDefinition(
        framework=AuditFramework.PCI_DSS,
        version="4.0",
        total_controls=12,
        categories=["Build and Maintain a Secure Network", "Protect Cardholder Data", "Maintain a Vulnerability Management Program", "Implement Strong Access Control Measures", "Regularly Monitor and Test Networks", "Maintain an Information Security Policy"],
        description="PCI DSS provides a baseline of technical and operational requirements to protect payment account data.",
    ),
    AuditFramework.GDPR: FrameworkDefinition(
        framework=AuditFramework.GDPR,
        version="2016/679",
        total_controls=10,
        categories=["Lawfulness of Processing", "Data Subject Rights", "Data Protection by Design", "International Transfers", "Data Breach Notification", "Records of Processing"],
        description="The General Data Protection Regulation governs the processing of personal data of individuals in the European Union.",
    ),
    AuditFramework.NIST_CSF: FrameworkDefinition(
        framework=AuditFramework.NIST_CSF,
        version="2.0",
        total_controls=23,
        categories=["Identify", "Protect", "Detect", "Respond", "Recover", "Govern"],
        description="NIST Cybersecurity Framework provides guidance for managing and reducing cybersecurity risk.",
    ),
    AuditFramework.EU_AI_ACT: FrameworkDefinition(
        framework=AuditFramework.EU_AI_ACT,
        version="2024",
        total_controls=8,
        categories=["Risk Classification", "Transparency", "Human Oversight", "Data Governance", "Technical Documentation", "Conformity Assessment"],
        description="The EU AI Act establishes a harmonized framework for the development, placing on the market, and use of AI systems in the European Union.",
    ),
}

_FRAMEWORK_CONTROL_MAP: dict[AuditFramework, list[dict]] = {
    AuditFramework.SOC2_TYPE2: _SOC2_CONTROLS,
    AuditFramework.ISO_27001: _ISO27001_CONTROLS,
    AuditFramework.HIPAA: _HIPAA_CONTROLS,
}


class AuditReportService:
    """Service for generating comprehensive audit-ready compliance reports."""

    def __init__(self, db, copilot_client=None):
        self._db = db
        self._copilot_client = copilot_client

    # ------------------------------------------------------------------
    # Report CRUD
    # ------------------------------------------------------------------

    async def generate_report(
        self,
        org_id: UUID,
        framework: AuditFramework,
        period_start: datetime,
        period_end: datetime,
        format: str = "pdf",
    ) -> AuditReport:
        """Generate an audit-ready compliance report for the given framework."""
        logger.info(
            "audit_report.generate",
            org_id=str(org_id),
            framework=framework.value,
        )

        control_results = self._evaluate_controls(framework)
        executive_summary = self._generate_executive_summary(framework, control_results)
        gaps = self._extract_gaps(control_results)
        evidence_summary = self._build_evidence_summary(control_results)

        try:
            report_format = ReportFormat(format)
        except ValueError:
            report_format = ReportFormat.PDF

        report = AuditReport(
            id=uuid4(),
            org_id=org_id,
            framework=framework,
            title=f"{framework.value.upper().replace('_', ' ')} Compliance Report",
            generated_at=datetime.utcnow(),
            period_start=period_start,
            period_end=period_end,
            overall_status=self._compute_overall_status(control_results),
            control_results=control_results,
            evidence_summary=evidence_summary,
            executive_summary=executive_summary,
            gaps=gaps,
            format=report_format,
        )
        _reports[report.id] = report
        logger.info("audit_report.generated", report_id=str(report.id))
        return report

    async def get_report(self, report_id: UUID) -> AuditReport | None:
        """Return a previously generated report by ID."""
        return _reports.get(report_id)

    async def list_reports(
        self,
        org_id: UUID,
        framework: AuditFramework | None = None,
    ) -> list[AuditReport]:
        """List reports for an organization, optionally filtered by framework."""
        results = [r for r in _reports.values() if r.org_id == org_id]
        if framework is not None:
            results = [r for r in results if r.framework == framework]
        return sorted(results, key=lambda r: r.generated_at, reverse=True)

    # ------------------------------------------------------------------
    # Frameworks
    # ------------------------------------------------------------------

    async def get_framework_definition(
        self,
        framework: AuditFramework,
    ) -> FrameworkDefinition:
        """Return metadata for the requested framework."""
        defn = _FRAMEWORK_DEFINITIONS.get(framework)
        if defn is None:
            raise ValueError(f"Unsupported framework: {framework.value}")
        return defn

    async def list_frameworks(self) -> list[FrameworkDefinition]:
        """Return all supported framework definitions."""
        return list(_FRAMEWORK_DEFINITIONS.values())

    # ------------------------------------------------------------------
    # Evidence collection
    # ------------------------------------------------------------------

    async def collect_evidence_auto(
        self,
        org_id: UUID,
        framework: AuditFramework,
    ) -> list[EvidenceItem]:
        """Automatically collect evidence artifacts for the given framework."""
        logger.info(
            "audit_report.collect_evidence",
            org_id=str(org_id),
            framework=framework.value,
        )

        now = datetime.utcnow()
        evidence_items: list[EvidenceItem] = []

        # Simulate automatic evidence collection across common sources
        source_templates = [
            (EvidenceType.POLICY_DOCUMENT, "Information Security Policy", "policy", "/docs/policies/security-policy.pdf"),
            (EvidenceType.ACCESS_LOG, "System Access Audit Log", "access_logs", "/logs/access-audit-2024.csv"),
            (EvidenceType.CONFIGURATION, "Encryption Configuration", "infrastructure", "/config/encryption-settings.json"),
            (EvidenceType.TEST_RESULT, "Penetration Test Report", "security_testing", "/reports/pentest-q4.pdf"),
            (EvidenceType.TRAINING_RECORD, "Security Awareness Training Records", "hr_system", "/training/completion-report.csv"),
            (EvidenceType.INCIDENT_LOG, "Incident Response Log", "incident_management", "/incidents/response-log-2024.json"),
            (EvidenceType.CODE_COMMIT, "Access Control Implementation", "github", "https://github.com/org/repo/commit/abc123"),
            (EvidenceType.SCREENSHOT, "MFA Configuration Screenshot", "admin_console", "/screenshots/mfa-config.png"),
        ]

        for etype, title, source, url in source_templates:
            evidence_items.append(
                EvidenceItem(
                    id=uuid4(),
                    type=etype,
                    title=title,
                    description=f"Auto-collected {title.lower()} for {framework.value} audit",
                    source=source,
                    url=url,
                    collected_at=now,
                    verified=True,
                )
            )

        logger.info(
            "audit_report.evidence_collected",
            org_id=str(org_id),
            count=len(evidence_items),
        )
        return evidence_items

    # ------------------------------------------------------------------
    # Auditor portal
    # ------------------------------------------------------------------

    async def create_auditor_session(
        self,
        org_id: UUID,
        framework: AuditFramework,
        auditor_email: str,
        auditor_name: str,
        role: AuditorRole,
    ) -> AuditorPortalSession:
        """Create an authenticated portal session for an external auditor."""
        logger.info(
            "audit_report.auditor_invite",
            org_id=str(org_id),
            auditor_email=auditor_email,
        )

        permissions = ["view_report", "view_evidence", "add_comment"]
        if role == AuditorRole.LEAD_AUDITOR:
            permissions.extend(["request_evidence", "mark_reviewed"])

        session = AuditorPortalSession(
            id=uuid4(),
            auditor_email=auditor_email,
            auditor_name=auditor_name,
            role=role,
            org_id=org_id,
            framework=framework,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            access_token=secrets.token_urlsafe(48),
            permissions=permissions,
        )
        _auditor_sessions[session.id] = session
        return session

    async def validate_auditor_session(
        self,
        session_id: UUID,
        access_token: str,
    ) -> AuditorPortalSession | None:
        """Validate an auditor session by ID and token."""
        session = _auditor_sessions.get(session_id)
        if session is None:
            return None
        if session.access_token != access_token:
            return None
        if session.expires_at < datetime.utcnow():
            return None
        return session

    async def submit_auditor_comment(
        self,
        session_id: UUID,
        control_id: str,
        comment: str,
        requires_response: bool = False,
    ) -> AuditorComment:
        """Record a comment from an auditor on a specific control."""
        session = _auditor_sessions.get(session_id)
        if session is None:
            raise ValueError("Invalid auditor session")

        auditor_comment = AuditorComment(
            id=uuid4(),
            session_id=session_id,
            control_id=control_id,
            comment=comment,
            created_at=datetime.utcnow(),
            requires_response=requires_response,
        )
        _auditor_comments.append(auditor_comment)
        logger.info(
            "audit_report.auditor_comment",
            session_id=str(session_id),
            control_id=control_id,
        )
        return auditor_comment

    async def get_auditor_comments(
        self,
        org_id: UUID,
        framework: AuditFramework,
    ) -> list[AuditorComment]:
        """Return all auditor comments for a framework within an organization."""
        session_ids = {
            s.id
            for s in _auditor_sessions.values()
            if s.org_id == org_id and s.framework == framework
        }
        return [c for c in _auditor_comments if c.session_id in session_ids]

    # ------------------------------------------------------------------
    # Gap analysis
    # ------------------------------------------------------------------

    async def get_gap_analysis(
        self,
        org_id: UUID,
        framework: AuditFramework,
    ) -> list[ControlGap]:
        """Return identified control gaps for a framework."""
        logger.info(
            "audit_report.gap_analysis",
            org_id=str(org_id),
            framework=framework.value,
        )
        control_results = self._evaluate_controls(framework)
        return self._extract_gaps(control_results)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    async def export_evidence_package(self, report_id: UUID) -> dict:
        """Export a complete evidence package for a report."""
        report = _reports.get(report_id)
        if report is None:
            raise ValueError("Report not found")

        logger.info("audit_report.export", report_id=str(report_id))

        evidence_files: list[dict] = []
        for cr in report.control_results:
            for ev in cr.evidence:
                evidence_files.append({
                    "evidence_id": str(ev.id),
                    "type": ev.type.value,
                    "title": ev.title,
                    "source": ev.source,
                    "url": ev.url,
                })

        return {
            "report_id": str(report.id),
            "framework": report.framework.value,
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "overall_status": report.overall_status.value,
            "executive_summary": report.executive_summary,
            "total_controls": report.evidence_summary.total_controls,
            "compliant_controls": report.evidence_summary.compliant,
            "coverage_pct": report.evidence_summary.coverage_pct,
            "evidence_files": evidence_files,
            "gap_count": len(report.gaps),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate_controls(self, framework: AuditFramework) -> list[ControlResult]:
        """Evaluate controls for a framework and return simulated results."""
        controls = _FRAMEWORK_CONTROL_MAP.get(framework, [])
        now = datetime.utcnow()
        results: list[ControlResult] = []

        for idx, ctrl in enumerate(controls):
            # Deterministic status based on index for reproducibility
            if idx % 5 == 0:
                status = ControlStatus.PARTIALLY_COMPLIANT
            elif idx % 7 == 0:
                status = ControlStatus.NON_COMPLIANT
            else:
                status = ControlStatus.COMPLIANT

            evidence: list[EvidenceItem] = []
            if status != ControlStatus.NON_COMPLIANT:
                evidence.append(
                    EvidenceItem(
                        id=uuid4(),
                        type=EvidenceType.POLICY_DOCUMENT,
                        title=f"Policy for {ctrl['name']}",
                        description=f"Documentation supporting {ctrl['id']}",
                        source="policy_repository",
                        url=f"/evidence/{ctrl['id'].lower().replace('.', '-')}.pdf",
                        collected_at=now,
                        verified=status == ControlStatus.COMPLIANT,
                    )
                )

            findings = ""
            remediation = ""
            if status == ControlStatus.NON_COMPLIANT:
                findings = f"Control {ctrl['id']} lacks sufficient evidence of implementation."
                remediation = f"Implement and document controls for {ctrl['name']}."
            elif status == ControlStatus.PARTIALLY_COMPLIANT:
                findings = f"Control {ctrl['id']} is partially implemented; additional evidence needed."
                remediation = f"Complete implementation and gather additional evidence for {ctrl['name']}."

            results.append(
                ControlResult(
                    control_id=ctrl["id"],
                    control_name=ctrl["name"],
                    control_description=ctrl["description"],
                    category=ctrl["category"],
                    status=status,
                    evidence=evidence,
                    findings=findings,
                    remediation=remediation,
                    last_assessed=now,
                )
            )

        return results

    def _generate_executive_summary(
        self,
        framework: AuditFramework,
        results: list[ControlResult],
    ) -> str:
        """Build a human-readable executive summary from control results."""
        total = len(results)
        compliant = sum(1 for r in results if r.status == ControlStatus.COMPLIANT)
        partial = sum(1 for r in results if r.status == ControlStatus.PARTIALLY_COMPLIANT)
        non_compliant = sum(1 for r in results if r.status == ControlStatus.NON_COMPLIANT)

        pct = (compliant / total * 100) if total else 0

        return (
            f"This report presents the {framework.value.upper().replace('_', ' ')} compliance "
            f"assessment results covering {total} controls. "
            f"{compliant} controls ({pct:.0f}%) are fully compliant, "
            f"{partial} are partially compliant, and {non_compliant} require remediation. "
            f"The organization should prioritize addressing the {non_compliant} non-compliant "
            f"control(s) to achieve full compliance readiness before the next audit cycle."
        )

    def _extract_gaps(self, results: list[ControlResult]) -> list[ControlGap]:
        """Identify gaps from non-compliant or partially-compliant controls."""
        gaps: list[ControlGap] = []
        for r in results:
            if r.status in (ControlStatus.NON_COMPLIANT, ControlStatus.PARTIALLY_COMPLIANT):
                severity = "high" if r.status == ControlStatus.NON_COMPLIANT else "medium"
                effort = 40.0 if r.status == ControlStatus.NON_COMPLIANT else 16.0

                remediation_steps = [
                    f"Review current implementation of {r.control_id}",
                    f"Document evidence for {r.control_name}",
                    "Assign remediation owner and deadline",
                    "Verify and validate corrective actions",
                ]

                gaps.append(
                    ControlGap(
                        control_id=r.control_id,
                        control_name=r.control_name,
                        status=r.status,
                        severity=severity,
                        remediation_steps=remediation_steps,
                        estimated_effort_hours=effort,
                        deadline=datetime.utcnow() + timedelta(days=90),
                    )
                )
        return gaps

    def _build_evidence_summary(self, results: list[ControlResult]) -> EvidenceSummary:
        """Build an aggregate evidence summary from control results."""
        total = len(results)
        compliant = sum(1 for r in results if r.status == ControlStatus.COMPLIANT)
        partial = sum(1 for r in results if r.status == ControlStatus.PARTIALLY_COMPLIANT)
        non_compliant = sum(1 for r in results if r.status == ControlStatus.NON_COMPLIANT)
        na = sum(1 for r in results if r.status == ControlStatus.NOT_APPLICABLE)

        evidence_count = sum(len(r.evidence) for r in results)
        assessed = total - na
        coverage = (compliant + partial) / assessed * 100 if assessed else 0

        return EvidenceSummary(
            total_controls=total,
            compliant=compliant,
            partially_compliant=partial,
            non_compliant=non_compliant,
            not_applicable=na,
            coverage_pct=round(coverage, 1),
            evidence_count=evidence_count,
            auto_collected=evidence_count,
            manual_uploaded=0,
        )

    def _compute_overall_status(self, results: list[ControlResult]) -> ControlStatus:
        """Determine the overall compliance status from individual results."""
        if not results:
            return ControlStatus.NOT_ASSESSED
        if any(r.status == ControlStatus.NON_COMPLIANT for r in results):
            return ControlStatus.PARTIALLY_COMPLIANT
        if all(r.status == ControlStatus.COMPLIANT for r in results):
            return ControlStatus.COMPLIANT
        return ControlStatus.PARTIALLY_COMPLIANT
