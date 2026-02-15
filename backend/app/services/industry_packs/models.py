"""Industry Compliance Starter Packs models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class IndustryVertical(str, Enum):
    """Supported industry verticals."""

    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    AI_COMPANY = "ai_company"
    ECOMMERCE = "ecommerce"
    INSURTECH = "insurtech"
    EDTECH = "edtech"
    GOVTECH = "govtech"


class PackStatus(str, Enum):
    """Starter pack provisioning status."""

    AVAILABLE = "available"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    OUTDATED = "outdated"


@dataclass
class RegulationBundle:
    """A pre-selected bundle of regulations for a vertical."""

    framework: str = ""
    name: str = ""
    description: str = ""
    mandatory: bool = True


@dataclass
class PolicyTemplate:
    """A pre-built policy template."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    content: str = ""
    category: str = ""


@dataclass
class IndustryPack:
    """A complete industry compliance starter pack."""

    id: UUID = field(default_factory=uuid4)
    vertical: IndustryVertical = IndustryVertical.FINTECH
    name: str = ""
    description: str = ""
    version: str = "1.0"
    status: PackStatus = PackStatus.AVAILABLE
    regulations: list[RegulationBundle] = field(default_factory=list)
    policies: list[PolicyTemplate] = field(default_factory=list)
    recommended_jurisdictions: list[str] = field(default_factory=list)
    tech_stack_recommendations: dict = field(default_factory=dict)
    setup_checklist: list[str] = field(default_factory=list)
    estimated_setup_minutes: int = 30


@dataclass
class PackProvisionResult:
    """Result of provisioning an industry pack."""

    pack_id: UUID = field(default_factory=uuid4)
    vertical: IndustryVertical = IndustryVertical.FINTECH
    regulations_activated: int = 0
    policies_created: int = 0
    scans_triggered: int = 0
    setup_checklist: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)


@dataclass
class OnboardingWizardState:
    """State of the interactive onboarding wizard."""

    step: int = 1
    total_steps: int = 4
    vertical: IndustryVertical | None = None
    jurisdictions: list[str] = field(default_factory=list)
    tech_stack: list[str] = field(default_factory=list)
    selected_regulations: list[str] = field(default_factory=list)
    completed: bool = False


class WizardStepType(str, Enum):
    """Types of wizard steps."""

    INDUSTRY_SELECT = "industry_select"
    REGULATION_CONFIG = "regulation_config"
    TECH_STACK = "tech_stack"
    POLICY_TEMPLATES = "policy_templates"
    REVIEW = "review"
    PROVISION = "provision"
    COMPLETE = "complete"


@dataclass
class WizardQuestion:
    """A question in a wizard step with branching logic."""

    id: str = ""
    question: str = ""
    question_type: str = "single_select"  # single_select, multi_select, text, boolean
    options: list[dict[str, str]] = field(default_factory=list)
    required: bool = True
    depends_on: str | None = None
    depends_value: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "question_type": self.question_type,
            "options": self.options,
            "required": self.required,
            "depends_on": self.depends_on,
            "depends_value": self.depends_value,
        }


@dataclass
class WizardStep:
    """A step in the guided onboarding wizard."""

    step_type: WizardStepType = WizardStepType.INDUSTRY_SELECT
    title: str = ""
    description: str = ""
    questions: list[WizardQuestion] = field(default_factory=list)
    completed: bool = False
    answers: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_type": self.step_type.value,
            "title": self.title,
            "description": self.description,
            "questions": [q.to_dict() for q in self.questions],
            "completed": self.completed,
            "answers": self.answers,
        }


@dataclass
class ProvisioningResult:
    """Result of provisioning an industry pack."""

    id: UUID = field(default_factory=uuid4)
    vertical: str = ""
    status: str = "completed"
    regulations_activated: int = 0
    policies_created: int = 0
    scan_configs_created: int = 0
    frameworks_registered: int = 0
    checklist_items: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    provisioned_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "vertical": self.vertical,
            "status": self.status,
            "regulations_activated": self.regulations_activated,
            "policies_created": self.policies_created,
            "scan_configs_created": self.scan_configs_created,
            "frameworks_registered": self.frameworks_registered,
            "checklist_items": self.checklist_items,
            "warnings": self.warnings,
            "provisioned_at": self.provisioned_at.isoformat(),
        }
