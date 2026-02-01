"""Tests for AI Safety Standards sources and risk classification."""

import pytest
from unittest.mock import MagicMock

from app.models.regulation import Jurisdiction, RegulatoryFramework
from app.services.monitoring.ai_safety_sources import (
    AIRiskLevel,
    AIRiskClassifier,
    AISafetyParser,
    AISafetySourceMonitor,
    AISystemClassification,
    AI_SAFETY_SOURCES,
    AI_SYSTEM_DETECTION_PATTERNS,
    NIST_AI_RMF_FUNCTIONS,
    get_ai_safety_source_definitions,
)


pytestmark = pytest.mark.asyncio


class TestAISafetySources:
    """Test suite for AI safety source definitions."""

    def test_source_definitions_valid(self):
        """Test that source definitions are valid."""
        sources = get_ai_safety_source_definitions()
        
        assert len(sources) >= 6
        
        # Check we have sources for key frameworks
        frameworks = {s["framework"] for s in sources}
        assert RegulatoryFramework.NIST_AI_RMF in frameworks
        assert RegulatoryFramework.ISO42001 in frameworks

    def test_nist_ai_rmf_sources_present(self):
        """Test that NIST AI RMF sources are defined."""
        sources = get_ai_safety_source_definitions()
        nist_sources = [s for s in sources if s["framework"] == RegulatoryFramework.NIST_AI_RMF]
        
        assert len(nist_sources) >= 2
        assert all(s["jurisdiction"] == Jurisdiction.US_FEDERAL for s in nist_sources)

    def test_iso42001_sources_present(self):
        """Test that ISO 42001 sources are defined."""
        sources = get_ai_safety_source_definitions()
        iso_sources = [s for s in sources if s["framework"] == RegulatoryFramework.ISO42001]
        
        assert len(iso_sources) >= 1
        assert all(s["jurisdiction"] == Jurisdiction.GLOBAL for s in iso_sources)


class TestNISTAIRMF:
    """Test suite for NIST AI RMF framework definitions."""

    def test_all_core_functions_defined(self):
        """Test that all NIST AI RMF core functions are defined."""
        assert "govern" in NIST_AI_RMF_FUNCTIONS
        assert "map" in NIST_AI_RMF_FUNCTIONS
        assert "measure" in NIST_AI_RMF_FUNCTIONS
        assert "manage" in NIST_AI_RMF_FUNCTIONS

    def test_govern_function_structure(self):
        """Test GOVERN function has proper structure."""
        govern = NIST_AI_RMF_FUNCTIONS["govern"]
        
        assert "description" in govern
        assert "categories" in govern
        assert len(govern["categories"]) >= 6
        
        for category in govern["categories"]:
            assert "id" in category
            assert "title" in category
            assert "description" in category
            assert category["id"].startswith("govern_")

    def test_map_function_structure(self):
        """Test MAP function has proper structure."""
        map_func = NIST_AI_RMF_FUNCTIONS["map"]
        
        assert "description" in map_func
        assert "categories" in map_func
        assert len(map_func["categories"]) >= 5
        
        for category in map_func["categories"]:
            assert category["id"].startswith("map_")

    def test_measure_function_structure(self):
        """Test MEASURE function has proper structure."""
        measure = NIST_AI_RMF_FUNCTIONS["measure"]
        
        assert "description" in measure
        assert "categories" in measure
        assert len(measure["categories"]) >= 4
        
        for category in measure["categories"]:
            assert category["id"].startswith("measure_")

    def test_manage_function_structure(self):
        """Test MANAGE function has proper structure."""
        manage = NIST_AI_RMF_FUNCTIONS["manage"]
        
        assert "description" in manage
        assert "categories" in manage
        assert len(manage["categories"]) >= 4
        
        for category in manage["categories"]:
            assert category["id"].startswith("manage_")


class TestAISystemDetectionPatterns:
    """Test suite for AI system detection patterns."""

    def test_ml_libraries_comprehensive(self):
        """Test that major ML libraries are included."""
        libraries = AI_SYSTEM_DETECTION_PATTERNS["ml_libraries"]
        
        # Check major frameworks
        assert "tensorflow" in libraries
        assert "torch" in libraries or "pytorch" in libraries
        assert "scikit-learn" in libraries or "sklearn" in libraries
        
        # Check LLM libraries
        assert "transformers" in libraries or "huggingface" in libraries
        assert "openai" in libraries
        assert "langchain" in libraries

    def test_ml_file_patterns_comprehensive(self):
        """Test that common ML file patterns are included."""
        patterns = AI_SYSTEM_DETECTION_PATTERNS["ml_file_patterns"]
        
        # Check for common model file extensions
        pattern_str = " ".join(patterns)
        assert "pt" in pattern_str or "pth" in pattern_str  # PyTorch
        assert "h5" in pattern_str or "keras" in pattern_str  # Keras
        assert "onnx" in pattern_str  # ONNX

    def test_high_risk_indicators_cover_eu_ai_act_areas(self):
        """Test that high-risk indicators cover EU AI Act Annex III areas."""
        indicators = " ".join(AI_SYSTEM_DETECTION_PATTERNS["high_risk_indicators"])
        
        # Biometric identification
        assert "biometric" in indicators.lower()
        assert "face" in indicators.lower()
        
        # Critical infrastructure
        assert "infrastructure" in indicators.lower()
        
        # Employment
        assert "hiring" in indicators.lower() or "recruitment" in indicators.lower()
        
        # Education
        assert "grading" in indicators.lower() or "admission" in indicators.lower()
        
        # Law enforcement
        assert "policing" in indicators.lower() or "crime" in indicators.lower()

    def test_prohibited_indicators_present(self):
        """Test that prohibited practice indicators are defined."""
        prohibited = AI_SYSTEM_DETECTION_PATTERNS["prohibited_indicators"]
        
        assert len(prohibited) >= 3
        indicators_str = " ".join(prohibited).lower()
        
        # Social scoring
        assert "social" in indicators_str and "scoring" in indicators_str
        
        # Subliminal manipulation
        assert "subliminal" in indicators_str


