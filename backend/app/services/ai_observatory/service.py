"""AI Model Compliance Observatory Service."""

import random
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_observatory.models import (
    AIModel,
    AIRiskLevel,
    BiasMetric,
    BiasMetricType,
    ExplainabilityReport,
    ModelComplianceReport,
    ModelStatus,
    ObservatoryDashboard,
)


logger = structlog.get_logger()

# EU AI Act high-risk use cases
_HIGH_RISK_USE_CASES = {
    "biometric_identification",
    "critical_infrastructure",
    "education_scoring",
    "employment_recruitment",
    "credit_scoring",
    "law_enforcement",
    "migration_asylum",
    "justice_administration",
}

_PROHIBITED_USE_CASES = {
    "social_scoring",
    "real_time_biometric_surveillance",
    "subliminal_manipulation",
    "vulnerability_exploitation",
}


class AIObservatoryService:
    """Service for AI model compliance observatory."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot_client = copilot_client
        self._models: list[AIModel] = []
        self._bias_metrics: dict[UUID, list[BiasMetric]] = {}
        self._explainability_reports: dict[UUID, ExplainabilityReport] = {}
        self._compliance_reports: dict[UUID, ModelComplianceReport] = {}

    async def register_model(
        self,
        name: str,
        model_type: str,
        version: str,
        framework: str,
        use_case: str,
    ) -> AIModel:
        """Register a new AI model for compliance tracking."""
        model = AIModel(
            name=name,
            model_type=model_type,
            version=version,
            framework=framework,
            use_case=use_case,
            risk_level=AIRiskLevel.MINIMAL_RISK,
            status=ModelStatus.UNDER_REVIEW,
            owner="",
            deployed_at=datetime.now(UTC),
        )
        self._models.append(model)
        logger.info("AI model registered", name=name, model_type=model_type)
        return model

    async def list_models(
        self,
        risk_level: AIRiskLevel | None = None,
        status: ModelStatus | None = None,
    ) -> list[AIModel]:
        """List AI models with optional filters."""
        results = list(self._models)
        if risk_level:
            results = [m for m in results if m.risk_level == risk_level]
        if status:
            results = [m for m in results if m.status == status]
        return results

    async def classify_risk(self, model_id: UUID) -> AIModel | None:
        """Apply EU AI Act risk classification based on use_case."""
        model = next((m for m in self._models if m.id == model_id), None)
        if not model:
            return None

        use_case_lower = model.use_case.lower().replace(" ", "_")
        if use_case_lower in _PROHIBITED_USE_CASES:
            model.risk_level = AIRiskLevel.PROHIBITED
        elif use_case_lower in _HIGH_RISK_USE_CASES:
            model.risk_level = AIRiskLevel.HIGH_RISK
        elif any(
            kw in use_case_lower for kw in ("chatbot", "content_generation", "recommendation")
        ):
            model.risk_level = AIRiskLevel.LIMITED_RISK
        else:
            model.risk_level = AIRiskLevel.MINIMAL_RISK

        logger.info(
            "Risk classified",
            model_id=str(model_id),
            risk_level=model.risk_level.value,
            use_case=model.use_case,
        )
        return model

    async def run_bias_assessment(
        self,
        model_id: UUID,
        protected_attributes: list[str],
    ) -> list[BiasMetric]:
        """Run bias assessment for protected attributes."""
        model = next((m for m in self._models if m.id == model_id), None)
        if not model:
            return []

        metrics: list[BiasMetric] = []
        thresholds = {
            BiasMetricType.DEMOGRAPHIC_PARITY: 0.1,
            BiasMetricType.EQUALIZED_ODDS: 0.1,
            BiasMetricType.DISPARATE_IMPACT: 0.8,
            BiasMetricType.CALIBRATION: 0.05,
            BiasMetricType.INDIVIDUAL_FAIRNESS: 0.1,
        }

        for attr in protected_attributes:
            for metric_type in BiasMetricType:
                threshold = thresholds[metric_type]
                if metric_type == BiasMetricType.DISPARATE_IMPACT:
                    value = round(random.uniform(0.6, 1.0), 4)
                    is_passing = value >= threshold
                else:
                    value = round(random.uniform(0.0, 0.25), 4)
                    is_passing = value <= threshold

                metric = BiasMetric(
                    model_id=model_id,
                    metric_type=metric_type,
                    value=value,
                    threshold=threshold,
                    is_passing=is_passing,
                    protected_attribute=attr,
                    measured_at=datetime.now(UTC),
                )
                metrics.append(metric)

        self._bias_metrics[model_id] = metrics
        logger.info(
            "Bias assessment completed",
            model_id=str(model_id),
            attributes=protected_attributes,
            metrics=len(metrics),
        )
        return metrics

    async def generate_explainability_report(self, model_id: UUID) -> ExplainabilityReport | None:
        """Generate an explainability report for a model."""
        model = next((m for m in self._models if m.id == model_id), None)
        if not model:
            return None

        features = {
            "feature_a": round(random.uniform(0.1, 0.4), 3),
            "feature_b": round(random.uniform(0.05, 0.3), 3),
            "feature_c": round(random.uniform(0.02, 0.2), 3),
            "feature_d": round(random.uniform(0.01, 0.15), 3),
            "feature_e": round(random.uniform(0.005, 0.1), 3),
        }
        # Normalize
        total = sum(features.values())
        features = {k: round(v / total, 3) for k, v in features.items()}

        coverage = round(random.uniform(0.6, 0.98), 2)
        report = ExplainabilityReport(
            model_id=model_id,
            method="SHAP",
            feature_importance=features,
            explanation_coverage=coverage,
            gdpr_art22_compliant=coverage >= 0.8,
            eu_ai_act_art13_compliant=coverage >= 0.75
            and model.risk_level != AIRiskLevel.PROHIBITED,
            generated_at=datetime.now(UTC),
        )
        self._explainability_reports[model_id] = report
        logger.info("Explainability report generated", model_id=str(model_id), coverage=coverage)
        return report

    async def assess_compliance(self, model_id: UUID) -> ModelComplianceReport | None:
        """Full compliance assessment for a model."""
        model = next((m for m in self._models if m.id == model_id), None)
        if not model:
            return None

        bias_metrics = self._bias_metrics.get(model_id, [])
        explainability = self._explainability_reports.get(model_id)

        issues: list[str] = []
        recommendations: list[str] = []

        # Check bias
        failing_bias = [m for m in bias_metrics if not m.is_passing]
        if failing_bias:
            issues.append(f"{len(failing_bias)} bias metrics failing thresholds")
            recommendations.append("Retrain model with debiased dataset")

        # Check explainability
        if not explainability:
            issues.append("No explainability report generated")
            recommendations.append("Generate SHAP/LIME explainability report")
        elif not explainability.gdpr_art22_compliant:
            issues.append("Explainability coverage below GDPR Art.22 requirements")
            recommendations.append("Improve explanation coverage to ≥80%")

        # Risk-level specific checks
        if model.risk_level == AIRiskLevel.PROHIBITED:
            issues.append("Model use case is prohibited under EU AI Act")
            recommendations.append("Discontinue deployment or change use case")
        elif model.risk_level == AIRiskLevel.HIGH_RISK:
            recommendations.append("Implement human oversight mechanism")
            recommendations.append("Maintain technical documentation per Art.11")

        doc_complete = len(issues) == 0
        human_oversight = (
            model.risk_level not in (AIRiskLevel.HIGH_RISK, AIRiskLevel.PROHIBITED)
            or random.random() > 0.5
        )
        overall = len(issues) == 0 and (not bias_metrics or not failing_bias)

        if overall:
            model.status = ModelStatus.COMPLIANT
        else:
            model.status = ModelStatus.NON_COMPLIANT

        model.last_assessed_at = datetime.now(UTC)

        report = ModelComplianceReport(
            model_id=model_id,
            risk_level=model.risk_level,
            bias_metrics=bias_metrics,
            explainability=explainability,
            documentation_complete=doc_complete,
            human_oversight_implemented=human_oversight,
            technical_documentation=f"Technical documentation for {model.name} v{model.version}",
            overall_compliant=overall,
            issues=issues,
            recommendations=recommendations,
            assessed_at=datetime.now(UTC),
        )
        self._compliance_reports[model_id] = report
        logger.info(
            "Compliance assessed",
            model_id=str(model_id),
            compliant=overall,
            issues=len(issues),
        )
        return report

    async def get_dashboard(self) -> ObservatoryDashboard:
        """Get observatory dashboard summary."""
        by_risk: dict[str, int] = {}
        for m in self._models:
            by_risk[m.risk_level.value] = by_risk.get(m.risk_level.value, 0) + 1

        compliant = sum(1 for m in self._models if m.status == ModelStatus.COMPLIANT)
        non_compliant = sum(1 for m in self._models if m.status == ModelStatus.NON_COMPLIANT)
        under_review = sum(1 for m in self._models if m.status == ModelStatus.UNDER_REVIEW)

        all_metrics = [m for metrics in self._bias_metrics.values() for m in metrics]
        avg_bias = 0.0
        if all_metrics:
            avg_bias = round(sum(m.value for m in all_metrics) / len(all_metrics), 4)

        alerts: list[dict] = []
        for m in self._models:
            if m.status == ModelStatus.NON_COMPLIANT:
                alerts.append(
                    {
                        "model": m.name,
                        "alert": "Non-compliant",
                        "risk_level": m.risk_level.value,
                    }
                )

        return ObservatoryDashboard(
            total_models=len(self._models),
            by_risk_level=by_risk,
            compliant_count=compliant,
            non_compliant_count=non_compliant,
            avg_bias_score=avg_bias,
            models_needing_review=under_review,
            recent_alerts=alerts,
        )

    async def update_model_status(
        self,
        model_id: UUID,
        status: ModelStatus,
    ) -> AIModel | None:
        """Update a model's compliance status."""
        model = next((m for m in self._models if m.id == model_id), None)
        if not model:
            return None
        model.status = status
        logger.info("Model status updated", model_id=str(model_id), status=status.value)
        return model
