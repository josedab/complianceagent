"""Copilot-powered compliance suggestions for IDE integration."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import structlog

from app.agents.copilot import CopilotClient, CopilotMessage
from app.services.ide.diagnostic import (
    CodeAction,
    ComplianceDiagnostic,
    DiagnosticCategory,
    DiagnosticSeverity,
    Position,
    Range,
)


logger = structlog.get_logger()


@dataclass
class ComplianceSuggestion:
    """AI-generated compliance suggestion."""

    diagnostic: ComplianceDiagnostic
    fix_code: str | None = None
    explanation: str | None = None
    confidence: float = 0.0
    regulation_context: str | None = None
    related_requirements: list[str] | None = None


@dataclass
class QuickFixResult:
    """Result of applying a quick fix."""

    original_code: str
    fixed_code: str
    explanation: str
    imports_added: list[str] | None = None
    compliance_comments: list[str] | None = None


class CopilotComplianceSuggester:
    """AI-powered compliance suggestion engine using Copilot SDK."""

    def __init__(self, copilot_client: CopilotClient | None = None):
        self._client = copilot_client
        self._suggestion_cache: dict[str, ComplianceSuggestion] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

    async def _get_client(self) -> CopilotClient:
        """Get or create Copilot client."""
        if self._client is None:
            self._client = CopilotClient()
        return self._client

    def _cache_key(self, code: str, diagnostic_code: str) -> str:
        """Generate cache key for suggestion."""
        content = f"{code}:{diagnostic_code}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def generate_suggestion(
        self,
        code: str,
        diagnostic: ComplianceDiagnostic,
        language: str,
        context_before: str | None = None,
        context_after: str | None = None,
    ) -> ComplianceSuggestion:
        """Generate AI-powered compliance suggestion for a diagnostic."""
        cache_key = self._cache_key(code, diagnostic.code)
        if cache_key in self._suggestion_cache:
            return self._suggestion_cache[cache_key]

        client = await self._get_client()

        system_prompt = """You are an expert compliance engineer helping developers fix compliance issues.
Generate specific, production-ready code fixes for compliance violations.

For each issue, provide:
1. Fixed code that addresses the compliance requirement
2. Brief explanation of why the fix is needed
3. Reference to specific regulation requirements

Return JSON with:
- fix_code: The corrected code (string)
- explanation: Why this fix addresses the compliance issue (string)
- confidence: How confident you are in this fix (0.0-1.0)
- regulation_context: Specific regulation text that applies (string)
- imports_needed: Any imports that need to be added (array of strings)"""

        context = ""
        if context_before:
            context += f"Code before:\n```{language}\n{context_before}\n```\n\n"
        context += f"Problematic code:\n```{language}\n{code}\n```\n"
        if context_after:
            context += f"\nCode after:\n```{language}\n{context_after}\n```"

        user_prompt = f"""Fix this compliance issue:

**Language**: {language}
**Regulation**: {diagnostic.regulation or 'General Compliance'}
**Issue Code**: {diagnostic.code}
**Issue Message**: {diagnostic.message}
**Category**: {diagnostic.category.value if diagnostic.category else 'Unknown'}
**Article Reference**: {diagnostic.article_reference or 'N/A'}

{context}

Provide a compliant fix. Return JSON only."""

        try:
            async with client:
                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=user_prompt)],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=2048,
                )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.rstrip("`")

            result = json.loads(content)

            suggestion = ComplianceSuggestion(
                diagnostic=diagnostic,
                fix_code=result.get("fix_code"),
                explanation=result.get("explanation"),
                confidence=result.get("confidence", 0.5),
                regulation_context=result.get("regulation_context"),
                related_requirements=result.get("imports_needed"),
            )

            self._suggestion_cache[cache_key] = suggestion
            return suggestion

        except Exception as e:
            logger.warning(f"Failed to generate Copilot suggestion: {e}")
            return ComplianceSuggestion(
                diagnostic=diagnostic,
                explanation=f"Unable to generate AI suggestion: {e}",
                confidence=0.0,
            )

    async def generate_quick_fix(
        self,
        code: str,
        diagnostic: ComplianceDiagnostic,
        language: str,
        fix_type: str = "auto",
    ) -> QuickFixResult:
        """Generate a quick fix for a compliance issue."""
        client = await self._get_client()

        fix_strategies = {
            "mask_pii": "Mask or redact the PII data before use",
            "encrypt": "Add encryption for sensitive data",
            "add_consent_check": "Add consent verification before processing",
            "add_audit_log": "Add audit logging for the operation",
            "add_documentation": "Add required compliance documentation",
            "add_explanation": "Add explainability for AI decisions",
            "auto": "Choose the most appropriate fix",
        }

        strategy = fix_strategies.get(fix_type, fix_strategies["auto"])

        system_prompt = f"""You are an expert {language} developer generating compliance fixes.

Generate production-quality code that:
1. Addresses the specific compliance violation
2. Follows existing code patterns and style
3. Includes necessary imports
4. Adds compliance comments where appropriate

Strategy: {strategy}

Return JSON with:
- fixed_code: The complete fixed code (string)
- explanation: What was changed and why (string)
- imports_added: List of imports to add at file top (array of strings)
- compliance_comments: Comments to add explaining compliance (array of strings)"""

        user_prompt = f"""Fix this {diagnostic.regulation} compliance issue:

**Issue**: {diagnostic.message}
**Code**: {diagnostic.code}
**Reference**: {diagnostic.article_reference or 'N/A'}

Original code:
```{language}
{code}
```

