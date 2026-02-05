"""Data models for Cross-Border Data Flow Mapper."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DataClassification(str, Enum):
    """Data classification levels."""
    
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"  # Personal Identifiable Information
    PHI = "phi"  # Protected Health Information
    PCI = "pci"  # Payment Card Industry data
    SENSITIVE = "sensitive"


class JurisdictionType(str, Enum):
    """Jurisdiction adequacy types."""
    
    ADEQUATE = "adequate"  # EU adequacy decision
    SCCS = "sccs"  # Standard Contractual Clauses required
    BCR = "bcr"  # Binding Corporate Rules required
    DEROGATION = "derogation"  # Specific derogations apply
    PROHIBITED = "prohibited"  # Transfer prohibited
    DOMESTIC = "domestic"  # Same jurisdiction


class TransferMechanism(str, Enum):
    """Legal transfer mechanisms."""
    
    ADEQUACY_DECISION = "adequacy_decision"
    STANDARD_CONTRACTUAL_CLAUSES = "scc"
    BINDING_CORPORATE_RULES = "bcr"
    CONSENT = "consent"
    CONTRACT_NECESSITY = "contract_necessity"
    LEGAL_CLAIMS = "legal_claims"
    PUBLIC_INTEREST = "public_interest"
    VITAL_INTERESTS = "vital_interests"
    APPROVED_CERTIFICATION = "approved_certification"
    APPROVED_CODE_OF_CONDUCT = "approved_code_of_conduct"
    NONE = "none"


class ComplianceStatus(str, Enum):
    """Compliance status for data flows."""
    
    COMPLIANT = "compliant"
    NEEDS_REVIEW = "needs_review"
    ACTION_REQUIRED = "action_required"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """Risk level for data transfers."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataLocation(BaseModel):
    """A data storage or processing location."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    
    # Location details
    country: str
    country_code: str  # ISO 3166-1 alpha-2
    region: str | None = None  # e.g., "EU", "EEA", "APAC"
    
    # Infrastructure
    provider: str | None = None  # e.g., "AWS", "Azure", "GCP"
    service: str | None = None  # e.g., "S3", "RDS", "BigQuery"
    
    # Data classification
    data_types: list[DataClassification] = Field(default_factory=list)
    
    # Compliance
    certifications: list[str] = Field(default_factory=list)  # e.g., "SOC 2", "ISO 27001"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DataFlow(BaseModel):
    """A data flow between two locations."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    
    # Flow endpoints
    source_id: UUID
    source_name: str
    source_country: str
    destination_id: UUID
    destination_name: str
    destination_country: str
    
    # Data details
    data_types: list[DataClassification] = Field(default_factory=list)
    data_categories: list[str] = Field(default_factory=list)  # e.g., "customer data", "employee data"
    purpose: str | None = None
    
    # Volume and frequency
    volume_estimate: str | None = None  # e.g., "10GB/day"
    frequency: str | None = None  # e.g., "continuous", "daily batch"
    
    # Compliance status
    transfer_mechanism: TransferMechanism = TransferMechanism.NONE
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    # Applicable regulations
    regulations: list[str] = Field(default_factory=list)
    
    # Actions needed
    actions_required: list[str] = Field(default_factory=list)
    
    # Metadata
    detected_from: str | None = None  # e.g., "code analysis", "manual entry"
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    last_reviewed: datetime | None = None
    reviewer: str | None = None


class JurisdictionConflict(BaseModel):
    """A conflict between jurisdictions affecting a data flow."""
    
    id: UUID = Field(default_factory=uuid4)
    flow_id: UUID
    
    # Conflict details
    source_jurisdiction: str
    destination_jurisdiction: str
    source_regulation: str
    destination_regulation: str
    
    conflict_type: str  # e.g., "data_localization", "access_restriction", "retention"
    description: str
    severity: RiskLevel
    
    # Resolution
    resolution_options: list[str] = Field(default_factory=list)
    recommended_resolution: str | None = None
    
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class TransferImpactAssessment(BaseModel):
    """Transfer Impact Assessment (TIA) for a data flow."""
    
    id: UUID = Field(default_factory=uuid4)
    flow_id: UUID
    
    # Assessment details
    assessment_date: datetime = Field(default_factory=datetime.utcnow)
    assessor: str | None = None
    
    # Source country analysis
    source_country: str
    source_legal_framework: str
    source_data_protection_authority: str | None = None
    
    # Destination country analysis
    destination_country: str
    destination_legal_framework: str
    destination_adequacy_status: JurisdictionType
    destination_government_access_risk: RiskLevel
    
    # Risk analysis
    overall_risk: RiskLevel
    risk_factors: list[str] = Field(default_factory=list)
    mitigating_factors: list[str] = Field(default_factory=list)
    
    # Supplementary measures
    supplementary_measures_required: bool = False
    recommended_measures: list[str] = Field(default_factory=list)
    
    # Transfer mechanism
    recommended_mechanism: TransferMechanism
    mechanism_justification: str | None = None
    
    # Documentation
    scc_template: str | None = None  # Link to SCC template
    additional_clauses: list[str] = Field(default_factory=list)
    
    # Approval
    approved: bool = False
    approval_date: datetime | None = None
    approver: str | None = None
    next_review_date: datetime | None = None


