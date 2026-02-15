"""Cross-Codebase Compliance Cloning service."""

from __future__ import annotations

from uuid import UUID, uuid4

import structlog

from app.services.compliance_cloning.models import (
    CloningStatus,
    ComplianceGap,
    MigrationPlan,
    PatternCategory,
    ReferenceRepo,
    RepoFingerprint,
)

logger = structlog.get_logger()

_REFERENCE_REPOS: list[ReferenceRepo] = [
    ReferenceRepo(
        id="ref-fintech-py", name="fintech-compliance-starter",
        url="https://github.com/example/fintech-compliance-starter",
        description="Production-ready fintech backend with full PCI-DSS and SOX compliance patterns.",
        languages=["Python"], frameworks=["FastAPI", "SQLAlchemy"],
        compliance_score=94.5, patterns_count=28, industry="Fintech", verified=True,
    ),
    ReferenceRepo(
        id="ref-healthtech-ts", name="hipaa-saas-template",
        url="https://github.com/example/hipaa-saas-template",
        description="HIPAA-compliant SaaS template with ePHI handling, BAA tracking, and audit logging.",
        languages=["TypeScript"], frameworks=["Next.js", "Prisma"],
        compliance_score=91.2, patterns_count=22, industry="Healthtech", verified=True,
    ),
    ReferenceRepo(
        id="ref-ai-platform", name="ai-compliance-platform",
        url="https://github.com/example/ai-compliance-platform",
        description="EU AI Act compliant ML platform with model cards, bias detection, and explainability.",
        languages=["Python"], frameworks=["FastAPI", "PyTorch"],
        compliance_score=88.7, patterns_count=19, industry="AI/ML", verified=True,
    ),
    ReferenceRepo(
        id="ref-ecommerce-java", name="gdpr-ecommerce-backend",
        url="https://github.com/example/gdpr-ecommerce-backend",
        description="GDPR-compliant e-commerce with consent management, data portability, and right to erasure.",
        languages=["Java"], frameworks=["Spring Boot", "Hibernate"],
        compliance_score=92.1, patterns_count=25, industry="E-commerce", verified=True,
    ),
]


class ComplianceCloningService:
    """Service for cross-codebase compliance cloning."""

    async def list_reference_repos(
        self, industry: str | None = None, language: str | None = None,
    ) -> list[ReferenceRepo]:
        result = list(_REFERENCE_REPOS)
        if industry:
            result = [r for r in result if r.industry.lower() == industry.lower()]
        if language:
            result = [r for r in result if language in r.languages]
        return result

    async def fingerprint_repo(self, repo_url: str) -> RepoFingerprint:
        return RepoFingerprint(
            repo_url=repo_url,
            languages=["Python", "TypeScript"],
            frameworks=["FastAPI", "React"],
            cloud_providers=["AWS"],
            compliance_patterns=["basic_auth", "logging"],
            compliance_score=45.2, similarity_score=0.0,
        )

    async def find_similar_repos(self, repo_url: str) -> list[ReferenceRepo]:
        fingerprint = await self.fingerprint_repo(repo_url)
        results = []
        for ref in _REFERENCE_REPOS:
            overlap = len(set(fingerprint.languages) & set(ref.languages))
            if overlap > 0:
                results.append(ref)
        return results

    async def generate_migration_plan(
        self, source_repo_id: str, target_repo_url: str,
    ) -> MigrationPlan:
        if not target_repo_url or not target_repo_url.strip():
            raise ValueError("target_repo_url must not be empty")
        ref = next((r for r in _REFERENCE_REPOS if r.id == source_repo_id), None)
        source_url = ref.url if ref else source_repo_id

        gaps = [
            ComplianceGap(id="gap-1", category=PatternCategory.ENCRYPTION,
                description="Missing encryption at rest for user data",
                severity="critical", reference_implementation="from cryptography.fernet import Fernet\ncipher = Fernet(key)\nencrypted = cipher.encrypt(data)",
                suggested_fix="Add Fernet encryption to all PII storage operations.",
                estimated_effort_hours=4.0, files_affected=["src/models/user.py", "src/db/storage.py"]),
            ComplianceGap(id="gap-2", category=PatternCategory.AUDIT_LOGGING,
                description="No structured audit logging for data access events",
                severity="high", reference_implementation="import structlog\naudit_log = structlog.get_logger('audit')\naudit_log.info('data_accessed', user_id=uid, resource=res)",
                suggested_fix="Implement structlog-based audit trail for all data access.",
                estimated_effort_hours=6.0, files_affected=["src/middleware/audit.py"]),
            ComplianceGap(id="gap-3", category=PatternCategory.CONSENT_MANAGEMENT,
                description="No consent collection or tracking mechanism",
                severity="high", reference_implementation="class ConsentManager:\n    def collect(self, user_id, purpose, granted): ...",
                suggested_fix="Add consent management module with purpose-based tracking.",
                estimated_effort_hours=8.0, files_affected=["src/services/consent.py", "src/api/consent.py"]),
            ComplianceGap(id="gap-4", category=PatternCategory.DATA_MASKING,
                description="API responses expose raw PII without masking",
                severity="medium", reference_implementation="def mask_email(email):\n    parts = email.split('@')\n    return f'{parts[0][:2]}***@{parts[1]}'",
                suggested_fix="Add response serializer with automatic PII masking.",
                estimated_effort_hours=3.0, files_affected=["src/api/serializers.py"]),
        ]
        total_hours = sum(g.estimated_effort_hours for g in gaps)
        plan = MigrationPlan(
            id=uuid4(), source_repo=source_url, target_repo=target_repo_url,
            status=CloningStatus.PLANNING, total_gaps=len(gaps), gaps=gaps,
            estimated_total_hours=total_hours, compliance_score_before=45.2, compliance_score_after=87.5,
        )
        logger.info("cloning.plan_generated", gaps=len(gaps), hours=total_hours)
        return plan
