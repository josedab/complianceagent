"""Base classes and types for compliance templates."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class TemplateCategory(str, Enum):
    """Categories of compliance templates."""

    CONSENT = "consent"
    DATA_ACCESS = "data_access"
    DATA_DELETION = "data_deletion"
    DATA_EXPORT = "data_export"
    ENCRYPTION = "encryption"
    AUDIT_LOGGING = "audit_logging"
    ACCESS_CONTROL = "access_control"
    BREACH_NOTIFICATION = "breach_notification"
    AI_TRANSPARENCY = "ai_transparency"
    AI_DOCUMENTATION = "ai_documentation"
    DATA_RETENTION = "data_retention"
    PCI_TOKENIZATION = "pci_tokenization"
    HIPAA_PHI_HANDLING = "hipaa_phi_handling"


@dataclass
class TemplateParameter:
    """A parameter that can be customized in a template."""

    name: str
    description: str
    type: str  # string, number, boolean, array, object
    required: bool = True
    default: Any = None
    validation: str | None = None  # regex or validation rule


@dataclass
class ComplianceTemplate:
    """A reusable compliance code template."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    category: TemplateCategory = TemplateCategory.CONSENT
    regulations: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    
    # Template content
    code: dict[str, str] = field(default_factory=dict)  # language -> code
    tests: dict[str, str] = field(default_factory=dict)  # language -> test code
    documentation: str = ""
    
    # Parameters for customization
    parameters: list[TemplateParameter] = field(default_factory=list)
    
    # Metadata
    version: str = "1.0.0"
    author: str = "ComplianceAgent"
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0
