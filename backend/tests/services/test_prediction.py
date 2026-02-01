"""Tests for regulatory prediction service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from app.services.prediction import (
    RegulatoryPredictionEngine,
    PredictedRegulation,
    RegulatorySignal,
    SignalSource,
    ImpactAssessment,
)

pytestmark = pytest.mark.asyncio


class TestRegulatoryPredictionEngine:
    """Test suite for RegulatoryPredictionEngine."""

    @pytest.fixture
    def engine(self):
        """Create RegulatoryPredictionEngine instance."""
        return RegulatoryPredictionEngine()

    async def test_analyze_regulatory_landscape(self, engine):
        """Test analyzing regulatory landscape."""
        with patch.object(engine, "_gather_signals") as mock_gather:
            mock_gather.return_value = [
                RegulatorySignal(
                    signal_id="sig-001",
                    source=SignalSource.EUR_LEX,
                    title="EU AI Act Implementation",
                    summary="Draft implementation guidelines published",
                    relevance_score=0.92,
                    detected_at=datetime.utcnow(),
                ),
            ]
            
            with patch.object(engine, "_generate_predictions") as mock_predict:
                mock_predict.return_value = [
                    PredictedRegulation(
                        prediction_id="pred-001",
                        regulation_name="EU AI Act Enforcement",
                        jurisdiction="EU",
                        predicted_date=datetime.utcnow() + timedelta(days=180),
                        confidence=0.85,
                        impact_areas=["AI systems", "High-risk classification"],
                        signals_count=5,
                    ),
                ]
                
                result = await engine.analyze_regulatory_landscape(
                    jurisdictions=["EU", "US"],
                    industries=["technology", "healthcare"],
                )
                
                assert "signals" in result
                assert "predictions" in result
                assert len(result["predictions"]) >= 1

    async def test_get_predictions(self, engine):
        """Test getting predictions."""
        with patch.object(engine, "_fetch_predictions") as mock_fetch:
            mock_fetch.return_value = [
                PredictedRegulation(
                    prediction_id="pred-001",
                    regulation_name="Digital Services Act Updates",
                    jurisdiction="EU",
                    predicted_date=datetime.utcnow() + timedelta(days=90),
                    confidence=0.78,
                    impact_areas=["Content moderation", "Platform liability"],
                    signals_count=3,
                ),
            ]
            
            predictions = await engine.get_predictions(
                jurisdiction="EU",
                min_confidence=0.7,
            )
            
            assert len(predictions) >= 1
            assert predictions[0].confidence >= 0.7

    async def test_get_prediction_timeline(self, engine):
        """Test getting prediction timeline."""
        with patch.object(engine, "_build_timeline") as mock_timeline:
            mock_timeline.return_value = {
                "timeline": [
                    {
                        "date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                        "event": "Comment period ends",
                        "regulation": "State Privacy Law",
                    },
                    {
                        "date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
                        "event": "Effective date",
                        "regulation": "State Privacy Law",
                    },
                ],
                "horizon_months": 12,
            }
            
            timeline = await engine.get_prediction_timeline(
                horizon_months=12,
                jurisdictions=["US"],
            )
            
            assert "timeline" in timeline
            assert len(timeline["timeline"]) >= 1

    async def test_assess_impact(self, engine):
        """Test assessing impact of predicted regulation."""
        prediction = PredictedRegulation(
            prediction_id="pred-002",
            regulation_name="Test Regulation",
            jurisdiction="US",
            predicted_date=datetime.utcnow() + timedelta(days=180),
            confidence=0.82,
            impact_areas=["Data handling", "Privacy"],
            signals_count=4,
        )
        
        codebase_info = {
            "languages": ["python", "typescript"],
            "frameworks": ["fastapi", "react"],
            "data_handling": ["user_data", "analytics"],
        }
        
        with patch.object(engine, "_calculate_impact") as mock_impact:
            mock_impact.return_value = ImpactAssessment(
                prediction_id="pred-002",
                overall_impact="high",
                affected_areas=[
                    {"area": "User data storage", "impact": "high"},
                    {"area": "Analytics pipeline", "impact": "medium"},
                ],
                estimated_effort_hours=160,
                priority="urgent",
                recommendations=[
                    "Review data retention policies",
                    "Implement consent management",
                ],
            )
            
            assessment = await engine.assess_impact(
                prediction=prediction,
                codebase_info=codebase_info,
            )
            
            assert assessment.overall_impact in ["low", "medium", "high"]
            assert assessment.estimated_effort_hours > 0

    async def test_subscribe_to_signals(self, engine):
        """Test subscribing to regulatory signals."""
        result = await engine.subscribe_to_signals(
            jurisdictions=["EU", "US"],
            industries=["healthcare"],
            keywords=["privacy", "data protection"],
            webhook_url="https://example.com/webhook",
        )
        
        assert result is not None
        assert "subscription_id" in result

    async def test_get_signal_sources(self, engine):
        """Test getting available signal sources."""
        sources = engine.get_signal_sources()
        
        assert len(sources) >= 5
        source_names = [s.source_name for s in sources]
        assert any("eur-lex" in s.lower() or "eu" in s.lower() for s in source_names)

    async def test_refresh_signals(self, engine):
        """Test refreshing signals from sources."""
        with patch.object(engine, "_fetch_new_signals") as mock_fetch:
            mock_fetch.return_value = {
                "new_signals": 5,
                "updated_predictions": 2,
                "last_refresh": datetime.utcnow().isoformat(),
            }
            
            result = await engine.refresh_signals()
            
            assert "new_signals" in result

    async def test_get_confidence_factors(self, engine):
        """Test getting confidence factors for a prediction."""
        with patch.object(engine, "_analyze_confidence") as mock_analyze:
            mock_analyze.return_value = {
                "factors": [
                    {"factor": "Legislative stage", "contribution": 0.3, "value": "Committee review"},
                    {"factor": "Historical accuracy", "contribution": 0.25, "value": "Similar predictions 80% accurate"},
                    {"factor": "Source reliability", "contribution": 0.2, "value": "Official sources"},
                ],
                "total_confidence": 0.82,
            }
            
            factors = await engine.get_confidence_factors("pred-001")
            
            assert "factors" in factors
            assert len(factors["factors"]) >= 2


class TestPredictedRegulation:
    """Test PredictedRegulation dataclass."""

    def test_prediction_creation(self):
        """Test creating a prediction."""
        prediction = PredictedRegulation(
            prediction_id="pred-001",
            regulation_name="Test Regulation",
            jurisdiction="US",
            predicted_date=datetime.utcnow() + timedelta(days=90),
            confidence=0.75,
            impact_areas=["Privacy", "Data handling"],
            signals_count=3,
        )
        
        assert prediction.prediction_id == "pred-001"
        assert prediction.confidence == 0.75

    def test_prediction_to_dict(self):
        """Test converting prediction to dict."""
        prediction = PredictedRegulation(
            prediction_id="pred-002",
            regulation_name="Another Regulation",
            jurisdiction="EU",
            predicted_date=datetime(2025, 6, 1),
            confidence=0.88,
            impact_areas=["Security"],
            signals_count=5,
        )
        
        pred_dict = prediction.to_dict()
        
        assert pred_dict["jurisdiction"] == "EU"
        assert pred_dict["confidence"] == 0.88


class TestRegulatorySignal:
    """Test RegulatorySignal dataclass."""

    def test_signal_creation(self):
        """Test creating a signal."""
        signal = RegulatorySignal(
            signal_id="sig-001",
            source=SignalSource.CONGRESS_GOV,
            title="New Privacy Bill",
            summary="Introduced in Senate",
            relevance_score=0.85,
            detected_at=datetime.utcnow(),
        )
        
        assert signal.source == SignalSource.CONGRESS_GOV
        assert signal.relevance_score == 0.85

    def test_signal_to_dict(self):
        """Test converting signal to dict."""
        signal = RegulatorySignal(
            signal_id="sig-002",
            source=SignalSource.EUR_LEX,
            title="Test Signal",
            summary="Test summary",
            relevance_score=0.72,
            detected_at=datetime(2024, 1, 15),
        )
        
        signal_dict = signal.to_dict()
        
        assert "source" in signal_dict


class TestImpactAssessment:
    """Test ImpactAssessment dataclass."""

    def test_assessment_creation(self):
        """Test creating an impact assessment."""
        assessment = ImpactAssessment(
            prediction_id="pred-001",
            overall_impact="high",
            affected_areas=[
                {"area": "User data", "impact": "high"},
            ],
            estimated_effort_hours=80,
            priority="urgent",
            recommendations=["Review policies"],
        )
        
        assert assessment.overall_impact == "high"
        assert assessment.estimated_effort_hours == 80

    def test_assessment_to_dict(self):
        """Test converting assessment to dict."""
        assessment = ImpactAssessment(
            prediction_id="pred-002",
            overall_impact="medium",
            affected_areas=[],
            estimated_effort_hours=40,
            priority="normal",
            recommendations=[],
        )
        
        assessment_dict = assessment.to_dict()
        
        assert assessment_dict["priority"] == "normal"


class TestSignalSource:
    """Test SignalSource enum."""

    def test_signal_sources(self):
        """Test signal source values."""
        assert SignalSource.EUR_LEX.value == "eur_lex"
        assert SignalSource.CONGRESS_GOV.value == "congress_gov"
        assert SignalSource.FTC.value == "ftc"
