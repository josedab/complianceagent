"""Multi-LLM Regulatory Parsing Engine Service."""

import asyncio
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.multi_llm.models import (
    ConsensusResult,
    ConsensusStrategy,
    CostOptimizationRecommendation,
    DivergenceDetail,
    DivergenceReport,
    EscalationPriority,
    EscalationStatus,
    EscalationTicket,
    FailoverEvent,
    LLMProvider,
    MultiLLMConfig,
    ParseStatus,
    ProviderConfig,
    ProviderHealthMetrics,
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
        self._latency_history: dict[str, list[float]] = {}
        self._request_counts: dict[str, int] = {}
        self._error_counts: dict[str, int] = {}
        self._last_errors: dict[str, str] = {}
        self._token_usage: dict[str, int] = {}
        self._escalations: dict[UUID, EscalationTicket] = {}
        self._failover_events: list[FailoverEvent] = []

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

    async def get_provider_health(self) -> list[ProviderHealthMetrics]:
        """Get health metrics for all configured providers."""
        metrics = []
        cost_rates = {
            LLMProvider.COPILOT: 0.003,
            LLMProvider.OPENAI: 0.010,
            LLMProvider.ANTHROPIC: 0.015,
            LLMProvider.LOCAL: 0.0,
        }

        for provider_config in self.config.providers:
            key = provider_config.provider.value
            latencies = self._latency_history.get(key, [])
            total = self._request_counts.get(key, 0)
            errors = self._error_counts.get(key, 0)
            tokens = self._token_usage.get(key, 0)
            cost_rate = cost_rates.get(provider_config.provider, 0.01)

            sorted_lat = sorted(latencies) if latencies else [0.0]
            p95_idx = int(len(sorted_lat) * 0.95)
            p99_idx = int(len(sorted_lat) * 0.99)

            status = "healthy"
            if total > 0 and errors / total > 0.5:
                status = "unhealthy"
            elif total > 0 and errors / total > 0.1:
                status = "degraded"

            metrics.append(ProviderHealthMetrics(
                provider=provider_config.provider,
                model_name=provider_config.model_name,
                status=status,
                avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
                p95_latency_ms=sorted_lat[p95_idx] if latencies else 0.0,
                p99_latency_ms=sorted_lat[p99_idx] if latencies else 0.0,
                success_rate=(total - errors) / total if total > 0 else 1.0,
                total_requests=total,
                failed_requests=errors,
                last_error=self._last_errors.get(key),
                last_check=datetime.now(UTC),
                cost_per_1k_tokens=cost_rate,
                total_tokens_used=tokens,
                estimated_monthly_cost=tokens * cost_rate / 1000,
            ))

        return metrics

    async def get_cost_recommendations(self) -> list[CostOptimizationRecommendation]:
        """Generate cost optimization recommendations."""
        recommendations = []
        health = await self.get_provider_health()

        total_monthly = sum(m.estimated_monthly_cost for m in health)

        # Check for underused expensive providers
        for m in health:
            if m.cost_per_1k_tokens > 0.01 and m.success_rate < 0.9:
                recommendations.append(CostOptimizationRecommendation(
                    title=f"Reduce usage of {m.provider.value}",
                    description=f"{m.provider.value} has {m.success_rate:.0%} success rate at ${m.cost_per_1k_tokens}/1k tokens. "
                                f"Consider reducing weight or disabling to save costs.",
                    estimated_savings_monthly=m.estimated_monthly_cost * 0.5,
                    effort="low",
                    current_cost=m.estimated_monthly_cost,
                    optimized_cost=m.estimated_monthly_cost * 0.5,
                ))

        # Suggest local LLM for simple parsing
        if total_monthly > 100 and not any(m.provider == LLMProvider.LOCAL for m in health):
            recommendations.append(CostOptimizationRecommendation(
                title="Add local LLM for simple parsing",
                description="Route simple regulation parsing to a local model (e.g., Llama 3) "
                            "to reduce cloud API costs for non-critical tasks.",
                estimated_savings_monthly=total_monthly * 0.3,
                effort="medium",
                current_cost=total_monthly,
                optimized_cost=total_monthly * 0.7,
            ))

        # Suggest caching strategy
        cache_size = len(self._results_cache)
        if cache_size > 0:
            recommendations.append(CostOptimizationRecommendation(
                title="Enable semantic caching",
                description="Cache similar regulation queries to avoid duplicate LLM calls. "
                            f"Currently {cache_size} results cached. Enable similarity matching "
                            "to reuse results for similar regulatory text.",
                estimated_savings_monthly=total_monthly * 0.15,
                effort="low",
                current_cost=total_monthly,
                optimized_cost=total_monthly * 0.85,
            ))

        return recommendations

    # ── Semantic Divergence Detection ────────────────────────────────────

    def analyze_divergence(
        self,
        consensus_id: str,
    ) -> DivergenceReport:
        """Analyze semantic divergence in a consensus result."""
        result = self._results_cache.get(UUID(consensus_id)) if consensus_id else None
        if not result:
            return DivergenceReport(consensus_id=consensus_id)

        provider_results = result.provider_results
        if len(provider_results) < 2:
            return DivergenceReport(
                consensus_id=consensus_id,
                total_obligations=len(result.obligations),
                agreed_count=len(result.obligations),
                diverged_count=0,
                divergence_rate=0.0,
                needs_human_review=False,
                severity="low",
            )

        divergences: list[DivergenceDetail] = []
        all_obligation_texts: set[str] = set()

        for pr in provider_results:
            for obl in pr.obligations:
                text = obl.get("text", obl.get("description", str(obl)))
                all_obligation_texts.add(text[:100])

        for obl_text in all_obligation_texts:
            agreeing = []
            disagreeing = []
            for pr in provider_results:
                pr_texts = [
                    o.get("text", o.get("description", str(o)))[:100]
                    for o in pr.obligations
                ]
                if obl_text in pr_texts or any(obl_text[:50] in t for t in pr_texts):
                    agreeing.append(pr.provider.value)
                else:
                    disagreeing.append(pr.provider.value)

            ratio = len(agreeing) / len(provider_results) if provider_results else 0
            if ratio < 1.0 and disagreeing:
                div_type = "omission" if ratio < 0.5 else "interpretation"
                divergences.append(DivergenceDetail(
                    obligation_text=obl_text,
                    providers_agree=agreeing,
                    providers_disagree=disagreeing,
                    agreement_ratio=round(ratio, 3),
                    divergence_type=div_type,
                    recommended_action="human_review" if ratio < 0.5 else "auto_resolve",
                    auto_escalated=ratio < 0.3,
                ))

        diverged_count = len(divergences)
        total = max(len(all_obligation_texts), 1)
        divergence_rate = round(diverged_count / total, 3)

        if divergence_rate > 0.5:
            severity = "critical"
        elif divergence_rate > 0.3:
            severity = "high"
        elif divergence_rate > 0.1:
            severity = "medium"
        else:
            severity = "low"

        return DivergenceReport(
            consensus_id=consensus_id,
            total_obligations=total,
            agreed_count=total - diverged_count,
            diverged_count=diverged_count,
            divergence_rate=divergence_rate,
            divergences=divergences,
            needs_human_review=severity in ("critical", "high"),
            severity=severity,
        )

    # ── Provider Health Dashboard ────────────────────────────────────────

    def get_provider_health_dashboard(self) -> list[dict[str, Any]]:
        """Get dashboard-style health metrics for all configured providers."""
        dashboard = []
        cost_per_1k = {
            LLMProvider.COPILOT: 0.002,
            LLMProvider.OPENAI: 0.003,
            LLMProvider.ANTHROPIC: 0.003,
            LLMProvider.LOCAL: 0.0,
        }

        for provider_config in self.config.providers:
            key = provider_config.provider.value
            latencies = self._latency_history.get(key, [])
            total = self._request_counts.get(key, 0)
            errors = self._error_counts.get(key, 0)
            successes = total - errors
            tokens = self._token_usage.get(key, 0)

            success_rate = round(successes / max(total, 1), 3)
            avg_lat = round(sum(latencies) / max(len(latencies), 1), 2)
            sorted_lat = sorted(latencies) if latencies else []
            p95_lat = round(
                sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0.0,
                2,
            )
            rate = cost_per_1k.get(provider_config.provider, 0.002)
            estimated_cost = round(tokens / 1000 * rate, 4)

            dashboard.append({
                "provider": key,
                "model_name": provider_config.model_name,
                "enabled": provider_config.enabled,
                "total_requests": total,
                "successful_requests": successes,
                "failed_requests": errors,
                "success_rate": success_rate,
                "avg_latency_ms": avg_lat,
                "p95_latency_ms": p95_lat,
                "total_tokens_used": tokens,
                "estimated_cost_usd": estimated_cost,
                "last_error": self._last_errors.get(key),
                "last_used": None,
                "uptime_percentage": round(success_rate * 100, 1),
            })

        return dashboard

    async def _run_provider(
        self, config: ProviderConfig, text: str, framework: str
    ) -> ProviderResult:
        """Run parsing with a single provider, with failover tracking."""
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

            # Record failover event
            other_providers = [
                p for p in self.config.providers
                if p.enabled and p.provider != config.provider
            ]
            failover_target = other_providers[0].provider.value if other_providers else "none"
            failover_event = FailoverEvent(
                failed_provider=config.provider.value,
                failover_provider=failover_target,
                reason=str(e),
                latency_ms=(time.monotonic() - start) * 1000,
            )
            self._failover_events.append(failover_event)
            logger.warning(
                "Failover event recorded",
                failed_provider=config.provider.value,
                failover_provider=failover_target,
            )

        result.latency_ms = (time.monotonic() - start) * 1000

        # Track metrics
        key = config.provider.value
        self._request_counts[key] = self._request_counts.get(key, 0) + 1
        if key not in self._latency_history:
            self._latency_history[key] = []
        self._latency_history[key].append(result.latency_ms)
        # Keep last 1000 latency samples
        if len(self._latency_history[key]) > 1000:
            self._latency_history[key] = self._latency_history[key][-1000:]
        self._token_usage[key] = self._token_usage.get(key, 0) + len(text.split()) * 2
        if result.error:
            self._error_counts[key] = self._error_counts.get(key, 0) + 1
            self._last_errors[key] = result.error

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

    # ── Human Escalation & Provider Failover ─────────────────────────────

    async def escalate_for_review(
        self, consensus_id: UUID, reason: str = ""
    ) -> EscalationTicket:
        """Create an escalation ticket from a low-confidence consensus result."""
        result = self._results_cache.get(consensus_id)
        if not result:
            msg = f"Consensus result {consensus_id} not found"
            raise ValueError(msg)

        # Build provider interpretation summaries
        interpretations = [
            {
                "provider": pr.provider.value,
                "model_name": pr.model_name,
                "obligations": pr.obligations,
                "entities": pr.entities,
                "confidence": pr.confidence,
            }
            for pr in result.provider_results
            if pr.error is None
        ]

        # Auto-determine priority based on scores
        if result.agreement_score < 0.3 or result.confidence < 0.3:
            priority = EscalationPriority.CRITICAL
        elif result.agreement_score < 0.5 or result.confidence < 0.5:
            priority = EscalationPriority.HIGH
        elif result.agreement_score < 0.7 or result.confidence < 0.7:
            priority = EscalationPriority.MEDIUM
        else:
            priority = EscalationPriority.LOW

        divergence_summary = reason or (
            f"Agreement score {result.agreement_score:.2f}, "
            f"confidence {result.confidence:.2f}. "
            f"{len(result.divergent_items)} divergent items across "
            f"{len(result.provider_results)} providers."
        )

        ticket = EscalationTicket(
            consensus_id=consensus_id,
            provider_interpretations=interpretations,
            agreement_score=result.agreement_score,
            confidence_score=result.confidence,
            divergence_summary=divergence_summary,
            priority=priority,
        )
        self._escalations[ticket.id] = ticket

        logger.info(
            "Escalation ticket created",
            ticket_id=str(ticket.id),
            consensus_id=str(consensus_id),
            priority=priority.value,
        )
        return ticket

    async def list_escalations(
        self, status: EscalationStatus | None = None
    ) -> list[EscalationTicket]:
        """List escalation tickets, optionally filtered by status."""
        tickets = list(self._escalations.values())
        if status is not None:
            tickets = [t for t in tickets if t.status == status]
        return sorted(tickets, key=lambda t: t.created_at, reverse=True)

    async def resolve_escalation(
        self,
        ticket_id: UUID,
        resolution: str,
        resolved_obligations: list[dict],
        resolved_by: str,
    ) -> EscalationTicket:
        """Resolve an escalation ticket with human-provided interpretation."""
        ticket = self._escalations.get(ticket_id)
        if not ticket:
            msg = f"Escalation ticket {ticket_id} not found"
            raise ValueError(msg)

        ticket.status = EscalationStatus.RESOLVED
        ticket.resolution = resolution
        ticket.resolved_obligations = resolved_obligations
        ticket.assigned_to = resolved_by
        ticket.resolved_at = datetime.now(UTC)

        # Update the cached consensus result with human-verified interpretation
        consensus = self._results_cache.get(ticket.consensus_id)
        if consensus:
            consensus.obligations = resolved_obligations
            consensus.needs_human_review = False
            consensus.status = ParseStatus.COMPLETED

        logger.info(
            "Escalation resolved",
            ticket_id=str(ticket_id),
            resolved_by=resolved_by,
        )
        return ticket

    async def get_failover_history(self, limit: int = 50) -> list[FailoverEvent]:
        """Return recent provider failover events."""
        return sorted(
            self._failover_events, key=lambda e: e.occurred_at, reverse=True
        )[:limit]