class TestAIRiskClassifier:
    """Test suite for AI risk classification."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return AIRiskClassifier()

    def test_classify_no_ai_as_minimal(self, classifier):
        """Test that code without AI is classified as minimal risk."""
        code = """
        def hello_world():
            print("Hello, World!")
        
        class Calculator:
            def add(self, a, b):
                return a + b
        """
        
        result = classifier.classify_from_code(code)
        
        assert result.risk_level == AIRiskLevel.MINIMAL
        assert result.confidence >= 0.8
        assert len(result.detected_patterns) == 0

    def test_classify_ml_code_as_limited(self, classifier):
        """Test that basic ML code is classified as limited risk."""
        code = """
        import torch
        import torch.nn as nn
        
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 1)
            
            def forward(self, x):
                return self.linear(x)
        
        model = SimpleModel()
        output = model.predict(input_data)
        """
        
        result = classifier.classify_from_code(code)
        
        assert result.risk_level in [AIRiskLevel.LIMITED, AIRiskLevel.HIGH]
        assert len(result.detected_patterns) > 0
        assert any("torch" in p.lower() for p in result.detected_patterns)

    def test_classify_biometric_as_high_risk(self, classifier):
        """Test that biometric AI is classified as high risk."""
        code = """
        import tensorflow as tf
        from face_recognition import detect_faces
        
        class BiometricAuth:
            def __init__(self):
                self.model = tf.keras.models.load_model('face_model.h5')
            
            def verify_identity(self, image):
                faces = detect_faces(image)
                return self.model.predict(faces)
        """
        
        result = classifier.classify_from_code(code)
        
        assert result.risk_level == AIRiskLevel.HIGH
        assert any("biometric" in r.lower() or "face" in r.lower() for r in result.high_risk_areas)
        assert len(result.applicable_requirements) > 0

    def test_classify_employment_ai_as_high_risk(self, classifier):
        """Test that employment/hiring AI is classified as high risk."""
        code = """
        from sklearn.ensemble import RandomForestClassifier
        
        class CVScreeningModel:
            def __init__(self):
                self.model = RandomForestClassifier()
            
            def screen_candidates(self, cv_data):
                # Automated CV screening for hiring decisions
                return self.model.predict(cv_data)
            
            def recruitment_score(self, candidate):
                return self.model.predict_proba(candidate)
        """
        
        result = classifier.classify_from_code(code)
        
        assert result.risk_level == AIRiskLevel.HIGH
        assert any(
            "hiring" in r.lower() or "recruitment" in r.lower() or "screening" in r.lower()
            for r in result.high_risk_areas
        )

    def test_classify_social_scoring_as_unacceptable(self, classifier):
        """Test that social scoring is classified as unacceptable."""
        code = """
        class CitizenScoreSystem:
            def calculate_social_scoring(self, citizen_data):
                # Calculate social credit score based on behavior
                score = self.model.predict(citizen_data)
                return score
        """
        
        result = classifier.classify_from_code(code)
        
        assert result.risk_level == AIRiskLevel.UNACCEPTABLE
        assert "prohibited" in result.reasons[0].lower()

    def test_classification_includes_requirements(self, classifier):
        """Test that high-risk classification includes applicable requirements."""
        code = """
        import tensorflow as tf
        
        class HealthcareDiagnostic:
            def diagnose(self, patient_data):
                return self.model.predict(patient_data)
        """
        
        result = classifier.classify_from_code(code)
        
        if result.risk_level == AIRiskLevel.HIGH:
            # Check for key EU AI Act article requirements
            requirements_text = " ".join(result.applicable_requirements)
            assert "Article 9" in requirements_text or "Risk Management" in requirements_text
            assert "Article 14" in requirements_text or "Human Oversight" in requirements_text

    def test_classification_includes_recommendations(self, classifier):
        """Test that classification includes recommendations."""
        code = """
        from transformers import pipeline
        
        classifier = pipeline("text-classification")
        result = classifier("User input text")
        """
        
        result = classifier.classify_from_code(code)
        
        assert len(result.recommendations) > 0


class TestAISafetyParser:
    """Test suite for AI safety document parser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return AISafetyParser()

    def test_parse_nist_ai_rmf(self, parser):
        """Test parsing NIST AI RMF content."""
        html_content = """
        <html>
        <body>
        <h1>NIST AI Risk Management Framework</h1>
        <section>
            <h2>GOVERN Function</h2>
            <p>Organizations shall establish governance structures for AI risk management.</p>
        </section>
        <section>
            <h2>MAP Function</h2>
            <p>Context and risks must be identified and characterized.</p>
        </section>
        </body>
        </html>
        """
        
        result = parser.parse_nist_ai_rmf(html_content)
        
        assert result["title"] == "NIST AI Risk Management Framework"
        assert "functions" in result
        assert len(result["guidance"]) > 0

    def test_extract_requirements(self, parser):
        """Test extracting requirements from AI safety content."""
        content = """
        Organizations shall implement a risk management system for AI.
        The system must include continuous monitoring of AI risks.
        Organizations should conduct regular assessments.
        """
        
        requirements = parser.extract_requirements(content, "nist_ai_rmf")
        
        assert len(requirements) >= 2
        assert any(r["obligation_type"] == "must" for r in requirements)
        assert all(r["framework"] == "nist_ai_rmf" for r in requirements)


