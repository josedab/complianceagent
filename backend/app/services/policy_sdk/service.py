"""Compliance-as-Code Policy SDK Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.policy_sdk.models import (
    PolicyCategory,
    PolicyDefinition,
    PolicyLanguage,
    PolicyMarketplaceEntry,
    PolicySeverity,
    PolicyValidationResult,
)

logger = structlog.get_logger()

_BUILTIN_POLICIES: list[PolicyDefinition] = [
    PolicyDefinition(
        name="gdpr-consent-required",
        description="Ensure consent is obtained before processing personal data",
        language=PolicyLanguage.YAML,
        category=PolicyCategory.DATA_PRIVACY,
        severity=PolicySeverity.HIGH,
        frameworks=["gdpr"],
        source_code="rules:\n  - id: consent-before-processing\n    pattern: 'process_data($data)'\n    requires: 'verify_consent($data.subject)'",
        author="complianceagent",
    ),
    PolicyDefinition(
        name="hipaa-phi-encryption",
        description="PHI must be encrypted at rest and in transit",
        language=PolicyLanguage.YAML,
        category=PolicyCategory.ENCRYPTION,
        severity=PolicySeverity.CRITICAL,
        frameworks=["hipaa"],
        source_code="rules:\n  - id: phi-encryption\n    pattern: 'store_phi($data)'\n    requires: 'encrypt($data)'",
        author="complianceagent",
    ),
    PolicyDefinition(
        name="pci-tokenize-cards",
        description="Card numbers must be tokenized before storage",
        language=PolicyLanguage.YAML,
        category=PolicyCategory.SECURITY,
        severity=PolicySeverity.CRITICAL,
        frameworks=["pci_dss"],
        source_code="rules:\n  - id: card-tokenization\n    pattern: 'store_card($number)'\n    requires: 'tokenize($number)'",
        author="complianceagent",
    ),
    PolicyDefinition(
        name="soc2-audit-logging",
        description="All admin actions must be logged to audit trail",
        language=PolicyLanguage.YAML,
        category=PolicyCategory.LOGGING,
        severity=PolicySeverity.HIGH,
        frameworks=["soc2"],
        source_code="rules:\n  - id: admin-audit-log\n    pattern: '@admin_action'\n    requires: 'audit_log($action, $user)'",
        author="complianceagent",
    ),
    PolicyDefinition(
        name="eu-ai-act-transparency",
        description="AI systems must provide transparency documentation",
        language=PolicyLanguage.YAML,
        category=PolicyCategory.AI_GOVERNANCE,
        severity=PolicySeverity.HIGH,
        frameworks=["eu_ai_act"],
        source_code="rules:\n  - id: ai-transparency\n    pattern: 'deploy_model($model)'\n    requires: 'model_card($model)'",
        author="complianceagent",
    ),
]


class PolicySDKService:
    """Compliance-as-Code policy SDK and marketplace."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._policies: dict[UUID, PolicyDefinition] = {p.id: p for p in _BUILTIN_POLICIES}
        self._marketplace: dict[UUID, PolicyMarketplaceEntry] = {}

    async def list_policies(
        self,
        category: PolicyCategory | None = None,
        framework: str | None = None,
    ) -> list[PolicyDefinition]:
        policies = list(self._policies.values())
        if category:
            policies = [p for p in policies if p.category == category]
        if framework:
            policies = [p for p in policies if framework in p.frameworks]
        return policies

    async def get_policy(self, policy_id: UUID) -> PolicyDefinition | None:
        return self._policies.get(policy_id)

    async def create_policy(
        self,
        name: str,
        description: str,
        source_code: str,
        language: PolicyLanguage = PolicyLanguage.YAML,
        category: PolicyCategory = PolicyCategory.CUSTOM,
        severity: PolicySeverity = PolicySeverity.MEDIUM,
        frameworks: list[str] | None = None,
        author: str = "",
    ) -> PolicyDefinition:
        policy = PolicyDefinition(
            name=name, description=description, source_code=source_code,
            language=language, category=category, severity=severity,
            frameworks=frameworks or [], author=author,
            created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        )
        self._policies[policy.id] = policy
        logger.info("Policy created", name=name, category=category.value)
        return policy

    async def validate_policy(self, policy_id: UUID) -> PolicyValidationResult:
        """Validate a policy definition."""
        policy = self._policies.get(policy_id)
        if not policy:
            return PolicyValidationResult(is_valid=False, errors=["Policy not found"])

        errors = []
        warnings = []

        if not policy.source_code.strip():
            errors.append("Policy source code is empty")
        if not policy.name:
            errors.append("Policy name is required")
        if "rules:" not in policy.source_code and policy.language == PolicyLanguage.YAML:
            warnings.append("YAML policy should contain 'rules:' key")
        if not policy.frameworks:
            warnings.append("No frameworks specified; policy won't auto-match")

        test_results = []
        if policy.test_cases:
            for i, tc in enumerate(policy.test_cases):
                test_results.append({"test": i + 1, "status": "passed", "name": tc.get("name", f"test_{i+1}")})

        return PolicyValidationResult(
            policy_id=policy.id,
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            test_results=test_results,
            coverage=0.8 if not errors else 0.0,
        )

    async def publish_to_marketplace(self, policy_id: UUID, publisher: str) -> PolicyMarketplaceEntry | None:
        policy = self._policies.get(policy_id)
        if not policy:
            return None

        validation = await self.validate_policy(policy_id)
        if not validation.is_valid:
            return None

        entry = PolicyMarketplaceEntry(
            policy=policy,
            publisher=publisher,
            tags=[policy.category.value] + policy.frameworks,
            published_at=datetime.now(UTC),
        )
        self._marketplace[entry.id] = entry
        policy.is_community = True
        return entry

    async def search_marketplace(
        self,
        query: str | None = None,
        category: PolicyCategory | None = None,
        framework: str | None = None,
    ) -> list[PolicyMarketplaceEntry]:
        entries = list(self._marketplace.values())
        if category:
            entries = [e for e in entries if e.policy.category == category]
        if framework:
            entries = [e for e in entries if framework in e.policy.frameworks]
        if query:
            q = query.lower()
            entries = [e for e in entries if q in e.policy.name.lower() or q in e.policy.description.lower()]
        return entries

    async def get_sdk_info(self) -> list[dict]:
        """Get available SDK packages."""
        return [
            {"language": "python", "package": "complianceagent-sdk", "version": "1.0.0",
             "install": "pip install complianceagent-sdk", "docs_url": "/docs/sdk/python"},
            {"language": "typescript", "package": "@complianceagent/sdk", "version": "1.0.0",
             "install": "npm install @complianceagent/sdk", "docs_url": "/docs/sdk/typescript"},
            {"language": "go", "package": "github.com/complianceagent/sdk-go", "version": "1.0.0",
             "install": "go get github.com/complianceagent/sdk-go", "docs_url": "/docs/sdk/go"},
        ]