class DataFlowMap(BaseModel):
    """Complete data flow map for an organization."""
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    name: str = "Data Flow Map"
    
    # Locations and flows
    locations: list[DataLocation] = Field(default_factory=list)
    flows: list[DataFlow] = Field(default_factory=list)
    conflicts: list[JurisdictionConflict] = Field(default_factory=list)
    assessments: list[TransferImpactAssessment] = Field(default_factory=list)
    
    # Summary statistics
    total_locations: int = 0
    total_flows: int = 0
    cross_border_flows: int = 0
    compliant_flows: int = 0
    action_required_flows: int = 0
    
    # Risk summary
    critical_risks: int = 0
    high_risks: int = 0
    medium_risks: int = 0
    low_risks: int = 0
    
    # Regions
    regions_involved: list[str] = Field(default_factory=list)
    countries_involved: list[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Jurisdiction Knowledge Base
# ============================================================================

# EU Adequacy Decisions (as of 2024)
EU_ADEQUATE_COUNTRIES = [
    "AD",  # Andorra
    "AR",  # Argentina
    "CA",  # Canada (commercial orgs)
    "FO",  # Faroe Islands
    "GG",  # Guernsey
    "IL",  # Israel
    "IM",  # Isle of Man
    "JP",  # Japan
    "JE",  # Jersey
    "NZ",  # New Zealand
    "KR",  # South Korea
    "CH",  # Switzerland
    "GB",  # United Kingdom
    "UY",  # Uruguay
    "US",  # USA (EU-US Data Privacy Framework participants)
]

# EEA Countries
EEA_COUNTRIES = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    "IS", "LI", "NO",  # EEA but not EU
]

# Countries with strict data localization requirements
DATA_LOCALIZATION_COUNTRIES = {
    "RU": "Russia requires personal data of Russian citizens to be stored on servers in Russia",
    "CN": "China requires certain data types to be stored within China",
    "VN": "Vietnam requires certain data to be stored locally",
    "ID": "Indonesia has data localization requirements for certain sectors",
    "IN": "India has localization requirements for payment data",
    "NG": "Nigeria requires certain government data to be stored locally",
    "BR": "Brazil has sector-specific localization requirements",
}

# Countries with government access concerns (Schrems II consideration)
HIGH_GOVERNMENT_ACCESS_RISK = [
    "US",  # FISA 702, EO 12333
    "CN",  # National Security Law
    "RU",  # SORM
    "IN",  # IT Act
    "AU",  # Assistance and Access Act
]

# Major privacy regulations by jurisdiction
JURISDICTION_REGULATIONS: dict[str, list[str]] = {
    "EU": ["GDPR"],
    "EEA": ["GDPR"],
    "GB": ["UK GDPR", "Data Protection Act 2018"],
    "US": ["CCPA", "CPRA", "State Privacy Laws", "HIPAA", "GLBA"],
    "CA": ["PIPEDA", "Quebec Law 25"],
    "BR": ["LGPD"],
    "CN": ["PIPL", "Cybersecurity Law", "Data Security Law"],
    "JP": ["APPI"],
    "KR": ["PIPA"],
    "AU": ["Privacy Act 1988"],
    "IN": ["DPDP Act 2023"],
    "SG": ["PDPA"],
}

# Standard Contractual Clauses modules
SCC_MODULES = {
    "controller_to_controller": "Module 1: Controller to Controller",
    "controller_to_processor": "Module 2: Controller to Processor",
    "processor_to_processor": "Module 3: Processor to Processor",
    "processor_to_controller": "Module 4: Processor to Controller",
}
