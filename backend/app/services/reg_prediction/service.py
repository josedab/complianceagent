"""Regulatory Impact Prediction Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.reg_prediction.models import (
    EarlyWarning,
    ImpactSeverity,
    PredictionAccuracy,
    PredictionConfidence,
    RegPrediction,
    RegulatorySignal,
    SignalType,
)


logger = structlog.get_logger()

_SEED_PREDICTIONS: list[RegPrediction] = [
    RegPrediction(
        title="GDPR Article 22 Amendment — Expanded AI Decision-Making Rules",
        description="Strong signals indicate the European Commission will propose amendments to Article 22, expanding requirements for automated decision-making to cover all AI-assisted decisions, not just solely automated ones.",
        jurisdiction="EU",
        affected_frameworks=["GDPR", "EU AI Act"],
        confidence=PredictionConfidence.HIGH,
        confidence_score=0.82,
        impact_severity=ImpactSeverity.MAJOR,
        predicted_effective_date="2027-Q1",
        prediction_horizon_months=10,
        supporting_signals=["EDPB guidelines consultation (2026-01)", "EP committee draft proposal (2025-11)", "CJEU ruling on automated decisions (2025-09)"],
        preparation_tasks=[
            {"task": "Audit all AI-assisted decision endpoints", "priority": "high"},
            {"task": "Implement human-in-the-loop for affected workflows", "priority": "high"},
            {"task": "Document explainability for AI features", "priority": "medium"},
        ],
        predicted_at=datetime(2026, 2, 15, tzinfo=UTC),
    ),
    RegPrediction(
        title="US Federal Privacy Law (APRA) — Comprehensive Data Privacy",
        description="Bipartisan momentum suggests a federal privacy law combining elements of CCPA, GDPR, and sector-specific rules with nationwide preemption.",
        jurisdiction="US",
        affected_frameworks=["CCPA", "HIPAA"],
        confidence=PredictionConfidence.MEDIUM,
        confidence_score=0.58,
        impact_severity=ImpactSeverity.TRANSFORMATIVE,
        predicted_effective_date="2028-Q2",
        prediction_horizon_months=24,
        supporting_signals=["Congressional hearing transcripts (2026-01)", "FTC enforcement trends (2025-2026)", "Industry lobbying disclosures"],
        preparation_tasks=[
            {"task": "Map all personal data processing across products", "priority": "high"},
            {"task": "Implement universal opt-out mechanisms", "priority": "medium"},
            {"task": "Prepare cross-state compliance unification", "priority": "low"},
        ],
        predicted_at=datetime(2026, 2, 10, tzinfo=UTC),
    ),
    RegPrediction(
        title="PCI-DSS v5.0 — Post-Quantum Cryptography Requirements",
        description="The PCI SSC is expected to mandate post-quantum cryptographic algorithms for card data protection, requiring migration from RSA/ECC.",
        jurisdiction="Global",
        affected_frameworks=["PCI-DSS"],
        confidence=PredictionConfidence.MEDIUM,
        confidence_score=0.65,
        impact_severity=ImpactSeverity.MAJOR,
        predicted_effective_date="2028-Q1",
        prediction_horizon_months=20,
        supporting_signals=["NIST post-quantum standards finalized (2024)", "PCI SSC working group formed (2025-06)", "Visa cryptographic roadmap (2025)"],
        preparation_tasks=[
            {"task": "Inventory all cryptographic implementations", "priority": "high"},
            {"task": "Test post-quantum TLS libraries (ML-KEM)", "priority": "medium"},
            {"task": "Plan key management system upgrade", "priority": "medium"},
        ],
        predicted_at=datetime(2026, 2, 1, tzinfo=UTC),
    ),
    RegPrediction(
        title="HIPAA Modernization — Cybersecurity Requirements",
        description="HHS proposed rule strengthening HIPAA Security Rule with mandatory MFA, encryption, and 72-hour incident reporting.",
        jurisdiction="US",
        affected_frameworks=["HIPAA"],
        confidence=PredictionConfidence.HIGH,
        confidence_score=0.88,
        impact_severity=ImpactSeverity.MAJOR,
        predicted_effective_date="2026-Q4",
        prediction_horizon_months=8,
        supporting_signals=["HHS Notice of Proposed Rulemaking (2024-12)", "Public comment period closed (2025-03)", "Congressional support statements"],
        preparation_tasks=[
            {"task": "Enable MFA on all PHI access points", "priority": "critical"},
            {"task": "Implement 72-hour incident reporting pipeline", "priority": "high"},
            {"task": "Encrypt all PHI at rest with AES-256", "priority": "high"},
        ],
        predicted_at=datetime(2026, 1, 20, tzinfo=UTC),
    ),
    RegPrediction(
        title="NIS2 Enforcement Escalation — Supply Chain Security",
        description="EU member states are expected to increase NIS2 enforcement focus on software supply chain security, requiring SBOMs and vendor assessments.",
        jurisdiction="EU",
        affected_frameworks=["NIS2", "SOC 2"],
        confidence=PredictionConfidence.HIGH,
        confidence_score=0.78,
        impact_severity=ImpactSeverity.MODERATE,
        predicted_effective_date="2026-Q3",
        prediction_horizon_months=4,
        supporting_signals=["ENISA supply chain guidance (2026-01)", "German BSI enforcement notices (2025-12)", "EU CRA implementation timeline"],
        preparation_tasks=[
            {"task": "Generate SBOM for all production artifacts", "priority": "high"},
            {"task": "Assess all third-party vendor compliance", "priority": "medium"},
            {"task": "Implement dependency vulnerability monitoring", "priority": "medium"},
        ],
        predicted_at=datetime(2026, 2, 18, tzinfo=UTC),
    ),
]

_SEED_SIGNALS: list[RegulatorySignal] = [
    RegulatorySignal(signal_type=SignalType.CONSULTATION, source="EDPB", jurisdiction="EU", title="EDPB launches consultation on AI-assisted decisions", relevance_score=0.92, detected_at=datetime(2026, 1, 15, tzinfo=UTC)),
    RegulatorySignal(signal_type=SignalType.LEGISLATIVE, source="US Congress", jurisdiction="US", title="APRA bill reintroduced with bipartisan support", relevance_score=0.75, detected_at=datetime(2026, 1, 20, tzinfo=UTC)),
    RegulatorySignal(signal_type=SignalType.ENFORCEMENT, source="HHS OCR", jurisdiction="US", title="HHS increases HIPAA audit frequency for cloud providers", relevance_score=0.88, detected_at=datetime(2026, 2, 1, tzinfo=UTC)),
    RegulatorySignal(signal_type=SignalType.GUIDANCE, source="PCI SSC", jurisdiction="Global", title="PCI SSC publishes post-quantum migration guidance", relevance_score=0.70, detected_at=datetime(2026, 2, 5, tzinfo=UTC)),
    RegulatorySignal(signal_type=SignalType.AMENDMENT, source="ENISA", jurisdiction="EU", title="ENISA updates NIS2 supply chain security guidelines", relevance_score=0.82, detected_at=datetime(2026, 2, 10, tzinfo=UTC)),
]


class RegPredictionService:
    """ML-based regulatory impact prediction with early warnings."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._predictions: list[RegPrediction] = list(_SEED_PREDICTIONS)
        self._signals: list[RegulatorySignal] = list(_SEED_SIGNALS)
        self._warnings: list[EarlyWarning] = []

    def list_predictions(
        self,
        jurisdiction: str | None = None,
        confidence: PredictionConfidence | None = None,
        framework: str | None = None,
        limit: int = 20,
    ) -> list[RegPrediction]:
        results = list(self._predictions)
        if jurisdiction:
            results = [p for p in results if p.jurisdiction == jurisdiction]
        if confidence:
            results = [p for p in results if p.confidence == confidence]
        if framework:
            results = [p for p in results if framework in p.affected_frameworks]
        return sorted(results, key=lambda p: p.confidence_score, reverse=True)[:limit]

    def get_prediction(self, prediction_id: str) -> RegPrediction | None:
        return next((p for p in self._predictions if str(p.id) == prediction_id), None)

    def list_signals(self, jurisdiction: str | None = None, signal_type: SignalType | None = None, limit: int = 50) -> list[RegulatorySignal]:
        results = list(self._signals)
        if jurisdiction:
            results = [s for s in results if s.jurisdiction == jurisdiction]
        if signal_type:
            results = [s for s in results if s.signal_type == signal_type]
        return sorted(results, key=lambda s: s.relevance_score, reverse=True)[:limit]

    async def generate_early_warnings(self) -> list[EarlyWarning]:
        warnings = []
        for pred in self._predictions:
            if pred.confidence_score >= 0.7:
                warning = EarlyWarning(
                    prediction_id=pred.id,
                    title=f"Early Warning: {pred.title}",
                    urgency="high" if pred.prediction_horizon_months <= 6 else "medium",
                    days_until_predicted=pred.prediction_horizon_months * 30,
                    recommended_actions=[t["task"] for t in pred.preparation_tasks[:3]],
                    created_at=datetime.now(UTC),
                )
                warnings.append(warning)
        self._warnings = warnings
        logger.info("Early warnings generated", count=len(warnings))
        return warnings

    def get_accuracy(self) -> PredictionAccuracy:
        total = len(self._predictions)
        sum(1 for p in self._predictions if p.confidence_score >= 0.7)
        return PredictionAccuracy(
            total_predictions=total,
            verified_correct=0,
            verified_incorrect=0,
            pending_verification=total,
            accuracy_rate=0.0,
            avg_lead_time_months=round(sum(p.prediction_horizon_months for p in self._predictions) / total, 1) if total else 0.0,
        )

    async def add_signal(self, signal_type: str, source: str, jurisdiction: str, title: str, relevance_score: float = 0.5) -> RegulatorySignal:
        signal = RegulatorySignal(
            signal_type=SignalType(signal_type),
            source=source,
            jurisdiction=jurisdiction,
            title=title,
            relevance_score=relevance_score,
            detected_at=datetime.now(UTC),
        )
        self._signals.append(signal)
        logger.info("Signal added", source=source, title=title)
        return signal