class TestAISafetySourceMonitor:
    """Test suite for AI safety source monitor."""

    def test_monitor_initialization(self):
        """Test that monitor initializes correctly."""
        monitor = AISafetySourceMonitor()
        
        assert monitor.crawler is not None
        assert monitor.parser is not None
        assert monitor.classifier is not None

    def test_classify_ai_system_method(self):
        """Test the classify_ai_system convenience method."""
        monitor = AISafetySourceMonitor()
        
        result = monitor.classify_ai_system(
            code_content="import tensorflow as tf; model = tf.keras.Model()",
            description="Machine learning model for predictions",
        )
        
        assert isinstance(result, AISystemClassification)
        assert result.risk_level in [AIRiskLevel.MINIMAL, AIRiskLevel.LIMITED, AIRiskLevel.HIGH]


class TestAIRequirementCategories:
    """Test AI-related requirement categories."""

    def test_ai_categories_in_enum(self):
        """Test that AI categories are defined in RequirementCategory."""
        from app.models.requirement import RequirementCategory
        
        # Check AI categories exist
        assert hasattr(RequirementCategory, "AI_TRANSPARENCY")
        assert hasattr(RequirementCategory, "AI_TESTING")
        assert hasattr(RequirementCategory, "AI_DOCUMENTATION")
        assert hasattr(RequirementCategory, "AI_RISK_CLASSIFICATION")
        assert hasattr(RequirementCategory, "HUMAN_OVERSIGHT")

    def test_ai_category_values(self):
        """Test AI category enum values."""
        from app.models.requirement import RequirementCategory
        
        assert RequirementCategory.AI_TRANSPARENCY.value == "ai_transparency"
        assert RequirementCategory.AI_RISK_CLASSIFICATION.value == "ai_risk_classification"
        assert RequirementCategory.HUMAN_OVERSIGHT.value == "human_oversight"


class TestEUAIActIntegration:
    """Test integration with existing EU AI Act sources."""

    def test_eu_ai_act_risk_categories_exist(self):
        """Test that EU AI Act risk categories are defined."""
        from app.services.monitoring.eu_ai_act_sources import EU_AI_ACT_RISK_CATEGORIES
        
        assert "unacceptable" in EU_AI_ACT_RISK_CATEGORIES
        assert "high" in EU_AI_ACT_RISK_CATEGORIES
        assert "limited" in EU_AI_ACT_RISK_CATEGORIES
        assert "minimal" in EU_AI_ACT_RISK_CATEGORIES

    def test_high_risk_requirements_exist(self):
        """Test that high-risk requirements are defined."""
        from app.services.monitoring.eu_ai_act_sources import HIGH_RISK_REQUIREMENTS
        
        assert len(HIGH_RISK_REQUIREMENTS) >= 10
        
        # Check for key articles
        articles = [r["article"] for r in HIGH_RISK_REQUIREMENTS]
        assert "Article 9" in articles  # Risk Management
        assert "Article 14" in articles  # Human Oversight
        assert "Article 15" in articles  # Accuracy, Robustness

    def test_gpai_requirements_exist(self):
        """Test that GPAI requirements are defined."""
        from app.services.monitoring.eu_ai_act_sources import GPAI_REQUIREMENTS
        
        assert len(GPAI_REQUIREMENTS) >= 4
        
        # Check for GPAI-specific obligations
        actions = " ".join(r["action"] for r in GPAI_REQUIREMENTS)
        assert "documentation" in actions.lower()
        assert "downstream" in actions.lower() or "information" in actions.lower()
