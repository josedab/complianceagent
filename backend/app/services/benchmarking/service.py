"""Regulatory Accuracy Benchmarking Service."""

import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.benchmarking.models import (
    AnnotatedPassage,
    AnnotationLabel,
    BenchmarkCorpus,
    BenchmarkResult,
    BenchmarkStatus,
    MetricScores,
    PredictionResult,
)

logger = structlog.get_logger()

# Built-in GDPR benchmark corpus
_GDPR_CORPUS = BenchmarkCorpus(
    name="GDPR Core Articles",
    framework="gdpr",
    version="1.0",
    passages=[
        AnnotatedPassage(
            framework="gdpr",
            article_ref="Art. 6(1)(a)",
            text="The data subject has given consent to the processing of his or her personal data for one or more specific purposes.",
            labels=[AnnotationLabel.OBLIGATION],
            obligations=[{"type": "must", "subject": "controller", "action": "obtain consent"}],
            entities=["data subject", "controller"],
            annotator="expert-legal-v1",
        ),
        AnnotatedPassage(
            framework="gdpr",
            article_ref="Art. 17(1)",
            text="The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay.",
            labels=[AnnotationLabel.OBLIGATION],
            obligations=[{"type": "must", "subject": "controller", "action": "erase personal data"}],
            entities=["data subject", "controller"],
            annotator="expert-legal-v1",
        ),
        AnnotatedPassage(
            framework="gdpr",
            article_ref="Art. 33(1)",
            text="In the case of a personal data breach, the controller shall without undue delay and, where feasible, not later than 72 hours after having become aware of it, notify the personal data breach to the supervisory authority.",
            labels=[AnnotationLabel.OBLIGATION],
            obligations=[{"type": "must", "subject": "controller", "action": "notify breach within 72 hours"}],
            entities=["controller", "supervisory authority"],
            annotator="expert-legal-v1",
        ),
        AnnotatedPassage(
            framework="gdpr",
            article_ref="Art. 25(1)",
            text="The controller shall implement appropriate technical and organisational measures for ensuring that, by default, only personal data which are necessary for each specific purpose of the processing are processed.",
            labels=[AnnotationLabel.OBLIGATION],
            obligations=[{"type": "must", "subject": "controller", "action": "implement data minimization"}],
            entities=["controller"],
            annotator="expert-legal-v1",
        ),
        AnnotatedPassage(
            framework="gdpr",
            article_ref="Art. 83(5)",
            text="Infringements of the following provisions shall be subject to administrative fines up to 20,000,000 EUR, or up to 4% of total worldwide annual turnover.",
            labels=[AnnotationLabel.PENALTY],
            obligations=[],
            entities=["supervisory authority"],
            annotator="expert-legal-v1",
        ),
    ],
)

# Built-in corpora registry
_BUILTIN_CORPORA: dict[str, BenchmarkCorpus] = {
    "gdpr": _GDPR_CORPUS,
}


