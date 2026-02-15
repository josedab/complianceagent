"""Industry Compliance Starter Packs Service."""

from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.industry_packs.models import (
    IndustryPack,
    IndustryVertical,
    OnboardingWizardState,
    PackProvisionResult,
    PackStatus,
    PolicyTemplate,
    ProvisioningResult,
    RegulationBundle,
    WizardQuestion,
    WizardStep,
    WizardStepType,
)

logger = structlog.get_logger()

# Pre-built industry packs
_INDUSTRY_PACKS: dict[IndustryVertical, IndustryPack] = {
    IndustryVertical.FINTECH: IndustryPack(
        vertical=IndustryVertical.FINTECH,
        name="Fintech Compliance Pack",
        description="Complete compliance bundle for financial technology companies",
        regulations=[
            RegulationBundle(framework="pci_dss", name="PCI-DSS v4.0", description="Payment card data security"),
            RegulationBundle(framework="sox", name="SOX", description="Financial reporting controls"),
            RegulationBundle(framework="gdpr", name="GDPR", description="EU data protection"),
            RegulationBundle(framework="ccpa", name="CCPA/CPRA", description="California privacy"),
            RegulationBundle(framework="soc2", name="SOC 2", description="Service organization controls"),
        ],
        policies=[
            PolicyTemplate(name="Data Encryption Policy", category="security", content="All PII and financial data must be encrypted at rest and in transit..."),
            PolicyTemplate(name="Access Control Policy", category="security", content="Principle of least privilege must be enforced..."),
            PolicyTemplate(name="Incident Response Plan", category="operations", content="Security incidents must be reported within 4 hours..."),
        ],
        recommended_jurisdictions=["us_federal", "us_california", "eu", "uk"],
        tech_stack_recommendations={"encryption": "AES-256-GCM", "tokenization": "required", "logging": "structured with PII masking"},
        setup_checklist=["Configure payment data tokenization", "Enable audit logging", "Set up encryption at rest", "Configure access controls", "Enable breach notification"],
        estimated_setup_minutes=45,
    ),
    IndustryVertical.HEALTHTECH: IndustryPack(
        vertical=IndustryVertical.HEALTHTECH,
        name="Healthtech Compliance Pack",
        description="HIPAA-centered compliance for healthcare technology",
        regulations=[
            RegulationBundle(framework="hipaa", name="HIPAA", description="Health data protection"),
            RegulationBundle(framework="gdpr", name="GDPR", description="EU data protection"),
            RegulationBundle(framework="soc2", name="SOC 2", description="Service organization controls"),
            RegulationBundle(framework="iso27001", name="ISO 27001", description="Information security management"),
        ],
        policies=[
            PolicyTemplate(name="PHI Handling Policy", category="privacy", content="Protected Health Information must be handled according to HIPAA minimum necessary standard..."),
            PolicyTemplate(name="BAA Template", category="legal", content="Business Associate Agreement template for third-party data sharing..."),
        ],
        recommended_jurisdictions=["us_federal", "eu"],
        tech_stack_recommendations={"phi_handling": "dedicated service", "audit_logging": "immutable", "encryption": "FIPS 140-2"},
        setup_checklist=["Configure PHI data classification", "Enable HIPAA audit controls", "Set up BAA tracking", "Configure minimum necessary access"],
        estimated_setup_minutes=60,
    ),
    IndustryVertical.AI_COMPANY: IndustryPack(
        vertical=IndustryVertical.AI_COMPANY,
        name="AI Company Compliance Pack",
        description="EU AI Act and AI safety framework compliance",
        regulations=[
            RegulationBundle(framework="eu_ai_act", name="EU AI Act", description="AI system regulation"),
            RegulationBundle(framework="nist_ai_rmf", name="NIST AI RMF", description="AI risk management"),
            RegulationBundle(framework="iso42001", name="ISO 42001", description="AI management system"),
            RegulationBundle(framework="gdpr", name="GDPR", description="EU data protection for training data"),
        ],
        policies=[
            PolicyTemplate(name="AI Risk Classification Policy", category="ai_governance", content="All AI systems must be classified by risk level per EU AI Act Annex III..."),
            PolicyTemplate(name="Model Documentation Standard", category="ai_governance", content="All high-risk AI systems must maintain technical documentation..."),
        ],
        recommended_jurisdictions=["eu", "us_federal", "uk"],
        tech_stack_recommendations={"model_cards": "required", "bias_testing": "automated", "explainability": "SHAP/LIME"},
        setup_checklist=["Classify AI systems by risk level", "Set up model documentation", "Configure bias testing", "Enable explainability tooling"],
        estimated_setup_minutes=40,
    ),
    IndustryVertical.ECOMMERCE: IndustryPack(
        vertical=IndustryVertical.ECOMMERCE,
        name="E-Commerce Compliance Pack",
        description="Privacy and payment compliance for online retail",
        regulations=[
            RegulationBundle(framework="gdpr", name="GDPR", description="EU data protection"),
            RegulationBundle(framework="ccpa", name="CCPA/CPRA", description="California privacy"),
            RegulationBundle(framework="pci_dss", name="PCI-DSS v4.0", description="Payment security"),
        ],
        policies=[
            PolicyTemplate(name="Cookie Consent Policy", category="privacy", content="All non-essential cookies require explicit opt-in consent..."),
            PolicyTemplate(name="DSAR Process", category="privacy", content="Data subject access requests must be fulfilled within 30 days..."),
        ],
        recommended_jurisdictions=["eu", "us_california", "uk"],
        tech_stack_recommendations={"consent_management": "required", "payment_tokenization": "required"},
        setup_checklist=["Configure consent management", "Set up payment tokenization", "Enable DSAR workflow", "Configure data retention policies"],
        estimated_setup_minutes=30,
    ),
}


