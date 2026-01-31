"""Query Parser - Extracts intent and entities from natural language queries."""

import re
from typing import Any

import structlog

from app.services.query_engine.models import (
    INTENT_PATTERNS,
    REGULATION_PATTERNS,
    ParsedQuery,
    QueryEntity,
    QueryIntent,
)


logger = structlog.get_logger()


class QueryParser:
    """Parses natural language compliance queries."""

    def __init__(self):
        self._intent_patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict[QueryIntent, list[re.Pattern]]:
        """Compile intent patterns."""
        compiled = {}
        for intent, patterns in INTENT_PATTERNS.items():
            compiled[intent] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        return compiled

    def parse(self, query: str) -> ParsedQuery:
        """Parse a natural language query.
        
        Args:
            query: The user's question or command
            
        Returns:
            ParsedQuery with extracted intent and entities
        """
        normalized = self._normalize_query(query)
        
        parsed = ParsedQuery(
            original_query=query,
            normalized_query=normalized,
        )
        
        # Detect intent
        parsed.intent, parsed.confidence = self._detect_intent(normalized)
        
        # Extract entities
        parsed.entities = self._extract_entities(normalized)
        
        # Extract specific fields
        parsed.regulations = self._extract_regulations(normalized)
        parsed.frameworks = parsed.regulations  # Alias for now
        parsed.file_patterns = self._extract_file_patterns(normalized)
        parsed.keywords = self._extract_keywords(normalized)
        parsed.time_reference = self._extract_time_reference(normalized)
        
        logger.debug(
            "Parsed query",
            intent=parsed.intent.value,
            confidence=parsed.confidence,
            regulations=parsed.regulations,
        )
        
        return parsed

    def _normalize_query(self, query: str) -> str:
        """Normalize query text."""
        # Basic normalization
        normalized = query.strip().lower()
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def _detect_intent(self, query: str) -> tuple[QueryIntent, float]:
        """Detect the intent of a query."""
        best_intent = QueryIntent.UNKNOWN
        best_score = 0.0
        
        for intent, patterns in self._intent_patterns.items():
            matches = 0
            for pattern in patterns:
                if pattern.search(query):
                    matches += 1
            
            if matches > 0:
                score = min(matches / len(patterns) + 0.3, 1.0)
                if score > best_score:
                    best_score = score
                    best_intent = intent
        
        # Default to regulation info if unknown but regulations mentioned
        if best_intent == QueryIntent.UNKNOWN:
            if any(re.search(p[0], query, re.IGNORECASE) for p in REGULATION_PATTERNS):
                best_intent = QueryIntent.REGULATION_INFO
                best_score = 0.5
        
        return best_intent, best_score

    def _extract_entities(self, query: str) -> list[QueryEntity]:
        """Extract entities from query."""
        entities = []
        
        # Extract regulations
        for pattern, name in REGULATION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                entities.append(QueryEntity(
                    entity_type="regulation",
                    value=name,
                    confidence=0.9,
                ))
        
        # Extract article/section references
        article_match = re.search(r'article\s*(\d+(?:\.\d+)?)', query, re.IGNORECASE)
        if article_match:
            entities.append(QueryEntity(
                entity_type="article",
                value=article_match.group(1),
                confidence=0.95,
            ))
        
        section_match = re.search(r'section\s*(\d+(?:\.\d+)?)', query, re.IGNORECASE)
        if section_match:
            entities.append(QueryEntity(
                entity_type="section",
                value=section_match.group(1),
                confidence=0.95,
            ))
        
        # Extract control IDs
        control_match = re.search(r'\b([A-Z]{2,4}[-.]?\d+(?:\.\d+)?)\b', query)
        if control_match:
            entities.append(QueryEntity(
                entity_type="control_id",
                value=control_match.group(1),
                confidence=0.8,
            ))
        
        # Extract file paths
        file_match = re.search(r'[\w/.-]+\.(py|js|ts|java|go|rb|yml|yaml|json)\b', query)
        if file_match:
            entities.append(QueryEntity(
                entity_type="file",
                value=file_match.group(0),
                confidence=0.95,
            ))
        
        return entities

    def _extract_regulations(self, query: str) -> list[str]:
        """Extract regulation names from query."""
        regulations = []
        for pattern, name in REGULATION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                regulations.append(name)
        return regulations

    def _extract_file_patterns(self, query: str) -> list[str]:
        """Extract file patterns from query."""
        patterns = []
        
        # Explicit file paths
        file_matches = re.findall(r'[\w/.-]+\.(py|js|ts|java|go|rb|yml|yaml|json)', query)
        patterns.extend(file_matches)
        
        # Directory references
        dir_matches = re.findall(r'in\s+(?:the\s+)?(\w+)\s+(?:directory|folder)', query)
        patterns.extend([f"{d}/**/*" for d in dir_matches])
        
        return patterns

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract important keywords from query."""
        # Common compliance keywords
        keywords = []
        
        keyword_list = [
            "encryption", "authentication", "authorization", "access control",
            "data protection", "privacy", "security", "audit", "logging",
            "backup", "incident", "breach", "vulnerability", "consent",
            "personal data", "pii", "phi", "sensitive data",
        ]
        
        for kw in keyword_list:
            if kw in query:
                keywords.append(kw)
        
        return keywords

    def _extract_time_reference(self, query: str) -> str | None:
        """Extract time references from query."""
        time_patterns = [
            (r'last\s+(week|month|year|quarter)', r'last \1'),
            (r'since\s+(\w+)', r'since \1'),
            (r'in\s+(january|february|march|april|may|june|july|august|september|october|november|december)', r'in \1'),
            (r'(\d{4})', r'\1'),
            (r'this\s+(week|month|year|quarter)', r'this \1'),
        ]
        
        for pattern, replacement in time_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None

    def suggest_clarifications(self, parsed: ParsedQuery) -> list[str]:
        """Suggest clarifying questions for ambiguous queries."""
        clarifications = []
        
        if parsed.intent == QueryIntent.UNKNOWN:
            clarifications.append("Could you rephrase your question? I can help with compliance status, regulation info, code review, or remediation guidance.")
        
        if parsed.intent == QueryIntent.COMPLIANCE_STATUS and not parsed.regulations:
            clarifications.append("Which regulation or framework are you asking about? (e.g., GDPR, HIPAA, SOC2)")
        
        if parsed.intent == QueryIntent.CODE_REVIEW and not parsed.file_patterns:
            clarifications.append("Which files or directories would you like me to review?")
        
        return clarifications


# Global instance
_parser: QueryParser | None = None


def get_query_parser() -> QueryParser:
    """Get or create query parser."""
    global _parser
    if _parser is None:
        _parser = QueryParser()
    return _parser
