"""Regulation-to-Architecture Advisor models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class DiagramFormat(str, Enum):
    MERMAID = "mermaid"
    D2 = "d2"
    PLANTUML = "plantuml"
    ASCII = "ascii"


class ComponentType(str, Enum):
    SERVICE = "service"
    DATABASE = "database"
    QUEUE = "queue"
    GATEWAY = "gateway"
    ENCRYPTION = "encryption"
    CONSENT = "consent"
    AUDIT = "audit"
    CACHE = "cache"


@dataclass
class ArchComponent:
    id: str = ""
    name: str = ""
    component_type: ComponentType = ComponentType.SERVICE
    frameworks: list[str] = field(default_factory=list)
    description: str = ""
    requirements: list[str] = field(default_factory=list)


@dataclass
class ArchConnection:
    source: str = ""
    target: str = ""
    label: str = ""
    encrypted: bool = False
    audit_logged: bool = False


@dataclass
class ArchitectureDiagram:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    frameworks: list[str] = field(default_factory=list)
    components: list[ArchComponent] = field(default_factory=list)
    connections: list[ArchConnection] = field(default_factory=list)
    diagram_format: DiagramFormat = DiagramFormat.MERMAID
    diagram_code: str = ""
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class ArchAdvisorStats:
    total_diagrams: int = 0
    by_framework: dict[str, int] = field(default_factory=dict)
    by_format: dict[str, int] = field(default_factory=dict)
    avg_components: float = 0.0
