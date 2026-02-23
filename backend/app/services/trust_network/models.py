"""Compliance Trust Network models."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AttestationType(str, Enum):
    SOC2_COMPLIANT = "soc2_compliant"
    ISO27001_CERTIFIED = "iso27001_certified"
    GDPR_COMPLIANT = "gdpr_compliant"
    HIPAA_COMPLIANT = "hipaa_compliant"
    PCI_COMPLIANT = "pci_compliant"


class VerificationStatus(str, Enum):
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


@dataclass
class ComplianceAttestation:
    id: UUID = field(default_factory=uuid4)
    org_name: str = ""
    attestation_type: AttestationType = AttestationType.SOC2_COMPLIANT
    framework: str = ""
    score: float = 0.0
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    merkle_root: str = ""
    signature: str = ""
    verification_url: str = ""
    status: VerificationStatus = VerificationStatus.PENDING


@dataclass
class MerkleNode:
    hash: str = ""
    left_hash: str = ""
    right_hash: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrustChain:
    id: UUID = field(default_factory=uuid4)
    attestations: list[ComplianceAttestation] = field(default_factory=list)
    merkle_root: str = ""
    chain_length: int = 0
    last_anchored_at: datetime | None = None


@dataclass
class VerificationResult:
    attestation_id: UUID = field(default_factory=uuid4)
    is_valid: bool = False
    verified_at: datetime | None = None
    proof_path: list[str] = field(default_factory=list)
    message: str = ""


@dataclass
class TrustNetworkStats:
    total_attestations: int = 0
    verified: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)
    chain_length: int = 0
