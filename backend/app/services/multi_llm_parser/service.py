"""Multi-LLM Compliance Parsing Service."""

import hashlib
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.multi_llm_parser.models import (
    ConsensusResult,
    ConsensusStrategy,
    LLMProvider,
    ParserStats,
    ParseStatus,
    ProviderConfig,
    ProviderResult,
)


logger = structlog.get_logger()

_DEFAULT_PROVIDERS: list[ProviderConfig] = [
    ProviderConfig(provider=LLMProvider.COPILOT, model="copilot-4", weight=1.0),
    ProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4o", weight=0.9),
    ProviderConfig(provider=LLMProvider.ANTHROPIC, model="claude-sonnet-4-20250514", weight=0.85),
]


class MultiLLMParserService:
    """Multi-LLM compliance parsing with consensus voting."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._providers = list(_DEFAULT_PROVIDERS)
        self._results: list[ConsensusResult] = []

    async def parse_legal_text(
        self,
        text: str,
        strategy: str = "majority_vote",
        providers: list[str] | None = None,
    ) -> ConsensusResult:
        start = datetime.now(UTC)
        strat = ConsensusStrategy(strategy)
        active = [p for p in self._providers if p.enabled]
        if providers:
            active = [p for p in active if p.provider.value in providers]

        # Simulate provider results (deterministic based on text hash)
        provider_results = []
        for prov in active:
            result = self._simulate_provider(prov, text)
            provider_results.append(result)

        # Build consensus
        consensus_reqs, agreement, divergences = self._build_consensus(provider_results, strat)
        status = ParseStatus.SUCCESS if agreement >= 0.8 else ParseStatus.DIVERGENT if agreement >= 0.5 else ParseStatus.PARTIAL
        final_conf = sum(r.confidence * next((p.weight for p in self._providers if p.provider == r.provider), 1.0) for r in provider_results) / max(1, sum(next((p.weight for p in self._providers if p.provider == r.provider), 1.0) for r in provider_results))
        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        result = ConsensusResult(
            text_input=text[:200],
            strategy=strat,
            status=status,
            consensus_requirements=consensus_reqs,
            provider_results=provider_results,
            agreement_rate=round(agreement, 3),
            divergences=divergences,
            final_confidence=round(final_conf, 3),
            total_latency_ms=round(duration, 2),
            parsed_at=datetime.now(UTC),
        )
        self._results.append(result)
        logger.info("Multi-LLM parse completed", providers=len(provider_results), agreement=agreement, status=status.value)
        return result

    def _simulate_provider(self, prov: ProviderConfig, text: str) -> ProviderResult:
        text_hash = int(hashlib.sha256(f"{prov.provider.value}:{text}".encode()).hexdigest()[:8], 16)
        confidence = 0.7 + (text_hash % 25) / 100

        # Extract requirements based on text analysis
        requirements = []
        obligation_words = {"must": "mandatory", "shall": "mandatory", "should": "recommended", "may": "optional"}
        for word, level in obligation_words.items():
            if word in text.lower():
                requirements.append({
                    "obligation": level,
                    "text": f"Extracted from '{word}' clause",
                    "confidence": round(confidence, 2),
                    "provider": prov.provider.value,
                })

        if not requirements:
            requirements.append({
                "obligation": "informational",
                "text": "General compliance requirement identified",
                "confidence": round(confidence * 0.8, 2),
                "provider": prov.provider.value,
            })

        latency = 50 + (text_hash % 200)
        return ProviderResult(
            provider=prov.provider,
            model=prov.model,
            requirements=requirements,
            confidence=round(confidence, 3),
            latency_ms=float(latency),
        )

    def _build_consensus(
        self, results: list[ProviderResult], strategy: ConsensusStrategy
    ) -> tuple[list[dict], float, list[dict]]:
        if not results:
            return [], 0.0, []

        # Collect all unique requirement obligations
        all_obligations: dict[str, int] = {}
        for r in results:
            for req in r.requirements:
                obl = req["obligation"]
                all_obligations[obl] = all_obligations.get(obl, 0) + 1

        # Build consensus based on strategy
        total_providers = len(results)
        consensus = []
        divergences = []

        for obl, count in all_obligations.items():
            agreement = count / total_providers
            if strategy == ConsensusStrategy.MAJORITY_VOTE and agreement >= 0.5:
                consensus.append({"obligation": obl, "agreement": round(agreement, 2), "providers_agreed": count})
            elif strategy == ConsensusStrategy.UNANIMOUS and agreement == 1.0:
                consensus.append({"obligation": obl, "agreement": 1.0, "providers_agreed": count})
            elif strategy in (ConsensusStrategy.HIGHEST_CONFIDENCE, ConsensusStrategy.WEIGHTED_AVERAGE):
                consensus.append({"obligation": obl, "agreement": round(agreement, 2), "providers_agreed": count})
            elif agreement < 0.5:
                divergences.append({"obligation": obl, "agreement": round(agreement, 2), "reason": f"Only {count}/{total_providers} providers agreed"})

        overall_agreement = sum(all_obligations.values()) / (len(all_obligations) * total_providers) if all_obligations else 0.0
        return consensus, round(overall_agreement, 3), divergences

    def list_providers(self) -> list[ProviderConfig]:
        return list(self._providers)

    async def toggle_provider(self, provider: str, enabled: bool) -> ProviderConfig | None:
        for p in self._providers:
            if p.provider.value == provider:
                p.enabled = enabled
                return p
        return None

    def get_stats(self) -> ParserStats:
        by_provider: dict[str, int] = {}
        by_strategy: dict[str, int] = {}
        agreements: list[float] = []
        confidences: list[float] = []
        divs = 0

        for r in self._results:
            by_strategy[r.strategy.value] = by_strategy.get(r.strategy.value, 0) + 1
            agreements.append(r.agreement_rate)
            confidences.append(r.final_confidence)
            divs += len(r.divergences)
            for pr in r.provider_results:
                by_provider[pr.provider.value] = by_provider.get(pr.provider.value, 0) + 1

        return ParserStats(
            total_parses=len(self._results),
            by_provider=by_provider,
            by_strategy=by_strategy,
            avg_agreement_rate=round(sum(agreements) / len(agreements), 3) if agreements else 0.0,
            avg_confidence=round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
            divergence_count=divs,
        )