class IndustryPacksService:
    """Service for industry-specific compliance starter packs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_packs(
        self, vertical: IndustryVertical | None = None
    ) -> list[IndustryPack]:
        """List available industry starter packs."""
        if vertical:
            pack = _INDUSTRY_PACKS.get(vertical)
            return [pack] if pack else []
        return list(_INDUSTRY_PACKS.values())

    async def get_pack(self, vertical: IndustryVertical) -> IndustryPack | None:
        """Get a specific industry pack."""
        return _INDUSTRY_PACKS.get(vertical)

    async def provision_pack(
        self,
        vertical: IndustryVertical,
        jurisdictions: list[str] | None = None,
        tech_stack: list[str] | None = None,
    ) -> PackProvisionResult:
        """Provision an industry pack for a tenant."""
        pack = _INDUSTRY_PACKS.get(vertical)
        if not pack:
            logger.warning("Pack not found", vertical=vertical.value)
            return PackProvisionResult(vertical=vertical)

        logger.info("Provisioning industry pack", vertical=vertical.value)

        result = PackProvisionResult(
            pack_id=pack.id,
            vertical=vertical,
            regulations_activated=len(pack.regulations),
            policies_created=len(pack.policies),
            scans_triggered=1,
            setup_checklist=pack.setup_checklist,
            next_steps=[
                f"Complete the {len(pack.setup_checklist)}-item setup checklist",
                "Connect your code repositories",
                "Run your first compliance scan",
                "Review the compliance dashboard",
            ],
        )

        return result

    async def get_wizard_state(self, session_id: str) -> OnboardingWizardState:
        """Get or create an onboarding wizard state."""
        return OnboardingWizardState()

    async def advance_wizard(
        self,
        state: OnboardingWizardState,
        vertical: IndustryVertical | None = None,
        jurisdictions: list[str] | None = None,
        tech_stack: list[str] | None = None,
    ) -> OnboardingWizardState:
        """Advance the onboarding wizard to the next step."""
        if vertical:
            state.vertical = vertical
        if jurisdictions:
            state.jurisdictions = jurisdictions
        if tech_stack:
            state.tech_stack = tech_stack

        state.step = min(state.step + 1, state.total_steps)
        if state.step >= state.total_steps:
            state.completed = True

        return state

    # ── Guided Wizard ────────────────────────────────────────────────────

    def get_wizard_steps(self, vertical: str) -> list[WizardStep]:
        """Get the full guided wizard with branching logic for a vertical."""
        steps = [
            WizardStep(
                step_type=WizardStepType.INDUSTRY_SELECT,
                title="Select Your Industry",
                description="Choose the industry vertical that best matches your business.",
                questions=[
                    WizardQuestion(
                        id="vertical",
                        question="What industry does your company operate in?",
                        question_type="single_select",
                        options=[
                            {"value": "fintech", "label": "Fintech / Financial Services"},
                            {"value": "healthtech", "label": "Healthtech / Healthcare"},
                            {"value": "ai_company", "label": "AI / Machine Learning"},
                            {"value": "ecommerce", "label": "E-Commerce / Retail"},
                            {"value": "saas", "label": "SaaS / Cloud Services"},
                            {"value": "insurance", "label": "Insurance / InsurTech"},
                            {"value": "government", "label": "Government / Public Sector"},
                        ],
                    ),
                ],
            ),
            WizardStep(
                step_type=WizardStepType.REGULATION_CONFIG,
                title="Configure Regulations",
                description="Select which regulations apply to your organization.",
                questions=[
                    WizardQuestion(
                        id="jurisdictions",
                        question="Which jurisdictions do you operate in?",
                        question_type="multi_select",
                        options=[
                            {"value": "us", "label": "United States"},
                            {"value": "eu", "label": "European Union"},
                            {"value": "uk", "label": "United Kingdom"},
                            {"value": "apac", "label": "Asia-Pacific"},
                            {"value": "global", "label": "Global"},
                        ],
                    ),
                    WizardQuestion(
                        id="handles_pii",
                        question="Does your application process personal data (PII)?",
                        question_type="boolean",
                    ),
                    WizardQuestion(
                        id="handles_phi",
                        question="Does your application process health information (PHI)?",
                        question_type="boolean",
                        depends_on="vertical",
                        depends_value="healthtech",
                    ),
                    WizardQuestion(
                        id="handles_payment",
                        question="Does your application process payment card data?",
                        question_type="boolean",
                        depends_on="vertical",
                        depends_value="fintech",
                    ),
                    WizardQuestion(
                        id="uses_ai",
                        question="Does your product use AI/ML models?",
                        question_type="boolean",
                    ),
                ],
            ),
            WizardStep(
                step_type=WizardStepType.TECH_STACK,
                title="Technology Stack",
                description="Tell us about your tech stack for tailored scanning.",
                questions=[
                    WizardQuestion(
                        id="languages",
                        question="What programming languages does your codebase use?",
                        question_type="multi_select",
                        options=[
                            {"value": "python", "label": "Python"},
                            {"value": "javascript", "label": "JavaScript/TypeScript"},
                            {"value": "java", "label": "Java"},
                            {"value": "go", "label": "Go"},
                            {"value": "csharp", "label": "C#/.NET"},
                            {"value": "ruby", "label": "Ruby"},
                        ],
                    ),
                    WizardQuestion(
                        id="cloud_provider",
                        question="Which cloud provider do you use?",
                        question_type="single_select",
                        options=[
                            {"value": "aws", "label": "AWS"},
                            {"value": "gcp", "label": "Google Cloud"},
                            {"value": "azure", "label": "Microsoft Azure"},
                            {"value": "multi", "label": "Multi-Cloud"},
                            {"value": "on_prem", "label": "On-Premises"},
                        ],
                    ),
                ],
            ),
            WizardStep(
                step_type=WizardStepType.REVIEW,
                title="Review Configuration",
                description="Review your configuration before provisioning.",
                questions=[],
            ),
        ]
        return steps

    async def provision_with_wizard(
        self,
        vertical: str,
        wizard_answers: dict[str, Any],
    ) -> ProvisioningResult:
        """Provision an industry pack using wizard answers for orchestrated setup."""
        pack = _INDUSTRY_PACKS.get(IndustryVertical(vertical)) if vertical in [v.value for v in IndustryVertical] else None
        if not pack:
            return ProvisioningResult(
                vertical=vertical,
                status="failed",
                warnings=[f"Unknown vertical: {vertical}"],
            )

        regulations_count = len(pack.regulations)
        policies_count = len(pack.policies)

        jurisdictions = wizard_answers.get("jurisdictions", ["us"])
        handles_pii = wizard_answers.get("handles_pii", False)
        uses_ai = wizard_answers.get("uses_ai", False)

        extra_regs = 0
        if handles_pii and "eu" in jurisdictions:
            extra_regs += 1  # GDPR
        if handles_pii and "us" in jurisdictions:
            extra_regs += 1  # CCPA
        if uses_ai and "eu" in jurisdictions:
            extra_regs += 1  # EU AI Act

        checklist = [
            {"item": "Regulations activated", "status": "completed", "count": regulations_count + extra_regs},
            {"item": "Policy templates created", "status": "completed", "count": policies_count},
            {"item": "Scan configurations generated", "status": "completed", "count": len(wizard_answers.get("languages", ["python"]))},
            {"item": "Compliance frameworks registered", "status": "completed", "count": regulations_count},
            {"item": "Initial baseline scan", "status": "pending", "count": 0},
        ]

        result = ProvisioningResult(
            vertical=vertical,
            status="completed",
            regulations_activated=regulations_count + extra_regs,
            policies_created=policies_count,
            scan_configs_created=len(wizard_answers.get("languages", ["python"])),
            frameworks_registered=regulations_count,
            checklist_items=checklist,
        )

        logger.info(
            "Industry pack provisioned via wizard",
            vertical=vertical,
            regulations=result.regulations_activated,
            policies=result.policies_created,
        )

        return result
