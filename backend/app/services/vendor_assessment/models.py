"""Vendor assessment data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class VendorStatus(str, Enum):
    """Vendor approval status."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class VendorRiskLevel(str, Enum):
    """Vendor risk classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class DependencyRiskLevel(str, Enum):
    """Dependency risk classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class Vendor:
    """Third-party vendor information."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    name: str = ""
    description: str = ""
    website: str = ""
    vendor_type: str = ""
    category: str = ""
    
    # Contact information
    primary_contact_name: str = ""
    primary_contact_email: str = ""
    
    # Compliance and certifications
    certifications: list[str] = field(default_factory=list)
    compliance_frameworks: list[str] = field(default_factory=list)
    data_processing_locations: list[str] = field(default_factory=list)
    
    # Risk profile
    risk_level: VendorRiskLevel = VendorRiskLevel.MEDIUM
    status: VendorStatus = VendorStatus.PENDING
    
    # Data handling
    data_types_processed: list[str] = field(default_factory=list)
    data_access_level: str = "none"
    subprocessors: list[str] = field(default_factory=list)
    
    # Audit and review
    last_assessment_date: datetime | None = None
    next_review_date: datetime | None = None
    contract_expiration: datetime | None = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: UUID | None = None
    notes: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class VendorAssessment:
    """Vendor compliance assessment."""
    id: UUID = field(default_factory=uuid4)
    vendor_id: UUID | None = None
    organization_id: UUID | None = None
    
    # Assessment details
    assessment_type: str = "initial"  # initial, periodic, incident
    assessment_date: datetime = field(default_factory=datetime.utcnow)
    assessor: str = ""
    
    # Scores (0-100)
    overall_score: float = 0.0
    security_score: float = 0.0
    privacy_score: float = 0.0
    operational_score: float = 0.0
    financial_score: float = 0.0
    
    # Risk evaluation
    risk_level: VendorRiskLevel = VendorRiskLevel.MEDIUM
    risk_factors: list[dict] = field(default_factory=list)
    
    # Compliance gaps
    compliance_gaps: list[dict] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    
    # Framework-specific assessments
    framework_assessments: dict[str, dict] = field(default_factory=dict)
    
    # Recommendations
    recommendation: str = ""
    conditions: list[str] = field(default_factory=list)
    
    # Status
    status: VendorStatus = VendorStatus.PENDING
    approved_by: str | None = None
    approved_at: datetime | None = None
    valid_until: datetime | None = None
    
    # Notes
    notes: str = ""
    attachments: list[str] = field(default_factory=list)


@dataclass
class Dependency:
    """Software dependency information."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    version: str = ""
    latest_version: str = ""
    package_manager: str = ""  # npm, pip, maven, etc.
    ecosystem: str = ""
    
    # Source and licensing
    repository_url: str = ""
    license: str = ""
    license_risk: str = "low"
    
    # Maintainership
    maintainer: str = ""
    last_updated: datetime | None = None
    downloads_weekly: int = 0
    stars: int = 0
    contributors: int = 0
    
    # Risk indicators
    is_outdated: bool = False
    is_deprecated: bool = False
    has_known_vulnerabilities: bool = False
    vulnerability_count: int = 0
    
    # Direct dependencies
    direct_dependencies: list[str] = field(default_factory=list)
    transitive_count: int = 0


@dataclass
class DependencyRisk:
    """Dependency risk assessment."""
    dependency: Dependency = field(default_factory=Dependency)
    risk_level: DependencyRiskLevel = DependencyRiskLevel.NONE
    risk_score: float = 0.0
    
    # Risk factors
    vulnerabilities: list[dict] = field(default_factory=list)
    license_issues: list[str] = field(default_factory=list)
    maintenance_issues: list[str] = field(default_factory=list)
    compliance_issues: list[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: list[str] = field(default_factory=list)
    remediation_priority: int = 0
    
    # Alternative packages
    alternatives: list[str] = field(default_factory=list)


@dataclass
class DependencyScanResult:
    """Result of dependency scanning."""
    id: UUID = field(default_factory=uuid4)
    repository_id: UUID | None = None
    organization_id: UUID | None = None
    scan_date: datetime = field(default_factory=datetime.utcnow)
    
    # Summary
    total_dependencies: int = 0
    direct_dependencies: int = 0
    transitive_dependencies: int = 0
    
    # Risk distribution
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    # Vulnerability summary
    total_vulnerabilities: int = 0
    critical_vulnerabilities: int = 0
    high_vulnerabilities: int = 0
    
    # License summary
    license_violations: int = 0
    copyleft_licenses: int = 0
    unknown_licenses: int = 0
    
    # Health score (0-100)
    health_score: float = 0.0
    
    # Detailed risks
    dependency_risks: list[DependencyRisk] = field(default_factory=list)
    
    # Compliance impact
    frameworks_affected: list[str] = field(default_factory=list)
    compliance_impact: dict[str, str] = field(default_factory=dict)


# Known license risk levels
LICENSE_RISKS = {
    "MIT": "low",
    "Apache-2.0": "low",
    "BSD-2-Clause": "low",
    "BSD-3-Clause": "low",
    "ISC": "low",
    "Unlicense": "low",
    "CC0-1.0": "low",
    "LGPL-2.1": "medium",
    "LGPL-3.0": "medium",
    "MPL-2.0": "medium",
    "EPL-1.0": "medium",
    "EPL-2.0": "medium",
    "GPL-2.0": "high",
    "GPL-3.0": "high",
    "AGPL-3.0": "critical",
    "SSPL-1.0": "critical",
    "Proprietary": "high",
    "Unknown": "medium",
}


# Vendor certifications and their compliance mapping
CERTIFICATION_COMPLIANCE_MAP = {
    "SOC2_TYPE_2": ["SOC2"],
    "SOC2_TYPE_1": ["SOC2"],
    "ISO_27001": ["SOC2", "GDPR"],
    "ISO_27017": ["SOC2", "GDPR"],
    "ISO_27018": ["GDPR"],
    "HIPAA_BAA": ["HIPAA"],
    "PCI_DSS": ["PCI_DSS"],
    "GDPR_COMPLIANT": ["GDPR"],
    "FEDRAMP": ["SOC2"],
    "CSA_STAR": ["SOC2"],
    "PRIVACY_SHIELD": ["GDPR"],
}