Return JSON only."""

        try:
            async with client:
                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=user_prompt)],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=2048,
                )

            content = response.content.strip()
            if content.startswith("```"):
                parts = content.split("```")
                content = parts[1] if len(parts) > 1 else content
                if content.startswith("json"):
                    content = content[4:]
            content = content.rstrip("`")

            result = json.loads(content)

            return QuickFixResult(
                original_code=code,
                fixed_code=result.get("fixed_code", code),
                explanation=result.get("explanation", "Fix applied"),
                imports_added=result.get("imports_added"),
                compliance_comments=result.get("compliance_comments"),
            )

        except Exception as e:
            logger.warning(f"Failed to generate quick fix: {e}")
            return QuickFixResult(
                original_code=code,
                fixed_code=code,
                explanation=f"Unable to generate fix: {e}",
            )

    async def get_regulation_tooltip(
        self,
        regulation: str,
        article_reference: str | None = None,
        category: DiagnosticCategory | None = None,
    ) -> dict[str, Any]:
        """Get detailed regulation information for tooltip display."""
        client = await self._get_client()

        system_prompt = """You are a regulatory compliance expert.
Provide clear, concise explanations of regulations for software developers.

Return JSON with:
- title: Regulation title
- summary: 2-3 sentence summary of what this requires
- key_requirements: Array of specific technical requirements
- penalties: Potential penalties for non-compliance
- examples: Array of code-level examples of compliance/non-compliance
- resources: Array of {title, url} for learning more"""

        query = f"Explain {regulation}"
        if article_reference:
            query += f" {article_reference}"
        if category:
            query += f" requirements for {category.value.replace('_', ' ')}"

        try:
            async with client:
                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=query)],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=1024,
                )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.rstrip("`"))

        except Exception as e:
            logger.warning(f"Failed to get regulation tooltip: {e}")
            return {
                "title": regulation,
                "summary": f"Information about {regulation}",
                "key_requirements": [],
                "penalties": "Consult official documentation",
                "examples": [],
                "resources": [],
            }

    async def analyze_code_block(
        self,
        code: str,
        language: str,
        regulations: list[str] | None = None,
    ) -> list[ComplianceSuggestion]:
        """Perform deep AI analysis of a code block for compliance issues."""
        client = await self._get_client()

        regs = regulations or ["GDPR", "CCPA", "HIPAA", "EU AI Act", "SOX"]

        system_prompt = f"""You are an expert compliance auditor analyzing code for regulatory issues.

Check the code against these regulations: {', '.join(regs)}

For each issue found, provide:
- line: Line number (0-indexed)
- start_char: Start character position
- end_char: End character position
- code: Issue code (e.g., "GDPR-001")
- severity: error, warning, information, or hint
- message: Clear description of the issue
- regulation: Which regulation is affected
- article: Specific article/section reference
- category: Category like data_privacy, consent, security, etc.
- fix_code: Suggested fix
- explanation: Why this is an issue

Return JSON array of issues. If no issues, return []."""

        try:
            async with client:
                response = await client.chat(
                    messages=[
                        CopilotMessage(
                            role="user",
                            content=f"Analyze this {language} code:\n\n```{language}\n{code}\n```\n\nReturn JSON array only.",
                        )
                    ],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=4096,
                )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            issues = json.loads(content.rstrip("`"))

            suggestions = []
            for issue in issues:
                severity_map = {
                    "error": DiagnosticSeverity.ERROR,
                    "warning": DiagnosticSeverity.WARNING,
                    "information": DiagnosticSeverity.INFORMATION,
                    "hint": DiagnosticSeverity.HINT,
                }
                category_map = {
                    "data_privacy": DiagnosticCategory.DATA_PRIVACY,
                    "consent": DiagnosticCategory.CONSENT,
                    "security": DiagnosticCategory.SECURITY,
                    "encryption": DiagnosticCategory.ENCRYPTION,
                    "audit_logging": DiagnosticCategory.AUDIT_LOGGING,
                    "ai_transparency": DiagnosticCategory.AI_TRANSPARENCY,
                    "ai_documentation": DiagnosticCategory.AI_DOCUMENTATION,
                    "pii_handling": DiagnosticCategory.PII_HANDLING,
                    "data_transfer": DiagnosticCategory.DATA_TRANSFER,
                    "data_retention": DiagnosticCategory.DATA_RETENTION,
                    "access_control": DiagnosticCategory.ACCESS_CONTROL,
                }

                diagnostic = ComplianceDiagnostic(
                    range=Range(
                        start=Position(
                            line=issue.get("line", 0),
                            character=issue.get("start_char", 0),
                        ),
                        end=Position(
                            line=issue.get("line", 0),
                            character=issue.get("end_char", 100),
                        ),
                    ),
                    message=issue.get("message", "Compliance issue detected"),
                    severity=severity_map.get(
                        issue.get("severity", "warning"),
                        DiagnosticSeverity.WARNING,
                    ),
                    code=issue.get("code", "AI-001"),
                    category=category_map.get(issue.get("category")),
                    regulation=issue.get("regulation"),
                    article_reference=issue.get("article"),
                )

                suggestion = ComplianceSuggestion(
                    diagnostic=diagnostic,
                    fix_code=issue.get("fix_code"),
                    explanation=issue.get("explanation"),
                    confidence=0.85,  # AI-generated
                )
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.warning(f"Failed to analyze code block: {e}")
            return []

    def clear_cache(self) -> None:
        """Clear the suggestion cache."""
        self._suggestion_cache.clear()


# Global suggester instance
_suggester: CopilotComplianceSuggester | None = None


def get_copilot_suggester() -> CopilotComplianceSuggester:
    """Get or create the global Copilot suggester."""
    global _suggester
    if _suggester is None:
        _suggester = CopilotComplianceSuggester()
    return _suggester
