"""Industry Compliance Starter Packs models."""

from dataclasses import dataclass, field
from enum import Enum
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
