"""Digital passport service for portable compliance credentials."""

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.digital_passport.models import (
    ComplianceCredential,
    CredentialType,
    DigitalPassport,
    PassportStats,
    PassportStatus,
    VerificationRequest,
    VerifierType,
)


logger = structlog.get_logger()


class DigitalPassportService:
    """Service for managing digital compliance passports and credentials."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._passports: dict[UUID, DigitalPassport] = {}
        self._verifications: dict[UUID, VerificationRequest] = {}
        self._seed_passports()

    def _generate_signature(self, org_name: str, credential_type: str, score: float) -> str:
        """Generate a hashlib-based signature for a credential."""
        payload = f"{org_name}:{credential_type}:{score}:{datetime.now(UTC).isoformat()}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def _seed_passports(self) -> None:
        """Seed initial passports with credentials."""
        seed_data = [
            (
                "Acme Corp",
                [
                    {"credential_type": CredentialType.soc2, "framework": "SOC 2 Type II", "score": 92.5, "grade": "A"},
                    {"credential_type": CredentialType.gdpr, "framework": "GDPR", "score": 88.0, "grade": "B+"},
                    {"credential_type": CredentialType.pci_dss, "framework": "PCI DSS v4.0", "score": 95.0, "grade": "A"},
                ],
            ),
            (
                "HealthTech Inc",
                [
                    {"credential_type": CredentialType.hipaa, "framework": "HIPAA", "score": 91.0, "grade": "A"},
                    {"credential_type": CredentialType.soc2, "framework": "SOC 2 Type II", "score": 87.0, "grade": "B+"},
                ],
            ),
            (
                "DataFlow EU",
                [
                    {"credential_type": CredentialType.gdpr, "framework": "GDPR", "score": 96.0, "grade": "A+"},
                    {"credential_type": CredentialType.iso27001, "framework": "ISO 27001:2022", "score": 90.0, "grade": "A"},
                    {"credential_type": CredentialType.eu_ai_act, "framework": "EU AI Act", "score": 82.0, "grade": "B"},
                ],
            ),
        ]
        now = datetime.now(UTC)
        for org_name, creds_data in seed_data:
            credentials = []
            for cred in creds_data:
                credential = ComplianceCredential(
                    id=uuid4(),
                    org_name=org_name,
                    credential_type=cred["credential_type"],
                    framework=cred["framework"],
                    score=cred["score"],
                    grade=cred["grade"],
                    issued_at=now,
                    expires_at=now + timedelta(days=365),
                    signature=self._generate_signature(org_name, cred["framework"], cred["score"]),
                    verification_url=f"https://verify.complianceagent.io/credentials/{uuid4()}",
                )
                credentials.append(credential)

            overall = sum(c.score for c in credentials) / len(credentials)
            passport_id = uuid4()
            passport = DigitalPassport(
                id=passport_id,
                org_name=org_name,
                credentials=credentials,
                overall_score=round(overall, 2),
                status=PassportStatus.active,
                qr_code_data=f"passport:{passport_id}",
                portable_url=f"https://passport.complianceagent.io/{passport_id}",
                created_at=now,
                last_updated=now,
            )
            self._passports[passport.id] = passport

    async def create_passport(
        self,
        org_name: str,
        credentials: list[dict],
    ) -> DigitalPassport:
        """Create a new digital passport with credentials."""
        now = datetime.now(UTC)
        cred_objects = []
        for cred in credentials:
            cred_type = CredentialType(cred.get("credential_type", "soc2"))
            score = cred.get("score", 0.0)
            credential = ComplianceCredential(
                id=uuid4(),
                org_name=org_name,
                credential_type=cred_type,
                framework=cred.get("framework", cred_type.value),
                score=score,
                grade=cred.get("grade", ""),
                issued_at=now,
                expires_at=now + timedelta(days=365),
                signature=self._generate_signature(org_name, cred_type.value, score),
                verification_url=f"https://verify.complianceagent.io/credentials/{uuid4()}",
            )
            cred_objects.append(credential)

        overall = sum(c.score for c in cred_objects) / len(cred_objects) if cred_objects else 0.0
        passport_id = uuid4()
        passport = DigitalPassport(
            id=passport_id,
            org_name=org_name,
            credentials=cred_objects,
            overall_score=round(overall, 2),
            status=PassportStatus.active,
            qr_code_data=f"passport:{passport_id}",
            portable_url=f"https://passport.complianceagent.io/{passport_id}",
            created_at=now,
            last_updated=now,
        )
        self._passports[passport.id] = passport
        logger.info("Passport created", org=org_name, credentials=len(cred_objects))
        return passport

    async def add_credential(
        self,
        passport_id: UUID,
        credential_type: CredentialType,
        framework: str,
        score: float,
    ) -> ComplianceCredential:
        """Add a credential to an existing passport."""
        if passport_id not in self._passports:
            raise ValueError(f"Passport not found: {passport_id}")
        passport = self._passports[passport_id]
        now = datetime.now(UTC)
        grade = "A+" if score >= 95 else "A" if score >= 90 else "B+" if score >= 85 else "B" if score >= 80 else "C"
        credential = ComplianceCredential(
            id=uuid4(),
            org_name=passport.org_name,
            credential_type=credential_type,
            framework=framework,
            score=score,
            grade=grade,
            issued_at=now,
            expires_at=now + timedelta(days=365),
            signature=self._generate_signature(passport.org_name, credential_type.value, score),
            verification_url=f"https://verify.complianceagent.io/credentials/{uuid4()}",
        )
        passport.credentials.append(credential)
        passport.overall_score = round(
            sum(c.score for c in passport.credentials) / len(passport.credentials), 2
        )
        passport.last_updated = now
        logger.info("Credential added", passport_id=str(passport_id), type=credential_type.value)
        return credential

    async def verify_passport(
        self,
        passport_id: UUID,
        verifier: str,
        verifier_type: VerifierType,
    ) -> VerificationRequest:
        """Verify a digital passport."""
        if passport_id not in self._passports:
            raise ValueError(f"Passport not found: {passport_id}")
        passport = self._passports[passport_id]
        verified = passport.status == PassportStatus.active
        verification = VerificationRequest(
            id=uuid4(),
            passport_id=passport_id,
            verifier=verifier,
            verifier_type=verifier_type,
            verified=verified,
            verified_at=datetime.now(UTC) if verified else None,
        )
        self._verifications[verification.id] = verification
        logger.info(
            "Passport verified",
            passport_id=str(passport_id),
            verifier=verifier,
            result=verified,
        )
        return verification

    async def suspend_passport(self, passport_id: UUID) -> DigitalPassport:
        """Suspend a digital passport."""
        if passport_id not in self._passports:
            raise ValueError(f"Passport not found: {passport_id}")
        passport = self._passports[passport_id]
        passport.status = PassportStatus.suspended
        passport.last_updated = datetime.now(UTC)
        logger.info("Passport suspended", passport_id=str(passport_id))
        return passport

    async def revoke_passport(self, passport_id: UUID) -> DigitalPassport:
        """Revoke a digital passport."""
        if passport_id not in self._passports:
            raise ValueError(f"Passport not found: {passport_id}")
        passport = self._passports[passport_id]
        passport.status = PassportStatus.revoked
        passport.last_updated = datetime.now(UTC)
        logger.info("Passport revoked", passport_id=str(passport_id))
        return passport

    async def get_passport(self, passport_id: UUID) -> DigitalPassport:
        """Get a passport by ID."""
        if passport_id not in self._passports:
            raise ValueError(f"Passport not found: {passport_id}")
        return self._passports[passport_id]

    async def list_passports(self) -> list[DigitalPassport]:
        """List all passports."""
        return list(self._passports.values())

    async def get_stats(self) -> PassportStats:
        """Get aggregate passport statistics."""
        passports = list(self._passports.values())
        all_creds = [c for p in passports for c in p.credentials]
        by_type: dict[str, int] = {}
        for cred in all_creds:
            key = cred.credential_type.value
            by_type[key] = by_type.get(key, 0) + 1
        return PassportStats(
            total_passports=len(passports),
            active=sum(1 for p in passports if p.status == PassportStatus.active),
            credentials_issued=len(all_creds),
            verifications=len(self._verifications),
            by_credential_type=by_type,
        )
