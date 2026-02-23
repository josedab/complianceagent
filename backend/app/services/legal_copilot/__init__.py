"""Legal copilot service."""

from app.services.legal_copilot.models import (
    ContractClause,
    DocumentType,
    LegalCitation,
    LegalCopilotStats,
    LegalDocument,
    ReviewStatus,
)
from app.services.legal_copilot.service import LegalCopilotService


__all__ = [
    "ContractClause",
    "DocumentType",
    "LegalCitation",
    "LegalCopilotService",
    "LegalCopilotStats",
    "LegalDocument",
    "ReviewStatus",
]
