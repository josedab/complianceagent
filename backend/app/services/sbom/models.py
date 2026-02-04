"""Models for SBOM (Software Bill of Materials) compliance integration."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SBOMFormat(str, Enum):
    """Supported SBOM output formats."""
    
    SPDX_JSON = "spdx-json"
    SPDX_XML = "spdx-xml"
    CYCLONEDX_JSON = "cyclonedx-json"
    CYCLONEDX_XML = "cyclonedx-xml"
    SWID = "swid"


class LicenseRisk(str, Enum):
    """License compliance risk levels."""
    
    LOW = "low"  # Permissive (MIT, Apache, BSD)
    MEDIUM = "medium"  # Weak copyleft (LGPL, MPL)
    HIGH = "high"  # Strong copyleft (GPL, AGPL)
    CRITICAL = "critical"  # Unknown or incompatible
    UNKNOWN = "unknown"


class ComplianceImpact(str, Enum):
    """Impact level for compliance violations."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class VulnerabilitySeverity(str, Enum):
    """CVE severity levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class SBOMComponent(BaseModel):
    """A single component in the SBOM."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    version: str
    purl: str | None = None  # Package URL
    cpe: str | None = None  # Common Platform Enumeration
    supplier: str | None = None
    author: str | None = None
    license: str | None = None
    license_risk: LicenseRisk = LicenseRisk.UNKNOWN
    type: str = "library"  # library, framework, application, container, os, device
    scope: str = "required"  # required, optional, excluded
    hash_sha256: str | None = None
    hash_sha1: str | None = None
    hash_md5: str | None = None
    download_url: str | None = None
    homepage: str | None = None
    description: str | None = None
    is_direct: bool = True
    dependencies: list[str] = Field(default_factory=list)
    vulnerabilities: list["ComponentVulnerability"] = Field(default_factory=list)
    compliance_issues: list["ComponentComplianceIssue"] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComponentVulnerability(BaseModel):
    """Vulnerability affecting a component."""
    
    id: str  # CVE-XXXX-XXXXX
    severity: VulnerabilitySeverity
    cvss_score: float | None = None
    cvss_vector: str | None = None
    description: str
    published_date: datetime | None = None
    modified_date: datetime | None = None
    fixed_in_version: str | None = None
    references: list[str] = Field(default_factory=list)
    exploitability: str | None = None  # active, poc, theoretical, none
    compliance_mappings: list["VulnerabilityComplianceMapping"] = Field(default_factory=list)


class VulnerabilityComplianceMapping(BaseModel):
    """Maps a vulnerability to regulatory compliance requirements."""
    
    vulnerability_id: str
    regulation: str
    requirement: str
    article: str | None = None
    impact: ComplianceImpact
    rationale: str
    remediation_deadline_days: int | None = None
    evidence_required: list[str] = Field(default_factory=list)


class ComponentComplianceIssue(BaseModel):
    """Compliance issue for a component."""
    
    id: UUID = Field(default_factory=uuid4)
    issue_type: str  # license, vulnerability, supply_chain, certification
    regulation: str
    requirement: str
    article: str | None = None
    impact: ComplianceImpact
    description: str
    remediation: str | None = None
    deadline: datetime | None = None


