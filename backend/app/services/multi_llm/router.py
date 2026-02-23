"""Smart routing for multi-LLM requests.

Routes regulatory parsing requests to the optimal provider based on
complexity, cost, and historical accuracy — avoiding expensive models
for simple tasks and escalating to premium models for complex ones.
"""

from dataclasses import dataclass, field
from enum import Enum

import structlog

from app.services.multi_llm.models import LLMProvider, ProviderConfig


logger = structlog.get_logger()


class QueryComplexity(str, Enum):
    """Estimated complexity of a regulatory parsing request."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class RoutingDecision:
    """The routing decision for a parsing request."""

    primary_provider: LLMProvider = LLMProvider.COPILOT
    secondary_providers: list[LLMProvider] = field(default_factory=list)
    complexity: QueryComplexity = QueryComplexity.MODERATE
    reason: str = ""
    use_consensus: bool = False
    estimated_cost_usd: float = 0.0


# Heuristic thresholds for text complexity
_COMPLEXITY_THRESHOLDS = {
    "simple_max_chars": 2000,
    "moderate_max_chars": 8000,
    "complex_max_chars": 20000,
}

# Keywords that signal complex / high-stakes parsing
_CRITICAL_KEYWORDS = [
    "prohibited",
    "sanctions",
    "criminal",
    "penalty",
    "imprisonment",
    "mandatory",
    "shall not",
    "must not",
    "high-risk",
    "fundamental rights",
]

_COMPLEX_KEYWORDS = [
    "cross-border",
    "derogation",
    "adequacy",
    "supervisory authority",
    "legitimate interest",
    "data protection impact assessment",
    "special categories",
    "profiling",
    "automated decision",
]

# Cost per 1k tokens (input) by provider
_COST_PER_1K: dict[LLMProvider, float] = {
    LLMProvider.LOCAL: 0.0,
    LLMProvider.COPILOT: 0.002,
    LLMProvider.OPENAI: 0.005,
    LLMProvider.ANTHROPIC: 0.008,
}


def classify_complexity(text: str, framework: str = "") -> QueryComplexity:
    """Classify the complexity of a regulatory text for routing."""
    text_lower = text.lower()
    length = len(text)

    # Check for critical keywords first
    if any(kw in text_lower for kw in _CRITICAL_KEYWORDS):
        return QueryComplexity.CRITICAL

    if any(kw in text_lower for kw in _COMPLEX_KEYWORDS):
        return QueryComplexity.COMPLEX

    if length <= _COMPLEXITY_THRESHOLDS["simple_max_chars"]:
        return QueryComplexity.SIMPLE

    if length <= _COMPLEXITY_THRESHOLDS["moderate_max_chars"]:
        return QueryComplexity.MODERATE

    return QueryComplexity.COMPLEX


def route_request(
    text: str,
    framework: str = "",
    available_providers: list[ProviderConfig] | None = None,
    accuracy_history: dict[str, float] | None = None,
) -> RoutingDecision:
    """Determine optimal provider routing for a regulatory parsing request.

    - **Simple** → cheapest available provider (local or Copilot)
    - **Moderate** → primary reliable provider (Copilot or OpenAI)
    - **Complex** → consensus of 2+ providers
    - **Critical** → consensus of ALL providers
    """
    complexity = classify_complexity(text, framework)
    providers = available_providers or []
    enabled = [p for p in providers if p.enabled]

    if not enabled:
        return RoutingDecision(reason="No providers available")

    # Sort by cost (cheapest first)
    sorted_by_cost = sorted(enabled, key=lambda p: _COST_PER_1K.get(p.provider, 0.01))

    # Sort by accuracy (best first, if history available)
    accuracy = accuracy_history or {}
    sorted_by_accuracy = sorted(
        enabled,
        key=lambda p: accuracy.get(p.provider.value, 0.8),
        reverse=True,
    )

    tokens_estimate = len(text.split()) * 1.3
    decision = RoutingDecision(complexity=complexity)

    if complexity == QueryComplexity.SIMPLE:
        primary = sorted_by_cost[0]
        decision.primary_provider = primary.provider
        decision.reason = f"Simple text ({len(text)} chars) → cheapest provider"
        decision.use_consensus = False
        decision.estimated_cost_usd = (
            tokens_estimate / 1000 * _COST_PER_1K.get(primary.provider, 0.002)
        )

    elif complexity == QueryComplexity.MODERATE:
        primary = sorted_by_accuracy[0] if sorted_by_accuracy else sorted_by_cost[0]
        decision.primary_provider = primary.provider
        decision.reason = f"Moderate text → most accurate provider ({primary.provider.value})"
        decision.use_consensus = False
        decision.estimated_cost_usd = (
            tokens_estimate / 1000 * _COST_PER_1K.get(primary.provider, 0.002)
        )

    elif complexity == QueryComplexity.COMPLEX:
        primary = sorted_by_accuracy[0] if sorted_by_accuracy else enabled[0]
        secondaries = [p.provider for p in enabled if p.provider != primary.provider][:1]
        decision.primary_provider = primary.provider
        decision.secondary_providers = secondaries
        decision.use_consensus = True
        decision.reason = f"Complex text → consensus of {1 + len(secondaries)} providers"
        total_cost = sum(
            tokens_estimate / 1000 * _COST_PER_1K.get(p, 0.002)
            for p in [primary.provider, *secondaries]
        )
        decision.estimated_cost_usd = total_cost

    else:  # CRITICAL
        decision.primary_provider = enabled[0].provider
        decision.secondary_providers = [p.provider for p in enabled[1:]]
        decision.use_consensus = True
        decision.reason = f"Critical text → all {len(enabled)} providers for maximum accuracy"
        total_cost = sum(
            tokens_estimate / 1000 * _COST_PER_1K.get(p.provider, 0.002) for p in enabled
        )
        decision.estimated_cost_usd = total_cost

    logger.info(
        "Request routed",
        complexity=complexity.value,
        primary=decision.primary_provider.value,
        consensus=decision.use_consensus,
        estimated_cost=round(decision.estimated_cost_usd, 4),
    )
    return decision