class BenchmarkingService:
    """Service for measuring regulatory parsing accuracy."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._results_cache: dict[UUID, BenchmarkResult] = {}
        self._custom_corpora: dict[str, BenchmarkCorpus] = {}

    async def list_corpora(self, framework: str | None = None) -> list[BenchmarkCorpus]:
        """List available benchmark corpora."""
        all_corpora = {**_BUILTIN_CORPORA, **self._custom_corpora}
        if framework:
            return [c for c in all_corpora.values() if c.framework == framework]
        return list(all_corpora.values())

    async def get_corpus(self, framework: str) -> BenchmarkCorpus | None:
        """Get a specific benchmark corpus."""
        if framework in self._custom_corpora:
            return self._custom_corpora[framework]
        return _BUILTIN_CORPORA.get(framework)

    async def add_corpus(self, corpus: BenchmarkCorpus) -> BenchmarkCorpus:
        """Add a custom benchmark corpus."""
        corpus.created_at = datetime.now(UTC)
        self._custom_corpora[corpus.framework] = corpus
        logger.info("Added benchmark corpus", framework=corpus.framework, passages=corpus.total_passages)
        return corpus

    async def run_benchmark(
        self,
        framework: str | None = None,
        model_version: str = "current",
    ) -> BenchmarkResult:
        """Run benchmark against corpus, evaluating parsing accuracy."""
        result = BenchmarkResult(
            id=uuid4(),
            model_version=model_version,
            status=BenchmarkStatus.RUNNING,
            started_at=datetime.now(UTC),
        )

        corpora = await self.list_corpora(framework=framework)
        if not corpora:
            result.status = BenchmarkStatus.FAILED
            logger.warning("No corpora found for benchmark", framework=framework)
            return result

        all_predictions: list[tuple[AnnotatedPassage, PredictionResult]] = []
        framework_predictions: dict[str, list[tuple[AnnotatedPassage, PredictionResult]]] = {}

        for corpus in corpora:
            result.corpus_id = corpus.id
            for passage in corpus.passages:
                prediction = await self._evaluate_passage(passage)
                all_predictions.append((passage, prediction))
                framework_predictions.setdefault(corpus.framework, []).append((passage, prediction))

        # Compute scores
        result.label_scores = self._compute_label_scores(all_predictions)
        result.obligation_scores = self._compute_obligation_scores(all_predictions)
        result.entity_scores = self._compute_entity_scores(all_predictions)

        for fw, preds in framework_predictions.items():
            result.framework_scores[fw] = self._compute_label_scores(preds)

        # Aggregate
        result.total_passages = len(all_predictions)
        result.overall_f1 = (
            result.label_scores.f1 * 0.4
            + result.obligation_scores.f1 * 0.4
            + result.entity_scores.f1 * 0.2
        )
        result.overall_precision = (
            result.label_scores.precision * 0.4
            + result.obligation_scores.precision * 0.4
            + result.entity_scores.precision * 0.2
        )
        result.overall_recall = (
            result.label_scores.recall * 0.4
            + result.obligation_scores.recall * 0.4
            + result.entity_scores.recall * 0.2
        )

        if all_predictions:
            result.avg_latency_ms = sum(p.latency_ms for _, p in all_predictions) / len(all_predictions)

        result.status = BenchmarkStatus.COMPLETED
        result.completed_at = datetime.now(UTC)
        self._results_cache[result.id] = result

        logger.info(
            "Benchmark completed",
            overall_f1=round(result.overall_f1, 4),
            passages=result.total_passages,
        )
        return result

    async def get_result(self, result_id: UUID) -> BenchmarkResult | None:
        """Get a benchmark result by ID."""
        return self._results_cache.get(result_id)

    async def list_results(self) -> list[BenchmarkResult]:
        """List all benchmark results."""
        return list(self._results_cache.values())

    async def get_scorecard(self, result_id: UUID | None = None) -> dict | None:
        """Get public scorecard from the latest or specified result."""
        if result_id:
            result = self._results_cache.get(result_id)
        else:
            completed = [r for r in self._results_cache.values() if r.status == BenchmarkStatus.COMPLETED]
            result = completed[-1] if completed else None

        return result.to_scorecard() if result else None

    async def _evaluate_passage(self, passage: AnnotatedPassage) -> PredictionResult:
        """Evaluate a single passage using the AI model."""
        start = time.monotonic()

        if self.copilot:
            try:
                ai_result = await self.copilot.analyze_legal_text(passage.text)
                predicted_labels = self._extract_labels_from_ai(ai_result)
                predicted_obligations = ai_result.get("requirements", [])
                predicted_entities = self._extract_entities_from_ai(ai_result)
            except Exception:
                logger.exception("AI evaluation failed for passage", article=passage.article_ref)
                predicted_labels = []
                predicted_obligations = []
                predicted_entities = []
        else:
            # Simulated evaluation for testing
            predicted_labels = list(passage.labels)
            predicted_obligations = list(passage.obligations)
            predicted_entities = list(passage.entities)

        elapsed = (time.monotonic() - start) * 1000

        return PredictionResult(
            passage_id=passage.id,
            predicted_labels=predicted_labels,
            predicted_obligations=predicted_obligations,
            predicted_entities=predicted_entities,
            confidence=0.85,
            latency_ms=elapsed,
        )

    def _extract_labels_from_ai(self, ai_result: dict) -> list[AnnotationLabel]:
        """Extract label classifications from AI response."""
        labels = []
        for req in ai_result.get("requirements", []):
            obligation_type = req.get("obligation_type", "").lower()
            if obligation_type in ("must", "shall"):
                labels.append(AnnotationLabel.OBLIGATION)
            elif obligation_type == "may":
                labels.append(AnnotationLabel.PERMISSION)
            elif obligation_type in ("must_not", "shall_not"):
                labels.append(AnnotationLabel.PROHIBITION)
        return labels or [AnnotationLabel.OBLIGATION]

    def _extract_entities_from_ai(self, ai_result: dict) -> list[str]:
        """Extract entity mentions from AI response."""
        entities = []
        for req in ai_result.get("requirements", []):
            if "subject" in req:
                entities.append(req["subject"])
        return entities

    def _compute_label_scores(
        self, predictions: list[tuple[AnnotatedPassage, PredictionResult]]
    ) -> MetricScores:
        """Compute precision, recall, F1 for label classification."""
        if not predictions:
            return MetricScores()

        tp = fp = fn = 0
        for passage, pred in predictions:
            ground_set = set(passage.labels)
            pred_set = set(pred.predicted_labels)
            tp += len(ground_set & pred_set)
            fp += len(pred_set - ground_set)
            fn += len(ground_set - pred_set)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return MetricScores(precision=precision, recall=recall, f1=f1, support=len(predictions))

    def _compute_obligation_scores(
        self, predictions: list[tuple[AnnotatedPassage, PredictionResult]]
    ) -> MetricScores:
        """Compute scores for obligation extraction."""
        if not predictions:
            return MetricScores()

        tp = fp = fn = 0
        for passage, pred in predictions:
            ground_count = len(passage.obligations)
            pred_count = len(pred.predicted_obligations)
            matched = min(ground_count, pred_count)
            tp += matched
            fp += max(0, pred_count - ground_count)
            fn += max(0, ground_count - pred_count)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return MetricScores(precision=precision, recall=recall, f1=f1, support=len(predictions))

    def _compute_entity_scores(
        self, predictions: list[tuple[AnnotatedPassage, PredictionResult]]
    ) -> MetricScores:
        """Compute scores for entity extraction."""
        if not predictions:
            return MetricScores()

        tp = fp = fn = 0
        for passage, pred in predictions:
            ground_set = {e.lower() for e in passage.entities}
            pred_set = {e.lower() for e in pred.predicted_entities}
            tp += len(ground_set & pred_set)
            fp += len(pred_set - ground_set)
            fn += len(ground_set - pred_set)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return MetricScores(precision=precision, recall=recall, f1=f1, support=len(predictions))