class SBOMDocument(BaseModel):
    """Complete SBOM document with compliance metadata."""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID | None = None
    repository_id: UUID | None = None
    name: str
    version: str
    format: SBOMFormat = SBOMFormat.CYCLONEDX_JSON
    spec_version: str = "1.5"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str | None = None
    tool_name: str = "ComplianceAgent"
    tool_version: str = "0.4.0"
    
    # Components
    components: list[SBOMComponent] = Field(default_factory=list)
    total_components: int = 0
    direct_dependencies: int = 0
    transitive_dependencies: int = 0
    
    # Vulnerability summary
    total_vulnerabilities: int = 0
    critical_vulnerabilities: int = 0
    high_vulnerabilities: int = 0
    medium_vulnerabilities: int = 0
    low_vulnerabilities: int = 0
    
    # Compliance summary
    compliance_score: float = 100.0
    total_compliance_issues: int = 0
    critical_compliance_issues: int = 0
    
    # License summary
    license_types: dict[str, int] = Field(default_factory=dict)
    high_risk_licenses: int = 0
    unknown_licenses: int = 0
    
    # Metadata
    source_files: list[str] = Field(default_factory=list)
    generation_time_ms: float | None = None
    signature: str | None = None  # Digital signature for authenticity
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def to_spdx(self) -> dict[str, Any]:
        """Convert to SPDX format."""
        return {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": f"SPDXRef-DOCUMENT-{self.id}",
            "name": self.name,
            "documentNamespace": f"https://complianceagent.ai/sbom/{self.id}",
            "creationInfo": {
                "created": self.created_at.isoformat(),
                "creators": [
                    f"Tool: {self.tool_name}-{self.tool_version}",
                    f"Organization: {self.organization_id}" if self.organization_id else "Organization: Unknown",
                ],
            },
            "packages": [
                {
                    "SPDXID": f"SPDXRef-Package-{c.id}",
                    "name": c.name,
                    "versionInfo": c.version,
                    "downloadLocation": c.download_url or "NOASSERTION",
                    "licenseConcluded": c.license or "NOASSERTION",
                    "supplier": f"Organization: {c.supplier}" if c.supplier else "NOASSERTION",
                    "checksums": [
                        {"algorithm": "SHA256", "checksumValue": c.hash_sha256}
                    ] if c.hash_sha256 else [],
                }
                for c in self.components
            ],
            "relationships": [
                {
                    "spdxElementId": f"SPDXRef-DOCUMENT-{self.id}",
                    "relatedSpdxElement": f"SPDXRef-Package-{c.id}",
                    "relationshipType": "DESCRIBES",
                }
                for c in self.components
            ],
        }
    
    def to_cyclonedx(self) -> dict[str, Any]:
        """Convert to CycloneDX format."""
        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{self.id}",
            "version": 1,
            "metadata": {
                "timestamp": self.created_at.isoformat(),
                "tools": [
                    {
                        "vendor": "ComplianceAgent",
                        "name": self.tool_name,
                        "version": self.tool_version,
                    }
                ],
                "component": {
                    "type": "application",
                    "name": self.name,
                    "version": self.version,
                },
            },
            "components": [
                {
                    "type": c.type,
                    "bom-ref": str(c.id),
                    "name": c.name,
                    "version": c.version,
                    "purl": c.purl,
                    "licenses": [{"license": {"id": c.license}}] if c.license else [],
                    "hashes": [
                        {"alg": "SHA-256", "content": c.hash_sha256}
                    ] if c.hash_sha256 else [],
                    "supplier": {"name": c.supplier} if c.supplier else None,
                }
                for c in self.components
            ],
            "vulnerabilities": [
                {
                    "id": v.id,
                    "source": {"name": "NVD"},
                    "ratings": [
                        {
                            "severity": v.severity.value,
                            "score": v.cvss_score,
                            "vector": v.cvss_vector,
                        }
                    ] if v.cvss_score else [],
                    "description": v.description,
                    "recommendation": f"Upgrade to {v.fixed_in_version}" if v.fixed_in_version else "Review and mitigate",
                }
                for c in self.components
                for v in c.vulnerabilities
            ],
        }


class SBOMComplianceReport(BaseModel):
    """Compliance report for an SBOM."""
    
    id: UUID = Field(default_factory=uuid4)
    sbom_id: UUID
    organization_id: UUID | None = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Overall scores
    overall_compliance_score: float
    vulnerability_score: float
    license_score: float
    supply_chain_score: float
    
    # Regulation-specific compliance
    regulation_compliance: dict[str, float] = Field(default_factory=dict)
    
    # Issues by regulation
    issues_by_regulation: dict[str, list[ComponentComplianceIssue]] = Field(default_factory=dict)
    
    # Vulnerability to compliance mappings
    vulnerability_mappings: list[VulnerabilityComplianceMapping] = Field(default_factory=list)
    
    # Risk summary
    critical_risks: list[str] = Field(default_factory=list)
    high_risks: list[str] = Field(default_factory=list)
    
    # Recommendations
    recommendations: list[str] = Field(default_factory=list)
    
    # Timeline requirements
    immediate_actions: list[str] = Field(default_factory=list)
    short_term_actions: list[str] = Field(default_factory=list)  # 30 days
    long_term_actions: list[str] = Field(default_factory=list)  # 90 days


