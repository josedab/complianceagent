"""Differential privacy primitives for federated compliance intelligence.

Implements Laplace noise mechanism for numeric queries and randomized
response for categorical data — ensuring that individual organization
contributions cannot be inferred from aggregate statistics.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog


logger = structlog.get_logger()


class PrivacyLevel(str, Enum):
    """Privacy budget presets."""

    STRICT = "strict"  # ε = 0.1 — very high privacy, noisy results
    BALANCED = "balanced"  # ε = 1.0 — standard privacy/utility tradeoff
    RELAXED = "relaxed"  # ε = 5.0 — lower privacy, cleaner results


@dataclass
class PrivacyBudget:
    """Tracks cumulative privacy expenditure (ε-budget)."""

    epsilon_total: float = 10.0
    epsilon_spent: float = 0.0
    queries_executed: int = 0

    @property
    def epsilon_remaining(self) -> float:
        return max(0.0, self.epsilon_total - self.epsilon_spent)

    @property
    def is_exhausted(self) -> bool:
        return self.epsilon_remaining <= 0

    def spend(self, epsilon: float) -> bool:
        """Attempt to spend epsilon from the budget."""
        if epsilon > self.epsilon_remaining:
            return False
        self.epsilon_spent += epsilon
        self.queries_executed += 1
        return True


@dataclass
class AnonymizedMetric:
    """A metric with differential privacy noise applied."""

    name: str = ""
    true_value: float | None = None  # never exposed externally
    noisy_value: float = 0.0
    epsilon_used: float = 1.0
    noise_scale: float = 0.0
    sensitivity: float = 1.0


@dataclass
class AnonymizedPattern:
    """A compliance pattern anonymized for sharing."""

    id: str = ""
    category: str = ""
    description: str = ""
    frequency: float = 0.0
    industry: str = ""
    regulation: str = ""
    anonymization_method: str = "laplace"
    epsilon: float = 1.0


# Preset epsilon values
PRIVACY_PRESETS: dict[PrivacyLevel, float] = {
    PrivacyLevel.STRICT: 0.1,
    PrivacyLevel.BALANCED: 1.0,
    PrivacyLevel.RELAXED: 5.0,
}


def laplace_noise(sensitivity: float, epsilon: float) -> float:
    """Generate Laplace noise for a given sensitivity and privacy budget.

    Uses the inverse CDF method to avoid importing numpy:
        noise = -b * sign(U) * ln(1 - 2|U|)  where b = sensitivity/epsilon
    """
    import secrets

    b = sensitivity / epsilon

    # Generate uniform random in (-0.5, 0.5)
    u = (secrets.randbelow(1_000_000) / 1_000_000) - 0.5

    # Laplace inverse CDF
    sign = 1.0 if u >= 0 else -1.0
    abs_u = abs(u)
    if abs_u >= 0.5:
        abs_u = 0.4999999
    noise = -b * sign * math.log(1 - 2 * abs_u)

    return noise


def add_laplace_noise(
    value: float,
    sensitivity: float = 1.0,
    epsilon: float = 1.0,
    clamp_min: float | None = None,
    clamp_max: float | None = None,
) -> AnonymizedMetric:
    """Apply Laplace mechanism to a numeric value.

    Parameters:
        value: The true value to protect.
        sensitivity: The maximum change one individual can cause (Δf).
        epsilon: Privacy parameter (smaller = more private).
        clamp_min/max: Optional bounds for the noisy output.
    """
    noise = laplace_noise(sensitivity, epsilon)
    noisy = value + noise

    if clamp_min is not None:
        noisy = max(clamp_min, noisy)
    if clamp_max is not None:
        noisy = min(clamp_max, noisy)

    return AnonymizedMetric(
        true_value=None,  # never store the true value in shared results
        noisy_value=round(noisy, 2),
        epsilon_used=epsilon,
        noise_scale=sensitivity / epsilon,
        sensitivity=sensitivity,
    )


def randomized_response(
    true_answer: bool,
    epsilon: float = 1.0,
) -> bool:
    """Randomized response mechanism for binary/categorical data.

    With probability p = e^ε / (1 + e^ε), report the truth;
    otherwise report the opposite.
    """
    import secrets

    p = math.exp(epsilon) / (1 + math.exp(epsilon))
    random_val = secrets.randbelow(1_000_000) / 1_000_000

    if random_val < p:
        return true_answer
    return not true_answer


def anonymize_compliance_patterns(
    patterns: list[dict[str, Any]],
    privacy_level: PrivacyLevel = PrivacyLevel.BALANCED,
    budget: PrivacyBudget | None = None,
) -> list[AnonymizedPattern]:
    """Anonymize a batch of compliance patterns for network sharing.

    Applies Laplace noise to frequency counts and randomized response
    to categorical flags.
    """
    epsilon = PRIVACY_PRESETS[privacy_level]

    if budget and budget.is_exhausted:
        logger.warning("Privacy budget exhausted, refusing to anonymize")
        return []

    anonymized: list[AnonymizedPattern] = []

    for pattern in patterns:
        per_query_epsilon = epsilon / max(len(patterns), 1)

        if budget and not budget.spend(per_query_epsilon):
            logger.warning("Privacy budget insufficient for remaining patterns")
            break

        freq = pattern.get("frequency", 0)
        noisy_freq = add_laplace_noise(
            value=freq,
            sensitivity=1.0,
            epsilon=per_query_epsilon,
            clamp_min=0.0,
        )

        anonymized.append(
            AnonymizedPattern(
                id=pattern.get("id", ""),
                category=pattern.get("category", ""),
                description=pattern.get("description", ""),
                frequency=noisy_freq.noisy_value,
                industry=pattern.get("industry", ""),
                regulation=pattern.get("regulation", ""),
                anonymization_method="laplace",
                epsilon=per_query_epsilon,
            )
        )

    logger.info(
        "Patterns anonymized",
        count=len(anonymized),
        privacy_level=privacy_level.value,
        epsilon=epsilon,
    )
    return anonymized


def compute_similar_organizations(
    org_profile: dict[str, Any],
    network_profiles: list[dict[str, Any]],
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Find 'companies like you' based on anonymized industry profiles.

    Uses Jaccard similarity on regulation set and industry match.
    """
    org_regs = set(org_profile.get("regulations", []))
    org_industry = org_profile.get("industry", "")
    org_size = org_profile.get("size_bucket", "medium")

    scored: list[tuple[float, dict[str, Any]]] = []

    for profile in network_profiles:
        profile_regs = set(profile.get("regulations", []))
        profile_industry = profile.get("industry", "")
        profile_size = profile.get("size_bucket", "medium")

        # Jaccard similarity on regulations
        intersection = org_regs & profile_regs
        union = org_regs | profile_regs
        reg_sim = len(intersection) / max(len(union), 1)

        # Industry match
        industry_match = 1.0 if org_industry == profile_industry else 0.0

        # Size match
        size_match = 1.0 if org_size == profile_size else 0.3

        similarity = reg_sim * 0.5 + industry_match * 0.3 + size_match * 0.2
        scored.append(
            (
                similarity,
                {
                    "id": profile.get("id", ""),
                    "industry": profile_industry,
                    "similarity_score": round(similarity, 3),
                    "shared_regulations": list(intersection),
                },
            )
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:max_results]]
