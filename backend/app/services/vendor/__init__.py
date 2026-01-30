"""Vendor and third-party risk assessment module."""

from dataclasses import dataclass, field
from datetime import datetime
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
    assessed_at: datetime = field(default_factory=datetime.utcnow)
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
    scanned_at: datetime = field(default_factory=datetime.utcnow)
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


class VendorRiskAssessor:
    """Assessor for vendor and third-party risk."""

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
        jurisdiction_risk = RiskLevel.LOW
        if any(j in jurisdictions for j in high_risk_jurisdictions):
            jurisdiction_risk = RiskLevel.HIGH
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
                vulnerabilities.append(DependencyVulnerability(
                    package_name=pkg_name,
                    package_version=pkg_version,
                    vulnerability_id=f"COMPLIANCE-{pkg_name.upper()}",
                    severity=flag["severity"],
                    description=flag["reason"],
                    compliance_impact=flag["compliance"],
                ))

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
        import json

        packages = []
        try:
            data = json.loads(content)
            deps = data.get("dependencies", {})
            for name, info in deps.items():
                version = info.get("version", "unknown") if isinstance(info, dict) else str(info)
                packages.append((name, version))
        except Exception as e:
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
