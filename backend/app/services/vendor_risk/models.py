"""Data models for Vendor Risk Compliance Graph."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class VendorType(str, Enum):
    """Types of vendors/dependencies."""
    
    PACKAGE = "package"  # npm, pip, etc.
    SAAS = "saas"
    INFRASTRUCTURE = "infrastructure"  # AWS, GCP, etc.
    API = "api"
    DATABASE = "database"
    CDN = "cdn"
    PAYMENT = "payment"
    ANALYTICS = "analytics"
    AUTH = "auth"
    STORAGE = "storage"


class RiskLevel(str, Enum):
    """Risk levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"
    UNKNOWN = "unknown"


class ComplianceTier(str, Enum):
    """Vendor compliance certification tiers."""
    
    FULLY_CERTIFIED = "fully_certified"  # Has all needed certs
    PARTIALLY_CERTIFIED = "partially_certified"
    SELF_ATTESTED = "self_attested"
    UNCERTIFIED = "uncertified"
    UNKNOWN = "unknown"


@dataclass
class Certification:
    """A compliance certification."""
    
    name: str
    issued_by: str = ""
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    verification_url: str = ""
    scope: str = ""


@dataclass
class Vendor:
    """A vendor or dependency."""
    
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    vendor_type: VendorType = VendorType.PACKAGE
    version: str = ""
    
    # Source info
    registry: str = ""  # npm, pypi, etc.
    homepage: str = ""
    repository: str = ""
    
    # Compliance info
    certifications: list[Certification] = field(default_factory=list)
    compliance_tier: ComplianceTier = ComplianceTier.UNKNOWN
    data_processing: list[str] = field(default_factory=list)  # personal_data, payment, etc.
    data_regions: list[str] = field(default_factory=list)
    
    # Risk assessment
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    risk_score: float = 0.0
    risk_factors: list[str] = field(default_factory=list)
    
    # Security
    last_security_audit: datetime | None = None
    known_vulnerabilities: int = 0
    security_contact: str = ""
    
    # Dependencies (for building graph)
    dependencies: list[str] = field(default_factory=list)  # Names of dependencies
    dependents: list[str] = field(default_factory=list)  # What depends on this
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyEdge:
    """An edge in the dependency graph."""
    
    source: str  # Vendor name
    target: str  # Dependency name
    relationship: str = "depends_on"  # depends_on, uses, integrates
    is_direct: bool = True  # Direct vs transitive
    is_optional: bool = False
    scope: str = ""  # runtime, dev, test


@dataclass
class VendorGraph:
    """A graph of vendors and their dependencies."""
    
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    repository_id: UUID | None = None
    
    # Nodes and edges
    vendors: dict[str, Vendor] = field(default_factory=dict)  # name -> Vendor
    edges: list[DependencyEdge] = field(default_factory=list)
    
    # Statistics
    total_vendors: int = 0
    total_dependencies: int = 0
    depth: int = 0  # Max dependency depth
    
    # Risk summary
    critical_risks: int = 0
    high_risks: int = 0
    medium_risks: int = 0
    overall_risk: RiskLevel = RiskLevel.UNKNOWN
    
    # Compliance summary
    certified_vendors: int = 0
    uncertified_vendors: int = 0
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    source: str = ""  # package.json, requirements.txt, etc.


@dataclass
class RiskAssessment:
    """Risk assessment for a vendor."""
    
    vendor_id: UUID
    vendor_name: str
    
    # Scores
    overall_risk: RiskLevel = RiskLevel.UNKNOWN
    risk_score: float = 0.0  # 0-100
    
    # Component scores
    security_score: float = 0.0
    compliance_score: float = 0.0
    maintenance_score: float = 0.0
    transparency_score: float = 0.0
    
    # Factors
    risk_factors: list[dict[str, Any]] = field(default_factory=list)
    mitigating_factors: list[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    
    # Assessment metadata
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    assessor: str = "system"


@dataclass
class ComplianceInheritance:
    """Compliance requirements inherited from vendor."""
    
    vendor_name: str
    inherited_requirements: list[str] = field(default_factory=list)
    affected_regulations: list[str] = field(default_factory=list)
    dpa_required: bool = False  # Data Processing Agreement
    subprocessor_notification: bool = False
    audit_rights: bool = False
    
    # Impact
    impact_summary: str = ""
    compliance_gaps: list[str] = field(default_factory=list)


# Well-known vendor database
KNOWN_VENDORS: dict[str, dict[str, Any]] = {
    # Cloud providers
    "aws": {
        "name": "Amazon Web Services",
        "type": VendorType.INFRASTRUCTURE,
        "certifications": ["SOC2", "ISO27001", "HIPAA", "PCI-DSS", "FedRAMP"],
        "data_processing": ["all"],
        "risk_level": RiskLevel.LOW,
    },
    "gcp": {
        "name": "Google Cloud Platform",
        "type": VendorType.INFRASTRUCTURE,
        "certifications": ["SOC2", "ISO27001", "HIPAA", "PCI-DSS", "FedRAMP"],
        "data_processing": ["all"],
        "risk_level": RiskLevel.LOW,
    },
    "azure": {
        "name": "Microsoft Azure",
        "type": VendorType.INFRASTRUCTURE,
        "certifications": ["SOC2", "ISO27001", "HIPAA", "PCI-DSS", "FedRAMP"],
        "data_processing": ["all"],
        "risk_level": RiskLevel.LOW,
    },
    # Payment
    "stripe": {
        "name": "Stripe",
        "type": VendorType.PAYMENT,
        "certifications": ["PCI-DSS", "SOC2"],
        "data_processing": ["payment", "personal_data"],
        "risk_level": RiskLevel.LOW,
    },
    # Auth
    "auth0": {
        "name": "Auth0",
        "type": VendorType.AUTH,
        "certifications": ["SOC2", "ISO27001", "HIPAA"],
        "data_processing": ["personal_data", "credentials"],
        "risk_level": RiskLevel.LOW,
    },
    "okta": {
        "name": "Okta",
        "type": VendorType.AUTH,
        "certifications": ["SOC2", "ISO27001", "FedRAMP"],
        "data_processing": ["personal_data", "credentials"],
        "risk_level": RiskLevel.LOW,
    },
    # Analytics
    "google-analytics": {
        "name": "Google Analytics",
        "type": VendorType.ANALYTICS,
        "certifications": ["SOC2"],
        "data_processing": ["personal_data", "behavior"],
        "risk_level": RiskLevel.MEDIUM,  # GDPR considerations
    },
    # Databases
    "mongodb-atlas": {
        "name": "MongoDB Atlas",
        "type": VendorType.DATABASE,
        "certifications": ["SOC2", "ISO27001", "HIPAA", "PCI-DSS"],
        "data_processing": ["all"],
        "risk_level": RiskLevel.LOW,
    },
}