# Regulatory mappings for vulnerabilities
VULNERABILITY_REGULATION_MAPPINGS = {
    # PCI-DSS Requirements
    "PCI-DSS": {
        "critical": {
            "requirement": "Requirement 6.3.3",
            "article": "6.3.3",
            "rationale": "Critical vulnerabilities in software components must be addressed within 30 days",
            "deadline_days": 30,
            "evidence": ["Vulnerability scan results", "Patch installation proof", "Testing evidence"],
        },
        "high": {
            "requirement": "Requirement 6.3.3",
            "article": "6.3.3",
            "rationale": "High severity vulnerabilities must be addressed within 90 days",
            "deadline_days": 90,
            "evidence": ["Vulnerability scan results", "Remediation plan"],
        },
    },
    # HIPAA Security Rule
    "HIPAA": {
        "critical": {
            "requirement": "§164.308(a)(1)(ii)(B) - Risk Management",
            "article": "164.308",
            "rationale": "Security measures to reduce risks to ePHI must address critical vulnerabilities",
            "deadline_days": 30,
            "evidence": ["Risk assessment", "Remediation documentation"],
        },
        "high": {
            "requirement": "§164.308(a)(1)(ii)(B) - Risk Management",
            "article": "164.308",
            "rationale": "High severity vulnerabilities affecting ePHI systems require prompt attention",
            "deadline_days": 60,
            "evidence": ["Risk assessment", "Mitigation plan"],
        },
    },
    # SOC 2
    "SOC 2": {
        "critical": {
            "requirement": "CC7.1 - System Operations",
            "article": "CC7.1",
            "rationale": "Vulnerabilities affecting system availability and security must be promptly remediated",
            "deadline_days": 30,
            "evidence": ["Vulnerability report", "Change management ticket", "Testing results"],
        },
    },
    # GDPR
    "GDPR": {
        "critical": {
            "requirement": "Article 32 - Security of Processing",
            "article": "32",
            "rationale": "Appropriate technical measures must ensure security of personal data processing",
            "deadline_days": 30,
            "evidence": ["Security assessment", "Remediation proof"],
        },
    },
    # NIST CSF
    "NIST CSF": {
        "critical": {
            "requirement": "ID.RA-1, RS.MI-1",
            "article": "ID.RA-1",
            "rationale": "Asset vulnerabilities must be identified and mitigated",
            "deadline_days": 30,
            "evidence": ["Vulnerability scan", "Mitigation evidence"],
        },
    },
}

# License compliance mappings
LICENSE_COMPLIANCE_INFO = {
    "MIT": {"risk": LicenseRisk.LOW, "copyleft": False, "attribution_required": True},
    "Apache-2.0": {"risk": LicenseRisk.LOW, "copyleft": False, "attribution_required": True, "patent_grant": True},
    "BSD-2-Clause": {"risk": LicenseRisk.LOW, "copyleft": False, "attribution_required": True},
    "BSD-3-Clause": {"risk": LicenseRisk.LOW, "copyleft": False, "attribution_required": True},
    "ISC": {"risk": LicenseRisk.LOW, "copyleft": False, "attribution_required": True},
    "LGPL-2.1": {"risk": LicenseRisk.MEDIUM, "copyleft": "weak", "attribution_required": True},
    "LGPL-3.0": {"risk": LicenseRisk.MEDIUM, "copyleft": "weak", "attribution_required": True},
    "MPL-2.0": {"risk": LicenseRisk.MEDIUM, "copyleft": "weak", "attribution_required": True},
    "GPL-2.0": {"risk": LicenseRisk.HIGH, "copyleft": "strong", "attribution_required": True},
    "GPL-3.0": {"risk": LicenseRisk.HIGH, "copyleft": "strong", "attribution_required": True},
    "AGPL-3.0": {"risk": LicenseRisk.HIGH, "copyleft": "strong", "network_copyleft": True},
    "Proprietary": {"risk": LicenseRisk.CRITICAL, "copyleft": False, "review_required": True},
    "UNKNOWN": {"risk": LicenseRisk.CRITICAL, "review_required": True},
}
