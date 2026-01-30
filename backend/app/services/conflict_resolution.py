"""Multi-jurisdiction conflict resolution service."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog

from app.models.regulation import Jurisdiction
from app.models.requirement import ObligationType, Requirement


logger = structlog.get_logger()


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving jurisdiction conflicts."""

    MOST_RESTRICTIVE = "most_restrictive"  # Apply the strictest requirement
    JURISDICTION_SPECIFIC = "jurisdiction_specific"  # Different rules per jurisdiction
    EXPLICIT_CONSENT = "explicit_consent"  # Let user choose
    UNION = "union"  # Combine all requirements
    HEADQUARTERS = "headquarters"  # Use HQ jurisdiction rules


@dataclass
class ConflictResult:
    """Result of conflict resolution."""

    has_conflict: bool
    conflicting_requirements: list[Requirement]
    resolution_strategy: ConflictResolutionStrategy
    resolved_requirement: dict[str, Any] | None
    notes: list[str]
    needs_human_review: bool


class JurisdictionConflictResolver:
    """Resolves conflicts between requirements from different jurisdictions."""

    # Jurisdiction strictness ranking (higher = stricter)
    STRICTNESS_RANKING = {
        Jurisdiction.EU: 10,  # GDPR is typically strictest
        Jurisdiction.UK: 9,
        Jurisdiction.US_CALIFORNIA: 8,
        Jurisdiction.US_NEW_YORK: 7,
        Jurisdiction.US_FEDERAL: 6,
        Jurisdiction.SINGAPORE: 5,
        Jurisdiction.SOUTH_KOREA: 6,
        Jurisdiction.CHINA: 8,  # PIPL has strict requirements
        Jurisdiction.INDIA: 5,
        Jurisdiction.JAPAN: 6,  # APPI has comprehensive requirements
        Jurisdiction.BRAZIL: 7,  # LGPD closely mirrors GDPR
        Jurisdiction.AUSTRALIA: 5,
        Jurisdiction.CANADA: 6,
        Jurisdiction.GLOBAL: 3,
    }

    # Common conflict patterns and resolutions
    CONFLICT_PATTERNS = {
        "data_retention": {
            "description": "Different data retention periods",
            "resolution": "Use shortest retention period",
            "strategy": ConflictResolutionStrategy.MOST_RESTRICTIVE,
        },
        "consent_requirements": {
            "description": "Different consent mechanisms",
            "resolution": "Implement strictest consent (opt-in)",
            "strategy": ConflictResolutionStrategy.MOST_RESTRICTIVE,
        },
        "data_transfer": {
            "description": "Cross-border data transfer restrictions",
            "resolution": "Apply all transfer restrictions",
            "strategy": ConflictResolutionStrategy.UNION,
        },
        "breach_notification": {
            "description": "Different breach notification timelines",
            "resolution": "Use shortest notification period",
            "strategy": ConflictResolutionStrategy.MOST_RESTRICTIVE,
        },
        "data_subject_rights": {
            "description": "Different data subject rights",
            "resolution": "Implement union of all rights",
            "strategy": ConflictResolutionStrategy.UNION,
        },
    }

    def __init__(self, default_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MOST_RESTRICTIVE):
        self.default_strategy = default_strategy

    def detect_conflicts(
        self,
        requirements: list[Requirement],
    ) -> list[list[Requirement]]:
        """Detect conflicting requirements across jurisdictions."""
        conflicts = []

        # Group by category
        by_category: dict[str, list[Requirement]] = {}
        for req in requirements:
            cat = req.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(req)

        # Find conflicts within each category
        for reqs in by_category.values():
            if len(reqs) < 2:
                continue

            # Check for jurisdictional differences
            jurisdictions = {r.regulation.jurisdiction for r in reqs if r.regulation}
            if len(jurisdictions) > 1:
                # Potential conflict
                if self._has_substantive_conflict(reqs):
                    conflicts.append(reqs)

        return conflicts

    def _has_substantive_conflict(self, requirements: list[Requirement]) -> bool:
        """Check if requirements have substantive differences."""
        # Check obligation types
        obligation_types = {r.obligation_type for r in requirements}
        if ObligationType.MUST in obligation_types and ObligationType.MAY in obligation_types:
            return True

        # Check timeframes
        timeframes = [r.deadline_days for r in requirements if r.deadline_days]
        if timeframes and max(timeframes) - min(timeframes) > 7:  # 7 day variance
            return True

        # Check for explicit conflicts in actions
        actions = [r.action.lower() for r in requirements]
        return bool(any("not" in a for a in actions) and any("not" not in a for a in actions))

    def resolve_conflict(
        self,
        conflicting_requirements: list[Requirement],
        strategy: ConflictResolutionStrategy | None = None,
        customer_hq_jurisdiction: Jurisdiction | None = None,
    ) -> ConflictResult:
        """Resolve a conflict between requirements."""
        strategy = strategy or self.default_strategy
        notes = []
        needs_review = False

        if not conflicting_requirements:
            return ConflictResult(
                has_conflict=False,
                conflicting_requirements=[],
                resolution_strategy=strategy,
                resolved_requirement=None,
                notes=[],
                needs_human_review=False,
            )

        # Identify conflict type
        category = conflicting_requirements[0].category.value
        conflict_pattern = self.CONFLICT_PATTERNS.get(category, {})

        if conflict_pattern:
            notes.append(f"Identified conflict pattern: {conflict_pattern.get('description')}")
            strategy = conflict_pattern.get("strategy", strategy)

        # Resolve based on strategy
        if strategy == ConflictResolutionStrategy.MOST_RESTRICTIVE:
            resolved = self._resolve_most_restrictive(conflicting_requirements)
            notes.append("Resolved using most restrictive requirement")

        elif strategy == ConflictResolutionStrategy.JURISDICTION_SPECIFIC:
            resolved = self._resolve_jurisdiction_specific(conflicting_requirements)
            notes.append("Resolved with jurisdiction-specific implementations")
            needs_review = True  # Complex implementation needs review

        elif strategy == ConflictResolutionStrategy.UNION:
            resolved = self._resolve_union(conflicting_requirements)
            notes.append("Resolved by combining all requirements")

        elif strategy == ConflictResolutionStrategy.HEADQUARTERS:
            if customer_hq_jurisdiction:
                resolved = self._resolve_headquarters(
                    conflicting_requirements, customer_hq_jurisdiction
                )
                notes.append(f"Resolved using HQ jurisdiction: {customer_hq_jurisdiction.value}")
            else:
                resolved = self._resolve_most_restrictive(conflicting_requirements)
                notes.append("No HQ jurisdiction specified, using most restrictive")

        else:  # EXPLICIT_CONSENT
            resolved = None
            needs_review = True
            notes.append("Requires explicit decision from compliance team")

        return ConflictResult(
            has_conflict=True,
            conflicting_requirements=conflicting_requirements,
            resolution_strategy=strategy,
            resolved_requirement=resolved,
            notes=notes,
            needs_human_review=needs_review,
        )

    def _resolve_most_restrictive(
        self,
        requirements: list[Requirement],
    ) -> dict[str, Any]:
        """Resolve by choosing the most restrictive requirement."""
        # Score each requirement
        scored = []
        for req in requirements:
            score = 0

            # Jurisdiction strictness
            if req.regulation:
                score += self.STRICTNESS_RANKING.get(req.regulation.jurisdiction, 0) * 10

            # Obligation type
            if req.obligation_type == ObligationType.MUST:
                score += 5
            elif req.obligation_type == ObligationType.MUST_NOT:
                score += 6
            elif req.obligation_type == ObligationType.SHOULD:
                score += 3

            # Shorter deadline = stricter
            if req.deadline_days:
                score += max(0, 30 - req.deadline_days)

            scored.append((score, req))

        # Get highest scored
        scored.sort(key=lambda x: x[0], reverse=True)
        strictest = scored[0][1]

        return {
            "reference_id": f"RESOLVED-{strictest.reference_id}",
            "title": f"[Resolved] {strictest.title}",
            "description": strictest.description,
            "obligation_type": strictest.obligation_type.value,
            "category": strictest.category.value,
            "action": strictest.action,
            "deadline_days": strictest.deadline_days,
            "source_requirements": [r.reference_id for r in requirements],
            "source_jurisdictions": list({
                r.regulation.jurisdiction.value for r in requirements if r.regulation
            }),
        }

    def _resolve_jurisdiction_specific(
        self,
        requirements: list[Requirement],
    ) -> dict[str, Any]:
        """Resolve with jurisdiction-specific implementations."""
        implementations = {}

        for req in requirements:
            if req.regulation:
                jurisdiction = req.regulation.jurisdiction.value
                implementations[jurisdiction] = {
                    "reference_id": req.reference_id,
                    "action": req.action,
                    "deadline_days": req.deadline_days,
                    "obligation_type": req.obligation_type.value,
                }

        return {
            "reference_id": f"MULTI-JURISDICTION-{requirements[0].category.value}",
            "title": f"Multi-jurisdiction: {requirements[0].title}",
            "description": "Jurisdiction-specific implementation required",
            "implementations": implementations,
            "source_requirements": [r.reference_id for r in requirements],
        }

    def _resolve_union(
        self,
        requirements: list[Requirement],
    ) -> dict[str, Any]:
        """Resolve by combining all requirements."""
        all_actions = []
        all_data_types = set()
        all_processes = set()
        min_deadline = None

        for req in requirements:
            all_actions.append(f"[{req.regulation.jurisdiction.value if req.regulation else 'Unknown'}] {req.action}")
            all_data_types.update(req.data_types)
            all_processes.update(req.processes)
            if req.deadline_days:
                if min_deadline is None or req.deadline_days < min_deadline:
                    min_deadline = req.deadline_days

        return {
            "reference_id": f"UNION-{requirements[0].category.value}",
            "title": f"[Combined] {requirements[0].title}",
            "description": "Combined requirement from multiple jurisdictions",
            "obligation_type": "must",
            "category": requirements[0].category.value,
            "actions": all_actions,
            "data_types": list(all_data_types),
            "processes": list(all_processes),
            "deadline_days": min_deadline,
            "source_requirements": [r.reference_id for r in requirements],
        }

    def _resolve_headquarters(
        self,
        requirements: list[Requirement],
        hq_jurisdiction: Jurisdiction,
    ) -> dict[str, Any]:
        """Resolve using headquarters jurisdiction."""
        # Find requirement matching HQ jurisdiction
        for req in requirements:
            if req.regulation and req.regulation.jurisdiction == hq_jurisdiction:
                return {
                    "reference_id": f"HQ-{req.reference_id}",
                    "title": f"[HQ-Based] {req.title}",
                    "description": req.description,
                    "obligation_type": req.obligation_type.value,
                    "category": req.category.value,
                    "action": req.action,
                    "deadline_days": req.deadline_days,
                    "source_requirements": [r.reference_id for r in requirements],
                    "primary_jurisdiction": hq_jurisdiction.value,
                }

        # If no HQ match, fall back to most restrictive
        return self._resolve_most_restrictive(requirements)


def resolve_jurisdiction_conflicts(
    requirements: list[Requirement],
    strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MOST_RESTRICTIVE,
    hq_jurisdiction: Jurisdiction | None = None,
) -> list[ConflictResult]:
    """Convenience function to detect and resolve all conflicts."""
    resolver = JurisdictionConflictResolver(default_strategy=strategy)
    conflicts = resolver.detect_conflicts(requirements)

    results = []
    for conflicting_reqs in conflicts:
        result = resolver.resolve_conflict(
            conflicting_reqs,
            strategy=strategy,
            customer_hq_jurisdiction=hq_jurisdiction,
        )
        results.append(result)

    return results
