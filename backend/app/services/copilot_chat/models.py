"""Compliance Copilot Chat models for non-technical users."""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class UserPersona(str, Enum):
    """User persona types for compliance chat."""

    CCO = "cco"
    AUDITOR = "auditor"
    LEGAL = "legal"
    DEVELOPER = "developer"
    EXECUTIVE = "executive"


class VisualType(str, Enum):
    """Visual presentation types for responses."""

    TABLE = "table"
    CHART = "chart"
    LIST = "list"
    CODE = "code"
    SUMMARY = "summary"
    HEATMAP = "heatmap"


@dataclass
class CannedQuery:
    """Pre-built query template for a persona."""

    id: str = ""
    persona: UserPersona = UserPersona.CCO
    category: str = ""
    label: str = ""
    query: str = ""
    icon: str = ""
    description: str = ""


@dataclass
class PersonaView:
    """Persona-specific view configuration."""

    persona: UserPersona = UserPersona.CCO
    display_name: str = ""
    description: str = ""
    default_regulations: list[str] = field(default_factory=list)
    dashboard_widgets: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)


@dataclass
class SimplifiedResponse:
    """Simplified compliance response for non-technical users."""

    id: UUID = field(default_factory=uuid4)
    question: str = ""
    answer: str = ""
    confidence: float = 0.0
    citations: list[str] = field(default_factory=list)
    suggested_followups: list[str] = field(default_factory=list)
    visual_type: VisualType = VisualType.SUMMARY
    persona: UserPersona = UserPersona.CCO


@dataclass
class ComplianceLocationResult:
    """Code location linked to a compliance requirement."""

    file_path: str = ""
    function_name: str = ""
    regulation: str = ""
    article: str = ""
    compliance_status: str = ""
    explanation: str = ""
