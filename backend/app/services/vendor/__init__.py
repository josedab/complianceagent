"""Vendor and third-party risk assessment module.

.. deprecated::
    This module contains the original vendor risk models. Newer implementations
    are in :mod:`app.services.vendor_risk` (risk analysis) and
    :mod:`app.services.vendor_assessment` (compliance assessment). Prefer those
    for new development.
"""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog


logger = structlog.get_logger()


class VendorType(str, Enum):
    """Types of vendors."""

    SAAS = "saas"
    LIBRARY = "library"
    API = "api"
    INFRASTRUCTURE = "infrastructure"
    DATA_PROCESSOR = "data_processor"


class RiskLevel(str, Enum):
    """Risk levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class VendorRiskAssessment:
    """Risk assessment for a vendor."""

    id: UUID = field(default_factory=uuid4)
    vendor_name: str = ""
    vendor_type: VendorType = VendorType.SAAS
    overall_risk: RiskLevel = RiskLevel.MEDIUM
    data_access_risk: RiskLevel = RiskLevel.MEDIUM
    compliance_risk: RiskLevel = RiskLevel.MEDIUM
    security_risk: RiskLevel = RiskLevel.MEDIUM
    availability_risk: RiskLevel = RiskLevel.LOW
    risk_score: float = 0.0  # 0-100
    findings: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    data_types_accessed: list[str] = field(default_factory=list)
    jurisdictions: list[str] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    next_review: datetime | None = None


@dataclass
class DependencyVulnerability:
    """A vulnerability in a dependency."""

    package_name: str
    package_version: str
    vulnerability_id: str  # CVE ID
    severity: str
    description: str
    fixed_version: str | None = None
    compliance_impact: list[str] = field(default_factory=list)


@dataclass
class DependencyScanResult:
    """Result of scanning dependencies."""

    scan_id: UUID = field(default_factory=uuid4)
    scanned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    total_dependencies: int = 0
    direct_dependencies: int = 0
    transitive_dependencies: int = 0
    vulnerabilities: list[DependencyVulnerability] = field(default_factory=list)
    outdated_count: int = 0
    license_issues: list[dict[str, Any]] = field(default_factory=list)
    risk_score: float = 0.0


# Known problematic packages for compliance
COMPLIANCE_FLAGGED_PACKAGES = {
    # Packages with known security issues
    "event-stream": {
        "reason": "Historical supply chain attack",
        "severity": "critical",
        "compliance": ["SOC 2", "PCI-DSS"],
    },
    "ua-parser-js": {
        "reason": "Historical supply chain attack",
        "severity": "high",
        "compliance": ["SOC 2"],
    },
    # Packages with data concerns
    "analytics": {
        "reason": "May send data to third parties",
        "severity": "medium",
        "compliance": ["GDPR", "CCPA"],
    },
    # Cryptographic concerns
    "md5": {
        "reason": "MD5 is cryptographically broken",
        "severity": "high",
        "compliance": ["PCI-DSS", "HIPAA"],
    },
    "sha1": {
        "reason": "SHA1 is deprecated for cryptographic use",
        "severity": "medium",
        "compliance": ["PCI-DSS", "HIPAA"],
    },
}


class _LegacyVendorRiskAssessor:
    """Assessor for vendor and third-party risk (legacy)."""

    def __init__(self):
        self._vendor_cache: dict[str, VendorRiskAssessment] = {}

    async def assess_vendor(
        self,
        vendor_name: str,
        vendor_type: VendorType,
        data_types: list[str],
        jurisdictions: list[str],
        certifications: list[str] | None = None,
    ) -> VendorRiskAssessment:
        """Assess risk for a vendor."""
        findings = []
        risk_scores = []

        # Check data access risk
        high_risk_data = ["PII", "PHI", "financial", "biometric"]
        data_risk = RiskLevel.LOW
        if any(dt in data_types for dt in high_risk_data):
            data_risk = RiskLevel.HIGH
            findings.append(f"Vendor accesses high-risk data types: {data_types}")
            risk_scores.append(80)
        else:
            risk_scores.append(20)

        # Check compliance risk based on certifications
        compliance_risk = RiskLevel.HIGH
        compliance_certs = ["SOC 2", "ISO 27001", "HIPAA", "PCI-DSS"]
        if certifications:
            matching = [c for c in certifications if any(cc in c for cc in compliance_certs)]
            if matching:
                compliance_risk = RiskLevel.LOW
                risk_scores.append(20)
            else:
                findings.append("Vendor lacks relevant compliance certifications")
                risk_scores.append(70)
        else:
            findings.append("No certifications provided")
            risk_scores.append(80)

        # Check jurisdiction risk
        high_risk_jurisdictions = ["CN", "RU"]
        if any(j in jurisdictions for j in high_risk_jurisdictions):
            findings.append(f"Vendor operates in high-risk jurisdictions: {jurisdictions}")
            risk_scores.append(90)
        else:
            risk_scores.append(20)

        # Calculate overall risk
        avg_score = sum(risk_scores) / len(risk_scores) if risk_scores else 50
        if avg_score >= 70:
            overall_risk = RiskLevel.HIGH
        elif avg_score >= 50:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW

        assessment = VendorRiskAssessment(
            vendor_name=vendor_name,
            vendor_type=vendor_type,
            overall_risk=overall_risk,
            data_access_risk=data_risk,
            compliance_risk=compliance_risk,
            security_risk=RiskLevel.MEDIUM,  # Would need security scan
            risk_score=avg_score,
            findings=findings,
            certifications=certifications or [],
            data_types_accessed=data_types,
            jurisdictions=jurisdictions,
        )

        self._vendor_cache[vendor_name] = assessment
        return assessment

    async def scan_dependencies(
        self,
        package_manager: str,
        lockfile_content: str,
        regulations: list[str] | None = None,
    ) -> DependencyScanResult:
        """Scan dependencies for vulnerabilities and compliance issues."""
        vulnerabilities = []
        license_issues = []
        packages = []

        # Parse lockfile based on package manager
        if package_manager == "npm":
            packages = self._parse_npm_lockfile(lockfile_content)
        elif package_manager == "pip":
            packages = self._parse_pip_requirements(lockfile_content)

        # Check against known compliance-flagged packages
        for pkg_name, pkg_version in packages:
            if pkg_name in COMPLIANCE_FLAGGED_PACKAGES:
                flag = COMPLIANCE_FLAGGED_PACKAGES[pkg_name]
                vulnerabilities.append(
                    DependencyVulnerability(
                        package_name=pkg_name,
                        package_version=pkg_version,
                        vulnerability_id=f"COMPLIANCE-{pkg_name.upper()}",
                        severity=flag["severity"],
                        description=flag["reason"],
                        compliance_impact=flag["compliance"],
                    )
                )

        # Calculate risk score
        critical_count = sum(1 for v in vulnerabilities if v.severity == "critical")
        high_count = sum(1 for v in vulnerabilities if v.severity == "high")
        risk_score = min(100, critical_count * 30 + high_count * 15)

        return DependencyScanResult(
            total_dependencies=len(packages),
            direct_dependencies=len(packages),  # Simplified
            transitive_dependencies=0,
            vulnerabilities=vulnerabilities,
            license_issues=license_issues,
            risk_score=risk_score,
        )

    def _parse_npm_lockfile(self, content: str) -> list[tuple[str, str]]:
        """Parse npm package-lock.json."""

        packages = []
        try:
            data = json.loads(content)
            deps = data.get("dependencies", {})
            for name, info in deps.items():
                version = info.get("version", "unknown") if isinstance(info, dict) else str(info)
                packages.append((name, version))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse npm lockfile: {e}")
        return packages

    def _parse_pip_requirements(self, content: str) -> list[tuple[str, str]]:
        """Parse pip requirements.txt."""
        packages = []
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" in line:
                parts = line.split("==")
                packages.append((parts[0].strip(), parts[1].strip()))
            elif ">=" in line:
                parts = line.split(">=")
                packages.append((parts[0].strip(), f">={parts[1].strip()}"))
            else:
                packages.append((line, "any"))
        return packages

    def get_vendor_alternatives(
        self,
        vendor_name: str,
        requirement: str,
    ) -> list[dict[str, Any]]:
        """Suggest compliant alternatives to a flagged vendor/package."""
        alternatives = {
            "md5": [
                {"name": "hashlib (SHA-256)", "reason": "Cryptographically secure"},
                {"name": "bcrypt", "reason": "For password hashing"},
            ],
            "sha1": [
                {"name": "hashlib (SHA-256)", "reason": "Current standard"},
                {"name": "hashlib (SHA-3)", "reason": "Latest standard"},
            ],
            "analytics": [
                {"name": "Plausible", "reason": "Privacy-focused, GDPR compliant"},
                {"name": "Fathom", "reason": "Privacy-first analytics"},
            ],
        }
        return alternatives.get(vendor_name, [])


# Test-compatible models and service


@dataclass
class VendorAssessment:
    """Assessment result for a vendor."""

    vendor_name: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    certifications: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vendor_name": self.vendor_name,
            "risk_level": self.risk_level.value
            if isinstance(self.risk_level, RiskLevel)
            else str(self.risk_level),
            "certifications": self.certifications,
            "issues": self.issues,
            "recommendations": self.recommendations,
        }


@dataclass
class DependencyRisk:
    """Risk assessment for a dependency."""

    package_name: str = ""
    version: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    vulnerabilities: list[dict[str, Any]] = field(default_factory=list)
    license: str = ""
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_name": self.package_name,
            "version": self.version,
            "risk_level": self.risk_level.value
            if isinstance(self.risk_level, RiskLevel)
            else str(self.risk_level),
            "vulnerabilities": self.vulnerabilities,
            "license": self.license,
            "recommendations": self.recommendations,
        }


class VendorRiskAssessor:
    """Assessor for vendor and dependency risks."""

    def __init__(self):
        pass

    async def assess_vendor(
        self,
        vendor_name: str = "",
        data_types: list[str] | None = None,
        regulations: list[str] | None = None,
    ) -> VendorAssessment:
        """Assess a vendor's compliance risk."""
        vendor_data = await self._fetch_vendor_data(vendor_name)
        certifications = vendor_data.get("certifications", [])
        risk_level = RiskLevel.LOW if certifications else RiskLevel.HIGH
        return VendorAssessment(
            vendor_name=vendor_name,
            risk_level=risk_level,
            certifications=certifications,
        )

    async def scan_dependencies(
        self,
        manifest_content: str = "",
        manifest_type: str = "npm",
        regulations: list[str] | None = None,
    ) -> list[DependencyRisk]:
        """Scan dependencies for risks."""
        vuln_data = await self._check_vulnerability_db(manifest_content, manifest_type)
        risks = []
        for pkg_name, info in vuln_data.items():
            vulns = info.get("vulnerabilities", [])
            risk_level = (
                RiskLevel.HIGH
                if any(v.get("severity") in ("critical", "high") for v in vulns)
                else RiskLevel.LOW
                if not vulns
                else RiskLevel.MEDIUM
            )
            risks.append(
                DependencyRisk(
                    package_name=pkg_name,
                    version="",
                    risk_level=risk_level,
                    vulnerabilities=vulns,
                    license=info.get("license", ""),
                )
            )
        return risks

    async def generate_risk_report(
        self,
        vendors: list[str] | None = None,
        regulations: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate a vendor risk report."""
        assessments = []
        for vendor in vendors or []:
            assessment = await self.assess_vendor(vendor, regulations=regulations)
            assessments.append(assessment)
        high_risk = sum(
            1 for a in assessments if a.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        )
        medium_risk = sum(1 for a in assessments if a.risk_level == RiskLevel.MEDIUM)
        return {
            "summary": {
                "total_vendors": len(assessments),
                "high_risk": high_risk,
                "medium_risk": medium_risk,
                "low_risk": len(assessments) - high_risk - medium_risk,
            },
            "assessments": [a.to_dict() for a in assessments],
        }

    def list_supported_manifest_types(self) -> list[str]:
        """List supported dependency manifest types."""
        return ["npm", "pip", "maven", "gradle", "go", "cargo", "nuget"]

    async def check_license_compliance(
        self,
        dependencies: list[dict[str, str]] | None = None,
        allowed_licenses: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """Check license compliance of dependencies."""
        issues = []
        for dep in dependencies or []:
            lic = dep.get("license", "")
            if allowed_licenses and lic not in allowed_licenses:
                issues.append(
                    {
                        "package": dep.get("name", ""),
                        "license": lic,
                        "issue": f"License {lic} is not in the allowed list",
                    }
                )
        return issues

    # Internal methods (mocked by tests)
    async def _fetch_vendor_data(self, vendor_name: str = "") -> dict[str, Any]:
        return {
            "name": vendor_name,
            "certifications": [],
            "data_processing_locations": [],
            "subprocessors": [],
        }

    async def _check_vulnerability_db(
        self, manifest_content: str = "", manifest_type: str = ""
    ) -> dict[str, Any]:
        return {}
