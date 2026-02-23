"""Digital passport models for portable compliance credentials."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class PassportStatus(str, Enum):
    """Status of a digital passport."""

    active = "active"
    expired = "expired"
    suspended = "suspended"
    revoked = "revoked"


class CredentialType(str, Enum):
    """Types of compliance credentials."""

    soc2 = "soc2"
    iso27001 = "iso27001"
    gdpr = "gdpr"
    hipaa = "hipaa"
    pci_dss = "pci_dss"
    eu_ai_act = "eu_ai_act"


class VerifierType(str, Enum):
    """Types of credential verifiers."""

    auditor = "auditor"
    regulator = "regulator"
    partner = "partner"
    vendor = "vendor"


@dataclass
class ComplianceCredential:
    """A verifiable compliance credential."""

    id: UUID = field(default_factory=uuid4)
    org_name: str = ""
    credential_type: CredentialType = CredentialType.soc2
    framework: str = ""
    score: float = 0.0
    grade: str = ""
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    issuer: str = "ComplianceAgent"
    signature: str = ""
    verification_url: str = ""


@dataclass
class DigitalPassport:
    """A digital compliance passport containing multiple credentials."""

    id: UUID = field(default_factory=uuid4)
    org_name: str = ""
    credentials: list[ComplianceCredential] = field(default_factory=list)
    overall_score: float = 0.0
    status: PassportStatus = PassportStatus.active
    qr_code_data: str = ""
    portable_url: str = ""
    created_at: datetime | None = None
    last_updated: datetime | None = None


@dataclass
class VerificationRequest:
    """A request to verify a digital passport."""

    id: UUID = field(default_factory=uuid4)
    passport_id: UUID = field(default_factory=uuid4)
    verifier: str = ""
    verifier_type: VerifierType = VerifierType.auditor
    verified: bool = False
    verified_at: datetime | None = None


@dataclass
class PassportStats:
    """Aggregate passport statistics."""

    total_passports: int = 0
    active: int = 0
    credentials_issued: int = 0
    verifications: int = 0
    by_credential_type: dict = field(default_factory=dict)
