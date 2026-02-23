"""Pre-configured industry compliance starter packs with onboarding wizard.

Provides ready-to-use compliance configurations for Fintech, Healthtech,
AI Companies, and E-commerce — enabling 5-minute time-to-first-scan.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog


logger = structlog.get_logger()


class Industry(str, Enum):
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    AI_COMPANY = "ai_company"
    ECOMMERCE = "ecommerce"


class OnboardingStepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class OnboardingStep:
    """A single step in the onboarding wizard."""

    id: str = ""
    title: str = ""
    description: str = ""
    status: OnboardingStepStatus = OnboardingStepStatus.PENDING
    required: bool = True
    order: int = 0
    action_url: str | None = None
    completed_at: datetime | None = None


@dataclass
class StarterPackConfig:
    """Configuration for an industry starter pack."""

    id: str = ""
    industry: Industry = Industry.FINTECH
    name: str = ""
    description: str = ""
    regulations: list[str] = field(default_factory=list)
    lint_rules: list[str] = field(default_factory=list)
    policy_templates: list[str] = field(default_factory=list)
    cicd_checks: list[str] = field(default_factory=list)
    onboarding_steps: list[OnboardingStep] = field(default_factory=list)
    estimated_setup_minutes: int = 5
    icon: str = ""


@dataclass
class ProvisioningResult:
    """Result of provisioning a starter pack for an organization."""

    id: UUID = field(default_factory=uuid4)
    organization_id: str = ""
    pack_id: str = ""
    industry: str = ""
    regulations_enabled: list[str] = field(default_factory=list)
    policies_created: int = 0
    lint_rules_enabled: int = 0
    cicd_configured: bool = False
    onboarding_steps: list[OnboardingStep] = field(default_factory=list)
    provisioned_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ── Built-in Starter Packs ───────────────────────────────────────────────

_COMMON_STEPS = [
    OnboardingStep(
        "connect-repo",
        "Connect Repository",
        "Link your GitHub/GitLab repository",
        order=0,
        action_url="/settings/repositories",
    ),
    OnboardingStep(
        "initial-scan",
        "Run Initial Scan",
        "Scan your codebase for compliance issues",
        order=1,
        action_url="/dashboard/repositories",
    ),
    OnboardingStep(
        "review-findings",
        "Review Findings",
        "Review detected compliance gaps",
        order=2,
        action_url="/dashboard/actions",
    ),
]

STARTER_PACKS: dict[str, StarterPackConfig] = {
    "fintech": StarterPackConfig(
        id="fintech",
        industry=Industry.FINTECH,
        name="Fintech Compliance Pack",
        description="PCI-DSS, SOX, SOC 2, GDPR — complete financial services compliance",
        regulations=["pci-dss", "sox", "soc2", "gdpr", "ccpa"],
        lint_rules=[
            "pci-card-data",
            "pci-encryption",
            "sox-financial-controls",
            "gdpr-consent",
            "gdpr-data-retention",
        ],
        policy_templates=[
            "pci-tokenization",
            "sox-access-controls",
            "gdpr-consent-banner",
            "soc2-logging",
        ],
        cicd_checks=["pci-dss-scan", "sox-audit-check", "gdpr-data-flow"],
        onboarding_steps=[
            *_COMMON_STEPS,
            OnboardingStep(
                "payment-scan",
                "Scan Payment Flows",
                "Identify payment data handling",
                order=3,
                action_url="/dashboard/data-flow",
            ),
            OnboardingStep(
                "enable-pci",
                "Enable PCI-DSS Rules",
                "Activate PCI-DSS lint rules",
                order=4,
                action_url="/settings/compliance",
            ),
        ],
        estimated_setup_minutes=5,
        icon="💰",
    ),
    "healthtech": StarterPackConfig(
        id="healthtech",
        industry=Industry.HEALTHTECH,
        name="Healthtech Compliance Pack",
        description="HIPAA, HITRUST, SOC 2 — healthcare data protection",
        regulations=["hipaa", "soc2", "gdpr"],
        lint_rules=[
            "hipaa-phi-detection",
            "hipaa-encryption",
            "hipaa-audit-logging",
            "hipaa-access-control",
        ],
        policy_templates=["hipaa-phi-handler", "hipaa-baa-template", "hipaa-incident-response"],
        cicd_checks=["hipaa-phi-scan", "encryption-check", "access-control-audit"],
        onboarding_steps=[
            *_COMMON_STEPS,
            OnboardingStep(
                "phi-detection",
                "Configure PHI Detection",
                "Set up PHI data pattern detection",
                order=3,
                action_url="/settings/compliance",
            ),
            OnboardingStep(
                "encryption-check",
                "Verify Encryption",
                "Check encryption for PHI at rest and in transit",
                order=4,
                action_url="/dashboard/posture-scoring",
            ),
        ],
        estimated_setup_minutes=5,
        icon="🏥",
    ),
    "ai_company": StarterPackConfig(
        id="ai_company",
        industry=Industry.AI_COMPANY,
        name="AI Company Compliance Pack",
        description="EU AI Act, NIST AI RMF, ISO 42001 — AI system compliance",
        regulations=["eu-ai-act", "nist-ai-rmf", "iso-42001", "gdpr"],
        lint_rules=[
            "ai-risk-classification",
            "ai-transparency",
            "ai-bias-detection",
            "ai-data-governance",
        ],
        policy_templates=[
            "ai-model-card",
            "ai-risk-assessment",
            "ai-transparency-notice",
            "ai-human-oversight",
        ],
        cicd_checks=["ai-risk-scan", "model-documentation-check", "bias-audit"],
        onboarding_steps=[
            *_COMMON_STEPS,
            OnboardingStep(
                "ai-inventory",
                "AI System Inventory",
                "Catalog your AI systems and their risk levels",
                order=3,
                action_url="/dashboard/ai-observatory",
            ),
            OnboardingStep(
                "risk-classify",
                "Classify AI Risk",
                "Assign EU AI Act risk levels to each system",
                order=4,
                action_url="/dashboard/ai-observatory",
            ),
        ],
        estimated_setup_minutes=5,
        icon="🤖",
    ),
    "ecommerce": StarterPackConfig(
        id="ecommerce",
        industry=Industry.ECOMMERCE,
        name="E-commerce Compliance Pack",
        description="GDPR, CCPA, PCI-DSS, accessibility — online retail compliance",
        regulations=["gdpr", "ccpa", "pci-dss", "soc2"],
        lint_rules=[
            "gdpr-consent",
            "gdpr-cookie-banner",
            "ccpa-opt-out",
            "pci-card-data",
            "accessibility-wcag",
        ],
        policy_templates=[
            "gdpr-consent-banner",
            "ccpa-opt-out-handler",
            "pci-tokenization",
            "cookie-policy",
        ],
        cicd_checks=["gdpr-data-scan", "pci-dss-scan", "accessibility-check"],
        onboarding_steps=[
            *_COMMON_STEPS,
            OnboardingStep(
                "privacy-scan",
                "Scan Privacy Flows",
                "Map data collection and processing",
                order=3,
                action_url="/dashboard/data-flow",
            ),
            OnboardingStep(
                "cookie-consent",
                "Configure Consent",
                "Set up cookie consent and preference center",
                order=4,
                action_url="/settings/compliance",
            ),
        ],
        estimated_setup_minutes=5,
        icon="🛒",
    ),
}


class StarterPackService:
    """Service for provisioning industry compliance starter packs."""

    def __init__(self):
        self._provisions: dict[UUID, ProvisioningResult] = {}

    def list_packs(self) -> list[StarterPackConfig]:
        """List all available starter packs."""
        return list(STARTER_PACKS.values())

    def get_pack(self, pack_id: str) -> StarterPackConfig | None:
        """Get a specific starter pack configuration."""
        return STARTER_PACKS.get(pack_id)

    async def provision(
        self,
        organization_id: str,
        pack_id: str,
    ) -> ProvisioningResult:
        """Provision a starter pack for an organization.

        Enables the regulations, creates policy templates, configures
        lint rules, and initializes the onboarding wizard.
        """
        pack = STARTER_PACKS.get(pack_id)
        if not pack:
            raise ValueError(f"Unknown starter pack: {pack_id}")

        # Reset onboarding step statuses
        steps = [
            OnboardingStep(
                id=s.id,
                title=s.title,
                description=s.description,
                status=OnboardingStepStatus.PENDING,
                required=s.required,
                order=s.order,
                action_url=s.action_url,
            )
            for s in pack.onboarding_steps
        ]

        result = ProvisioningResult(
            organization_id=organization_id,
            pack_id=pack_id,
            industry=pack.industry.value,
            regulations_enabled=pack.regulations,
            policies_created=len(pack.policy_templates),
            lint_rules_enabled=len(pack.lint_rules),
            cicd_configured=bool(pack.cicd_checks),
            onboarding_steps=steps,
        )
        self._provisions[result.id] = result

        logger.info(
            "Starter pack provisioned",
            org=organization_id,
            pack=pack_id,
            regulations=len(pack.regulations),
        )
        return result

    async def update_onboarding_step(
        self,
        provision_id: UUID,
        step_id: str,
        status: OnboardingStepStatus,
    ) -> ProvisioningResult | None:
        """Update the status of an onboarding step."""
        provision = self._provisions.get(provision_id)
        if not provision:
            return None

        for step in provision.onboarding_steps:
            if step.id == step_id:
                step.status = status
                if status == OnboardingStepStatus.COMPLETED:
                    step.completed_at = datetime.now(UTC)
                break

        return provision

    async def get_onboarding_progress(
        self,
        provision_id: UUID,
    ) -> dict[str, Any]:
        """Get onboarding progress for a provisioned pack."""
        provision = self._provisions.get(provision_id)
        if not provision:
            return {"error": "Provision not found"}

        total = len(provision.onboarding_steps)
        completed = sum(
            1 for s in provision.onboarding_steps if s.status == OnboardingStepStatus.COMPLETED
        )

        return {
            "provision_id": str(provision.id),
            "pack_id": provision.pack_id,
            "total_steps": total,
            "completed_steps": completed,
            "progress_pct": round(completed / max(total, 1) * 100, 1),
            "is_complete": completed == total,
            "steps": [
                {
                    "id": s.id,
                    "title": s.title,
                    "status": s.status.value,
                    "order": s.order,
                    "action_url": s.action_url,
                }
                for s in provision.onboarding_steps
            ],
        }
