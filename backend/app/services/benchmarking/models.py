"""Regulatory accuracy benchmarking models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class BenchmarkStatus(str, Enum):
    """Benchmark run status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnnotationLabel(str, Enum):
    """Expert annotation label types."""

    OBLIGATION = "obligation"
    PERMISSION = "permission"
    PROHIBITION = "prohibition"
    DEFINITION = "definition"
    SCOPE = "scope"
    EXEMPTION = "exemption"
    PENALTY = "penalty"


@dataclass
class AnnotatedPassage:
    """An expert-annotated regulatory passage."""

    id: UUID = field(default_factory=uuid4)
    framework: str = ""
    article_ref: str = ""
    text: str = ""
    labels: list[AnnotationLabel] = field(default_factory=list)
    obligations: list[dict] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    annotator: str = ""
    confidence: float = 1.0


@dataclass
class BenchmarkCorpus:
    """A collection of annotated passages for benchmarking."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    framework: str = ""
    version: str = "1.0"
    passages: list[AnnotatedPassage] = field(default_factory=list)
    created_at: datetime | None = None

    @property
    def total_passages(self) -> int:
        return len(self.passages)


@dataclass
class PredictionResult:
    """Model prediction for a single passage."""

    passage_id: UUID = field(default_factory=uuid4)
    predicted_labels: list[AnnotationLabel] = field(default_factory=list)
    predicted_obligations: list[dict] = field(default_factory=list)
    predicted_entities: list[str] = field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float = 0.0


@dataclass
class MetricScores:
    """Precision, recall, F1 for a metric."""

    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    support: int = 0


@dataclass
class BenchmarkResult:
    """Results of a benchmark run."""

    id: UUID = field(default_factory=uuid4)
    corpus_id: UUID = field(default_factory=uuid4)
    model_version: str = ""
    status: BenchmarkStatus = BenchmarkStatus.PENDING

    # Scores by category
    label_scores: MetricScores = field(default_factory=MetricScores)
    obligation_scores: MetricScores = field(default_factory=MetricScores)
    entity_scores: MetricScores = field(default_factory=MetricScores)

    # Per-framework breakdown
    framework_scores: dict[str, MetricScores] = field(default_factory=dict)

    # Aggregate
    overall_f1: float = 0.0
    overall_precision: float = 0.0
    overall_recall: float = 0.0
    avg_latency_ms: float = 0.0
    total_passages: int = 0
    errors: int = 0

    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_scorecard(self) -> dict:
        """Generate public scorecard data."""
        return {
            "model_version": self.model_version,
            "overall": {
                "f1": round(self.overall_f1, 4),
                "precision": round(self.overall_precision, 4),
                "recall": round(self.overall_recall, 4),
            },
            "labels": {
                "f1": round(self.label_scores.f1, 4),
                "precision": round(self.label_scores.precision, 4),
                "recall": round(self.label_scores.recall, 4),
            },
            "obligations": {
                "f1": round(self.obligation_scores.f1, 4),
                "precision": round(self.obligation_scores.precision, 4),
                "recall": round(self.obligation_scores.recall, 4),
            },
            "entities": {
                "f1": round(self.entity_scores.f1, 4),
                "precision": round(self.entity_scores.precision, 4),
                "recall": round(self.entity_scores.recall, 4),
            },
            "frameworks": {
                fw: {"f1": round(s.f1, 4), "precision": round(s.precision, 4), "recall": round(s.recall, 4)}
                for fw, s in self.framework_scores.items()
            },
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "total_passages": self.total_passages,
        }
