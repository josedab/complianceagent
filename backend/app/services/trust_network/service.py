"""Compliance Trust Network Service."""
import hashlib
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.trust_network.models import (
    AttestationType,
    ComplianceAttestation,
    TrustChain,
    TrustNetworkStats,
    VerificationResult,
    VerificationStatus,
)


logger = structlog.get_logger()


class TrustNetworkService:
    """Manages cryptographic attestations and trust chains for compliance."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._attestations: list[ComplianceAttestation] = []
        self._chain_root: str = ""

    def _compute_hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def _compute_merkle_root(self, items: list[str]) -> str:
        if not items:
            return self._compute_hash("empty")
        hashes = [self._compute_hash(item) for item in items]
        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                left = hashes[i]
                right = hashes[i + 1] if i + 1 < len(hashes) else left
                combined = self._compute_hash(left + right)
                next_level.append(combined)
            hashes = next_level
        return hashes[0]

    async def create_attestation(
        self,
        org_name: str,
        attestation_type: str,
        framework: str,
        score: float,
    ) -> ComplianceAttestation:
        now = datetime.now(UTC)
        att_type = AttestationType(attestation_type)

        data_str = f"{org_name}:{att_type.value}:{framework}:{score}:{now.isoformat()}"
        merkle_root = self._compute_hash(data_str)
        signature = self._compute_hash(f"sig:{merkle_root}")

        attestation = ComplianceAttestation(
            org_name=org_name,
            attestation_type=att_type,
            framework=framework,
            score=score,
            valid_from=now,
            valid_until=None,
            merkle_root=merkle_root,
            signature=signature,
            verification_url=f"https://trust.compliance.dev/verify/{merkle_root[:16]}",
            status=VerificationStatus.VALID,
        )
        self._attestations.append(attestation)
        self._update_chain_root()

        logger.info(
            "Attestation created",
            org=org_name,
            type=att_type.value,
            score=score,
        )
        return attestation

    async def verify_attestation(
        self,
        attestation_id: UUID,
    ) -> VerificationResult:
        attestation = self._find_attestation(attestation_id)
        if not attestation:
            return VerificationResult(
                attestation_id=attestation_id,
                is_valid=False,
                verified_at=datetime.now(UTC),
                message="Attestation not found",
            )

        data_str = (
            f"{attestation.org_name}:{attestation.attestation_type.value}"
            f":{attestation.framework}:{attestation.score}"
            f":{attestation.valid_from.isoformat() if attestation.valid_from else ''}"
        )
        expected_hash = self._compute_hash(data_str)
        is_valid = expected_hash == attestation.merkle_root

        proof_path = [
            attestation.merkle_root,
            self._compute_hash(attestation.merkle_root + self._chain_root),
        ]

        logger.info(
            "Attestation verified",
            attestation_id=str(attestation_id),
            is_valid=is_valid,
        )
        return VerificationResult(
            attestation_id=attestation_id,
            is_valid=is_valid,
            verified_at=datetime.now(UTC),
            proof_path=proof_path,
            message="Verification successful" if is_valid else "Hash mismatch",
        )

    async def revoke_attestation(self, attestation_id: UUID) -> ComplianceAttestation | None:
        attestation = self._find_attestation(attestation_id)
        if attestation:
            attestation.status = VerificationStatus.REVOKED
            self._update_chain_root()
            logger.info("Attestation revoked", attestation_id=str(attestation_id))
        return attestation

    def list_attestations(
        self,
        org_name: str | None = None,
        attestation_type: str | None = None,
    ) -> list[ComplianceAttestation]:
        results = list(self._attestations)
        if org_name:
            results = [a for a in results if a.org_name == org_name]
        if attestation_type:
            att_type = AttestationType(attestation_type)
            results = [a for a in results if a.attestation_type == att_type]
        return results

    def get_trust_chain(self) -> TrustChain:
        valid = [
            a for a in self._attestations
            if a.status == VerificationStatus.VALID
        ]
        return TrustChain(
            attestations=valid,
            merkle_root=self._chain_root,
            chain_length=len(valid),
            last_anchored_at=datetime.now(UTC),
        )

    def get_stats(self) -> TrustNetworkStats:
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        verified = 0
        for a in self._attestations:
            by_type[a.attestation_type.value] = (
                by_type.get(a.attestation_type.value, 0) + 1
            )
            by_status[a.status.value] = by_status.get(a.status.value, 0) + 1
            if a.status == VerificationStatus.VALID:
                verified += 1
        return TrustNetworkStats(
            total_attestations=len(self._attestations),
            verified=verified,
            by_type=by_type,
            by_status=by_status,
            chain_length=len(self._attestations),
        )

    def _find_attestation(self, attestation_id: UUID) -> ComplianceAttestation | None:
        for a in self._attestations:
            if a.id == attestation_id:
                return a
        return None

    def _update_chain_root(self) -> None:
        roots = [a.merkle_root for a in self._attestations]
        self._chain_root = self._compute_merkle_root(roots) if roots else ""
