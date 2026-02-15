"""Blockchain-Based Compliance Audit Trail models."""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class BlockType(str, Enum):
    COMPLIANCE_DECISION = "compliance_decision"
    CODE_CHANGE = "code_change"
    EVIDENCE_SUBMISSION = "evidence_submission"
    APPROVAL = "approval"
    AUDIT_EVENT = "audit_event"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    TAMPERED = "tampered"
    PENDING = "pending"
    ERROR = "error"


@dataclass
class AuditBlock:
    """A block in the compliance audit blockchain."""

    id: UUID = field(default_factory=uuid4)
    index: int = 0
    block_type: BlockType = BlockType.AUDIT_EVENT
    data: dict = field(default_factory=dict)
    previous_hash: str = ""
    hash: str = ""
    timestamp: str = ""
    nonce: int = 0


@dataclass
class BlockchainState:
    """Current state of the audit blockchain."""

    chain_length: int = 0
    latest_hash: str = ""
    is_valid: bool = True
    created_at: str = ""


@dataclass
class VerificationResult:
    """Result of chain verification."""

    chain_length: int = 0
    is_valid: bool = True
    invalid_blocks: list[int] = field(default_factory=list)
    verification_time_ms: float = 0.0
    verified_at: str = ""


@dataclass
class SmartContract:
    """A compliance smart contract."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    contract_type: str = ""
    conditions: list[dict] = field(default_factory=list)
    auto_approve: bool = False
    created_at: str = ""


@dataclass
class AuditProof:
    """Proof of a block's inclusion in the chain."""

    block_index: int = 0
    block_hash: str = ""
    merkle_root: str = ""
    merkle_proof: list[str] = field(default_factory=list)
    verified: bool = False
