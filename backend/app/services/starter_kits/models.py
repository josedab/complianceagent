"""Starter kit data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class TemplateCategory(str, Enum):
    """Categories of templates."""
    DATA_PROTECTION = "data_protection"
    AUTHENTICATION = "authentication"
    ENCRYPTION = "encryption"
    LOGGING = "logging"
    CONSENT = "consent"
    DATA_RETENTION = "data_retention"
    ACCESS_CONTROL = "access_control"
    AUDIT = "audit"
    INCIDENT_RESPONSE = "incident_response"
    DOCUMENTATION = "documentation"


class TemplateLanguage(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    CONFIG = "config"
    MARKDOWN = "markdown"


@dataclass
class CodeTemplate:
    """Code template for compliance implementation."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    language: TemplateLanguage = TemplateLanguage.PYTHON
    category: TemplateCategory = TemplateCategory.DATA_PROTECTION
    
    # Template content
    content: str = ""
    file_name: str = ""
    
    # Requirements this template addresses
    requirement_ids: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    
    # Customization
    placeholders: list[dict] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    
    # Metadata
    version: str = "1.0.0"
    author: str = "ComplianceAgent"


@dataclass
class ConfigTemplate:
    """Configuration template."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    file_name: str = ""
    content: str = ""
    format: str = "yaml"
    frameworks: list[str] = field(default_factory=list)


@dataclass
class DocumentTemplate:
    """Policy/documentation template."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    content: str = ""
    document_type: str = ""
    frameworks: list[str] = field(default_factory=list)


@dataclass
class StarterKit:
    """Complete starter kit for a regulatory framework."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    framework: str = ""
    version: str = "1.0.0"
    
    # Contents
    code_templates: list[CodeTemplate] = field(default_factory=list)
    config_templates: list[ConfigTemplate] = field(default_factory=list)
    document_templates: list[DocumentTemplate] = field(default_factory=list)
    
    # Requirements covered
    requirements_covered: list[str] = field(default_factory=list)
    
    # Languages supported
    supported_languages: list[TemplateLanguage] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    download_count: int = 0
    
    # Installation instructions
    quick_start: str = ""
    prerequisites: list[str] = field(default_factory=list)
