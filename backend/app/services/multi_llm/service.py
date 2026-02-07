"""Multi-LLM Regulatory Parsing Engine Service."""

import asyncio
import time
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.multi_llm.models import (
    ConsensusResult,
    ConsensusStrategy,
    LLMProvider,
    MultiLLMConfig,
    ParseStatus,
    ProviderConfig,
    ProviderResult,
)

logger = structlog.get_logger()


class MultiLLMService:
    """Service for multi-LLM regulatory parsing with consensus."""

    def __init__(
        self,
        db: AsyncSession,
        copilot_client: object | None = None,
        config: MultiLLMConfig | None = None,
    ):
        self.db = db
        self.copilot = copilot_client
        self.config = config or MultiLLMConfig(
            providers=[
                ProviderConfig(provider=LLMProvider.COPILOT, model_name="copilot-default", weight=1.0),
            ]
        )
        self._results_cache: dict[UUID, ConsensusResult] = {}

    async def parse_regulation(
        self,
        text: str,
        framework: str = "",
        strategy: ConsensusStrategy | None = None,
    ) -> ConsensusResult:
        """Parse regulatory text using multiple LLMs and build consensus."""
        start = time.monotonic()
        effective_strategy = strategy or self.config.consensus_strategy

        result = ConsensusResult(
            status=ParseStatus.IN_PROGRESS,
            strategy=effective_strategy,
        )

        enabled_providers = [p for p in self.config.providers if p.enabled]

        if not enabled_providers:
            result.status = ParseStatus.FAILED
            return result

        # Run all providers in parallel
        provider_results = await asyncio.gather(
            *[self._run_provider(provider, text, framework) for provider in enabled_providers],
            return_exceptions=True,
        )

        for pr in provider_results:
            if isinstance(pr, ProviderResult):
                result.provider_results.append(pr)
            elif isinstance(pr, Exception):
                result.provider_results.append(
                    ProviderResult(error=str(pr))
                )

        successful = [pr for pr in result.provider_results if pr.error is None]

        if not successful:
            result.status = ParseStatus.FAILED
            return result

        # Build consensus
        if len(successful) == 1 and self.config.fallback_to_single:
            result.obligations = successful[0].obligations
            result.entities = successful[0].entities
            result.confidence = successful[0].confidence
            result.agreement_score = 1.0
        else:
            self._build_consensus(result, successful, effective_strategy)

        # Check for divergence
        if result.agreement_score < (1 - self.config.divergence_threshold):
            result.status = ParseStatus.DIVERGENT
            result.needs_human_review = True
        else:
            result.status = ParseStatus.COMPLETED

        result.total_latency_ms = (time.monotonic() - start) * 1000
        result.completed_at = datetime.now(UTC)
        self._results_cache[result.id] = result

        logger.info(
            "Multi-LLM parse complete",
            providers=len(successful),
            strategy=effective_strategy.value,
            agreement=round(result.agreement_score, 3),
            divergent=result.needs_human_review,
        )
        return result

    async def get_result(self, result_id: UUID) -> ConsensusResult | None:
        """Get a cached consensus result."""
        return self._results_cache.get(result_id)

    async def list_providers(self) -> list[ProviderConfig]:
        """List configured LLM providers."""
        return self.config.providers

    async def add_provider(self, provider: ProviderConfig) -> ProviderConfig:
        """Add a new LLM provider."""
        self.config.providers.append(provider)
        logger.info("Provider added", provider=provider.provider.value, model=provider.model_name)
        return provider

    async def remove_provider(self, provider_name: LLMProvider) -> bool:
        """Remove an LLM provider."""
        original_count = len(self.config.providers)
        self.config.providers = [p for p in self.config.providers if p.provider != provider_name]
        removed = len(self.config.providers) < original_count
        if removed:
            logger.info("Provider removed", provider=provider_name.value)
        return removed

    async def update_config(self, config: MultiLLMConfig) -> MultiLLMConfig:
        """Update the multi-LLM configuration."""
        self.config = config
        return config

    async def get_config(self) -> MultiLLMConfig:
        """Get current configuration."""
        return self.config

    async def _run_provider(
        self, config: ProviderConfig, text: str, framework: str
    ) -> ProviderResult:
        """Run parsing with a single provider."""
        start = time.monotonic()
        result = ProviderResult(
            provider=config.provider,
            model_name=config.model_name,
        )

        try:
            if config.provider == LLMProvider.COPILOT and self.copilot:
                ai_result = await self.copilot.analyze_legal_text(text)
                result.obligations = ai_result.get("requirements", [])
                result.entities = self._extract_entities(ai_result)
                result.confidence = self._avg_confidence(ai_result)
                result.raw_response = ai_result
            else:
                # Simulated provider response for non-Copilot providers
                result.obligations = [{"type": "must", "action": "comply", "subject": "controller"}]
                result.entities = ["controller", "data subject"]
                result.confidence = 0.80
        except Exception as e:
            result.error = str(e)
            logger.exception("Provider failed", provider=config.provider.value)

        result.latency_ms = (time.monotonic() - start) * 1000
        return result

    def _build_consensus(
        self,
        result: ConsensusResult,
        providers: list[ProviderResult],
        strategy: ConsensusStrategy,
    ) -> None:
        """Build consensus from multiple provider results."""
        if strategy == ConsensusStrategy.HIGHEST_CONFIDENCE:
            best = max(providers, key=lambda p: p.confidence)
            result.obligations = best.obligations
            result.entities = best.entities
            result.confidence = best.confidence

        elif strategy == ConsensusStrategy.WEIGHTED_AVERAGE:
            # Merge obligations weighted by confidence
            all_obligations = []
            for pr in providers:
                all_obligations.extend(pr.obligations)
            result.obligations = self._deduplicate_obligations(all_obligations)
            result.confidence = sum(p.confidence for p in providers) / len(providers)

            # Merge entities
            all_entities: set[str] = set()
            for pr in providers:
                all_entities.update(pr.entities)
            result.entities = sorted(all_entities)

        else:  # MAJORITY_VOTE (default)
            # Count obligation actions
            action_counts: dict[str, int] = {}
            action_map: dict[str, dict] = {}
            for pr in providers:
                for obl in pr.obligations:
                    key = obl.get("action", "")
                    action_counts[key] = action_counts.get(key, 0) + 1
                    action_map[key] = obl

            threshold = len(providers) / 2
            result.obligations = [
                action_map[action] for action, count in action_counts.items() if count > threshold
            ]

            # Majority vote on entities
            entity_counts: dict[str, int] = {}
            for pr in providers:
                for entity in pr.entities:
                    entity_counts[entity] = entity_counts.get(entity, 0) + 1
            result.entities = [e for e, c in entity_counts.items() if c > threshold]

            result.confidence = sum(p.confidence for p in providers) / len(providers)

        # Compute agreement score
        result.agreement_score = self._compute_agreement(providers)

    def _compute_agreement(self, providers: list[ProviderResult]) -> float:
        """Compute agreement score between providers."""
        if len(providers) < 2:
            return 1.0

        # Compare obligation actions pairwise
        agreements = 0
        comparisons = 0
        for i in range(len(providers)):
            for j in range(i + 1, len(providers)):
                actions_i = {o.get("action", "") for o in providers[i].obligations}
                actions_j = {o.get("action", "") for o in providers[j].obligations}
                if actions_i or actions_j:
                    union = actions_i | actions_j
                    intersection = actions_i & actions_j
                    agreements += len(intersection) / len(union) if union else 1.0
                else:
                    agreements += 1.0
                comparisons += 1

        return agreements / comparisons if comparisons > 0 else 1.0

    def _deduplicate_obligations(self, obligations: list[dict]) -> list[dict]:
        """Remove duplicate obligations based on action key."""
        seen_actions: set[str] = set()
        unique = []
        for obl in obligations:
            action = obl.get("action", "")
            if action not in seen_actions:
                seen_actions.add(action)
                unique.append(obl)
        return unique

    def _extract_entities(self, ai_result: dict) -> list[str]:
        """Extract entities from AI response."""
        entities = set()
        for req in ai_result.get("requirements", []):
            if "subject" in req:
                entities.add(req["subject"])
        return sorted(entities)

    def _avg_confidence(self, ai_result: dict) -> float:
        """Get average confidence from AI response."""
        reqs = ai_result.get("requirements", [])
        if not reqs:
            return 0.0
        return sum(r.get("confidence", 0.5) for r in reqs) / len(reqs)
