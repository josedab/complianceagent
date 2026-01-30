"""IDE integration services for real-time compliance checking."""

from app.services.ide.analyzer import IDEComplianceAnalyzer
from app.services.ide.copilot_suggestions import (
    ComplianceSuggestion,
    CopilotComplianceSuggester,
    QuickFixResult,
    get_copilot_suggester,
)
from app.services.ide.diagnostic import ComplianceDiagnostic, DiagnosticSeverity
from app.services.ide.lsp_server import ComplianceLSPServer


__all__ = [
    "ComplianceDiagnostic",
    "ComplianceLSPServer",
    "ComplianceSuggestion",
    "CopilotComplianceSuggester",
    "DiagnosticSeverity",
    "IDEComplianceAnalyzer",
    "QuickFixResult",
    "get_copilot_suggester",
]
