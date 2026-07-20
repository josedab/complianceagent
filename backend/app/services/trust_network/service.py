"""Compliance Trust Network Service."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_state import TrustAttestationRecord
from app.services.trust_network.models import (
    AttestationType,
    ComplianceAttestation,
    TrustChain,
    TrustNetworkStats,
    VerificationResult,
    VerificationStatus,
)


logger = structlog.get_logger()


def _parse_notes(record: TrustAttestationRecord) -> dict:
    if not record.notes:
        return {}
    try:
        return json.loads(record.notes)
    except json.JSONDecodeError:
        return {}


def _record_to_attestation(record: TrustAttestationRecord) -> ComplianceAttestation:
    notes = _parse_notes(record)
    evidence_refs = list(record.evidence_references or [])
    # Use the exact valid_from stored in notes (same value used for hash computation)
    valid_from_str = notes.get("valid_from", "")
    valid_from = datetime.fromisoformat(valid_from_str) if valid_from_str else record.created_at
    return ComplianceAttestation(
        id=record.id,
        org_name=notes.get("org_name", str(record.organization_id)),
        attestation_type=AttestationType(record.attestation_type),
        framework=record.regulation,
        score=float(notes.get("score", 0.0)),
        valid_from=valid_from,
        valid_until=record.expires_at,
        merkle_root=notes.get("merkle_root", evidence_refs[0] if evidence_refs else ""),
        signature=notes.get("signature", evidence_refs[1] if len(evidence_refs) > 1 else ""),
        verification_url=notes.get("verification_url", ""),
        status=VerificationStatus(record.status),
    )


class TrustNetworkService:
    """Manages cryptographic attestations and trust chains for compliance."""

    def __init__(
        self,
        db: AsyncSession,
        organization_id: UUID | None = None,
        user_id: UUID | None = None,
    ):
        self.db = db
        self.organization_id = organization_id
        self.user_id = user_id

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
                next_level.append(self._compute_hash(left + right))
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
        if self.organization_id is None or self.user_id is None:
            raise ValueError("organization_id and user_id are required to persist attestations")

        data_str = f"{org_name}:{att_type.value}:{framework}:{score}:{now.isoformat()}"
        merkle_root = self._compute_hash(data_str)
        signature = self._compute_hash(f"sig:{merkle_root}")
        verification_url = f"https://trust.compliance.dev/verify/{merkle_root[:16]}"

        record = TrustAttestationRecord(
            organization_id=self.organization_id,
            attested_by=self.user_id,
            attestation_type=att_type.value,
            regulation=framework,
            status=VerificationStatus.VALID.value,
            evidence_references=[merkle_root, signature],
            notes=json.dumps(
                {
                    "org_name": org_name,
                    "score": score,
                    "merkle_root": merkle_root,
                    "signature": signature,
                    "verification_url": verification_url,
                    "valid_from": now.isoformat(),
                }
            ),
        )
        self.db.add(record)
        await self.db.flush()
        logger.info("Attestation created", org=org_name, type=att_type.value, score=score)
        return _record_to_attestation(record)

    async def verify_attestation(self, attestation_id: UUID) -> VerificationResult:
        stmt = select(TrustAttestationRecord).where(
            TrustAttestationRecord.id == attestation_id,
            TrustAttestationRecord.organization_id == self.organization_id,
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return VerificationResult(
                attestation_id=attestation_id,
                is_valid=False,
                verified_at=datetime.now(UTC),
                message="Attestation not found",
            )

        attestation = _record_to_attestation(record)
        valid_from = attestation.valid_from.isoformat() if attestation.valid_from else ""
        data_str = f"{attestation.org_name}:{attestation.attestation_type.value}:{attestation.framework}:{attestation.score}:{valid_from}"
        expected_hash = self._compute_hash(data_str)
        is_valid = expected_hash == attestation.merkle_root

        all_attestations = await self.list_attestations()
        chain_root = (
            self._compute_merkle_root([item.merkle_root for item in all_attestations])
            if all_attestations
            else ""
        )
        proof_path = [attestation.merkle_root]
        if chain_root:
            proof_path.append(self._compute_hash(attestation.merkle_root + chain_root))

        logger.info("Attestation verified", attestation_id=str(attestation_id), is_valid=is_valid)
        return VerificationResult(
            attestation_id=attestation_id,
            is_valid=is_valid,
            verified_at=datetime.now(UTC),
            proof_path=proof_path,
            message="Verification successful" if is_valid else "Hash mismatch",
        )

    async def revoke_attestation(self, attestation_id: UUID) -> ComplianceAttestation | None:
        stmt = select(TrustAttestationRecord).where(
            TrustAttestationRecord.id == attestation_id,
            TrustAttestationRecord.organization_id == self.organization_id,
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        record.status = VerificationStatus.REVOKED.value
        await self.db.flush()
        logger.info("Attestation revoked", attestation_id=str(attestation_id))
        return _record_to_attestation(record)

    async def list_attestations(
        self,
        org_name: str | None = None,
        attestation_type: str | None = None,
    ) -> list[ComplianceAttestation]:
        stmt = select(TrustAttestationRecord).where(
            TrustAttestationRecord.organization_id == self.organization_id
        )
        if attestation_type:
            stmt = stmt.where(
                TrustAttestationRecord.attestation_type == AttestationType(attestation_type).value
            )
        result = await self.db.execute(stmt)
        attestations = [_record_to_attestation(record) for record in result.scalars().all()]
        if org_name:
            attestations = [
                attestation for attestation in attestations if attestation.org_name == org_name
            ]
        return attestations

    async def get_trust_chain(self) -> TrustChain:
        valid = [
            attestation
            for attestation in await self.list_attestations()
            if attestation.status == VerificationStatus.VALID
        ]
        merkle_root = (
            self._compute_merkle_root([attestation.merkle_root for attestation in valid])
            if valid
            else ""
        )
        return TrustChain(
            attestations=valid,
            merkle_root=merkle_root,
            chain_length=len(valid),
            last_anchored_at=max(
                (attestation.valid_from for attestation in valid if attestation.valid_from),
                default=None,
            ),
        )

    async def get_stats(self) -> TrustNetworkStats:
        attestations = await self.list_attestations()
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        verified = 0
        for attestation in attestations:
            by_type[attestation.attestation_type.value] = (
                by_type.get(attestation.attestation_type.value, 0) + 1
            )
            by_status[attestation.status.value] = by_status.get(attestation.status.value, 0) + 1
            if attestation.status == VerificationStatus.VALID:
                verified += 1
        return TrustNetworkStats(
            total_attestations=len(attestations),
            verified=verified,
            by_type=by_type,
            by_status=by_status,
            chain_length=len(attestations),
        )
