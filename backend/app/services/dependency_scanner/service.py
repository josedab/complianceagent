"""Vendor/Third-Party Dependency Risk Scanner service.

Scans npm/pip/maven dependencies for license violations, compliance risks,
deprecated crypto, and data-sharing SDKs.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession


logger = structlog.get_logger()


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class LicenseCategory(str, Enum):
    PERMISSIVE = "permissive"
    WEAK_COPYLEFT = "weak_copyleft"
    STRONG_COPYLEFT = "strong_copyleft"
    PROPRIETARY = "proprietary"
    UNKNOWN = "unknown"


@dataclass
class DependencyRisk:
    package: str = ""
    version: str = ""
    ecosystem: str = ""  # npm, pip, maven, go
    license: str = ""
    license_category: LicenseCategory = LicenseCategory.UNKNOWN
    risk_level: RiskLevel = RiskLevel.LOW
    issues: list[str] = field(default_factory=list)
    cve_count: int = 0
    data_sharing: bool = False
    deprecated_crypto: bool = False


@dataclass
class DependencyScanResult:
    id: UUID = field(default_factory=uuid4)
    total_dependencies: int = 0
    critical_risks: int = 0
    high_risks: int = 0
    license_violations: int = 0
    deprecated_crypto_count: int = 0
    data_sharing_count: int = 0
    risks: list[DependencyRisk] = field(default_factory=list)
    scanned_at: datetime | None = None
    ecosystem: str = ""


# License classification database
_LICENSE_DB: dict[str, LicenseCategory] = {
    "MIT": LicenseCategory.PERMISSIVE,
    "Apache-2.0": LicenseCategory.PERMISSIVE,
    "BSD-2-Clause": LicenseCategory.PERMISSIVE,
    "BSD-3-Clause": LicenseCategory.PERMISSIVE,
    "ISC": LicenseCategory.PERMISSIVE,
    "LGPL-2.1": LicenseCategory.WEAK_COPYLEFT,
    "LGPL-3.0": LicenseCategory.WEAK_COPYLEFT,
    "MPL-2.0": LicenseCategory.WEAK_COPYLEFT,
    "GPL-2.0": LicenseCategory.STRONG_COPYLEFT,
    "GPL-3.0": LicenseCategory.STRONG_COPYLEFT,
    "AGPL-3.0": LicenseCategory.STRONG_COPYLEFT,
    "SSPL-1.0": LicenseCategory.PROPRIETARY,
    "BSL-1.1": LicenseCategory.PROPRIETARY,
}

# Known data-sharing SDKs
_DATA_SHARING_PACKAGES: set[str] = {
    "analytics-node", "segment-analytics", "mixpanel",
    "amplitude-js", "hotjar", "fullstory",
    "sentry", "datadog", "newrelic",
}

# Deprecated crypto patterns
_DEPRECATED_CRYPTO: set[str] = {
    "pycrypto", "python-jose", "itsdangerous",
    "md5", "sha1",
}


class DependencyScannerService:
    """Scans dependencies for license, security, and compliance risks."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._scan_results: list[DependencyScanResult] = []

    async def scan_requirements(
        self,
        dependencies: list[dict[str, str]],
        ecosystem: str = "pip",
        proprietary_project: bool = True,
    ) -> DependencyScanResult:
        """Scan a dependency list for compliance risks.

        Args:
            dependencies: List of {"name": "...", "version": "...", "license": "..."} dicts
            ecosystem: Package ecosystem (pip, npm, maven, go)
            proprietary_project: If True, copyleft licenses are flagged
        """
        risks: list[DependencyRisk] = []

        for dep in dependencies:
            pkg = dep.get("name", "")
            version = dep.get("version", "")
            license_id = dep.get("license", "UNKNOWN")
            license_cat = _LICENSE_DB.get(license_id, LicenseCategory.UNKNOWN)

            issues: list[str] = []
            risk_level = RiskLevel.NONE
            data_sharing = pkg.lower() in _DATA_SHARING_PACKAGES
            deprecated = pkg.lower() in _DEPRECATED_CRYPTO

            # License compliance
            if proprietary_project and license_cat == LicenseCategory.STRONG_COPYLEFT:
                issues.append(f"Strong copyleft license ({license_id}) in proprietary project — legal review required")
                risk_level = RiskLevel.CRITICAL
            elif license_cat == LicenseCategory.UNKNOWN:
                issues.append("Unknown license — manual review required")
                risk_level = max_risk(risk_level, RiskLevel.MEDIUM)

            # Data sharing
            if data_sharing:
                issues.append(f"{pkg} may transmit data to third parties — verify GDPR/CCPA compliance")
                risk_level = max_risk(risk_level, RiskLevel.HIGH)

            # Deprecated crypto
            if deprecated:
                issues.append(f"{pkg} uses deprecated cryptography — upgrade required for HIPAA/PCI compliance")
                risk_level = max_risk(risk_level, RiskLevel.HIGH)

            risks.append(DependencyRisk(
                package=pkg, version=version, ecosystem=ecosystem,
                license=license_id, license_category=license_cat,
                risk_level=risk_level, issues=issues,
                data_sharing=data_sharing, deprecated_crypto=deprecated,
            ))

        result = DependencyScanResult(
            total_dependencies=len(dependencies),
            critical_risks=sum(1 for r in risks if r.risk_level == RiskLevel.CRITICAL),
            high_risks=sum(1 for r in risks if r.risk_level == RiskLevel.HIGH),
            license_violations=sum(1 for r in risks if r.license_category in (LicenseCategory.STRONG_COPYLEFT, LicenseCategory.UNKNOWN)),
            deprecated_crypto_count=sum(1 for r in risks if r.deprecated_crypto),
            data_sharing_count=sum(1 for r in risks if r.data_sharing),
            risks=[r for r in risks if r.risk_level != RiskLevel.NONE],
            scanned_at=datetime.now(UTC),
            ecosystem=ecosystem,
        )
        self._scan_results.append(result)

        logger.info(
            "dependency_scan_complete",
            ecosystem=ecosystem,
            total=len(dependencies),
            critical=result.critical_risks,
            high=result.high_risks,
        )
        return result

    async def get_scan_history(self, limit: int = 10) -> list[DependencyScanResult]:
        return self._scan_results[-limit:]


def max_risk(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    order = {RiskLevel.NONE: 0, RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
    return a if order.get(a, 0) >= order.get(b, 0) else b
