"""Tests for v2 API endpoints across all 10 next-gen features."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app

    return TestClient(app)


class TestMarketplaceV2:
    """Tests for GitHub Marketplace webhook auth and app manifest."""

    def test_get_app_manifest(self, client):
        resp = client.get("/api/v1/marketplace-app/app-manifest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "ComplianceAgent"
        assert "pull_request" in data["default_events"]
        assert data["default_permissions"]["checks"] == "write"

    def test_webhook_verify_invalid(self, client):
        resp = client.post(
            "/api/v1/marketplace-app/webhook/verify",
            json={"payload": "test", "signature": "sha256=invalid"},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is False


class TestRemediationV2:
    """Tests for fix templates and state validation."""

    def test_list_fix_templates(self, client):
        resp = client.get("/api/v1/remediation/templates")
        assert resp.status_code == 200
        templates = resp.json()
        assert len(templates) >= 8
        assert any(t["framework"] == "gdpr" for t in templates)

    def test_list_templates_by_framework(self, client):
        resp = client.get("/api/v1/remediation/templates?framework=hipaa")
        assert resp.status_code == 200
        templates = resp.json()
        assert all(t["framework"] == "hipaa" for t in templates)

    def test_get_template_by_id(self, client):
        resp = client.get("/api/v1/remediation/templates/gdpr-consent-check")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "gdpr-consent-check"
        assert data["framework"] == "gdpr"

    def test_get_template_not_found(self, client):
        resp = client.get("/api/v1/remediation/templates/nonexistent")
        assert resp.status_code == 404

    def test_apply_template(self, client):
        resp = client.post(
            "/api/v1/remediation/templates/apply",
            json={
                "template_id": "gdpr-consent-check",
                "variables": {"purpose": "marketing"},
                "file_path": "src/data/consent.py",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "marketing" in data["fixed_code"]
        assert data["file_path"] == "src/data/consent.py"

    def test_validate_transition_valid(self, client):
        resp = client.post(
            "/api/v1/remediation/validate-transition",
            json={"current_state": "review", "target_state": "approved"},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_validate_transition_invalid(self, client):
        resp = client.post(
            "/api/v1/remediation/validate-transition",
            json={"current_state": "completed", "target_state": "generating"},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is False


class TestEvidenceVaultV2:
    """Tests for multi-framework control mapping."""

    def test_list_soc2_controls(self, client):
        resp = client.get("/api/v1/evidence-vault/v2/controls/soc2")
        assert resp.status_code == 200
        controls = resp.json()
        assert len(controls) >= 10
        assert controls[0]["framework"] == "soc2"

    def test_list_unknown_framework(self, client):
        resp = client.get("/api/v1/evidence-vault/v2/controls/unknown")
        assert resp.status_code == 404

    def test_assess_framework(self, client):
        resp = client.post(
            "/api/v1/evidence-vault/v2/assess",
            json={
                "framework": "soc2",
                "available_evidence": [
                    "Access control policy",
                    "Access review logs",
                    "Access logs",
                    "SSO configuration",
                    "MFA enrollment",
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["framework"] == "soc2"
        assert data["implemented"] >= 1
        assert data["grade"] in ("A+", "A", "B+", "B", "C", "D", "F")


class TestSelfHostedV2:
    """Tests for air-gapped deployment features."""

    def test_list_regulation_bundles(self, client):
        resp = client.get("/api/v1/self-hosted/v2/bundles")
        assert resp.status_code == 200
        bundles = resp.json()
        assert len(bundles) == 4
        ids = [b["id"] for b in bundles]
        assert "core" in ids
        assert "healthcare" in ids

    def test_generate_helm_values(self, client):
        resp = client.post(
            "/api/v1/self-hosted/v2/helm-values",
            json={
                "mode": "self_hosted",
                "llm_backend": "local_ollama",
                "bundles": ["core", "eu"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "backend" in data
        assert "postgresql" in data
        assert data["regulationBundles"] == ["core", "eu"]


class TestIndustryPacksV2:
    """Tests for starter packs."""

    def test_list_starter_packs(self, client):
        resp = client.get("/api/v1/industry-packs/v2/starter-packs")
        assert resp.status_code == 200
        packs = resp.json()
        assert len(packs) == 4
        industries = [p["industry"] for p in packs]
        assert "fintech" in industries
        assert "healthtech" in industries

    def test_get_starter_pack(self, client):
        resp = client.get("/api/v1/industry-packs/v2/starter-packs/fintech")
        assert resp.status_code == 200
        data = resp.json()
        assert "pci-dss" in data["regulations"]

    def test_get_starter_pack_not_found(self, client):
        resp = client.get("/api/v1/industry-packs/v2/starter-packs/nonexistent")
        assert resp.status_code == 404


class TestMultiLLMV2:
    """Tests for smart routing."""

    def test_classify_simple(self, client):
        resp = client.post("/api/v1/multi-llm/classify-complexity?text=What%20is%20GDPR?")
        assert resp.status_code == 200
        data = resp.json()
        assert data["complexity"] == "simple"

    def test_classify_critical(self, client):
        resp = client.post(
            "/api/v1/multi-llm/classify-complexity?text=prohibited+practices+under+penalty+of+imprisonment"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["complexity"] == "critical"
        assert len(data["critical_keywords_found"]) > 0


class TestFederatedIntelV2:
    """Tests for differential privacy features."""

    def test_anonymize_patterns(self, client):
        resp = client.post(
            "/api/v1/federated-intel/v2/anonymize",
            json={
                "patterns": [
                    {"id": "p1", "frequency": 100, "category": "encryption"},
                    {"id": "p2", "frequency": 50, "category": "access_control"},
                ],
                "privacy_level": "balanced",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["anonymization_method"] == "laplace"

    def test_find_similar_orgs(self, client):
        resp = client.post(
            "/api/v1/federated-intel/v2/similar-orgs",
            json={
                "regulations": ["gdpr", "pci-dss"],
                "industry": "fintech",
                "size_bucket": "medium",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["similarity_score"] > 0

    def test_privacy_budget(self, client):
        resp = client.get("/api/v1/federated-intel/v2/privacy-budget")
        assert resp.status_code == 200
        data = resp.json()
        assert data["epsilon_total"] == 10.0
        assert data["is_exhausted"] is False

    def test_noise_demo(self, client):
        resp = client.post("/api/v1/federated-intel/v2/noise-demo?true_value=100&epsilon=1.0")
        assert resp.status_code == 200
        data = resp.json()
        assert "noisy_value" in data
        assert data["epsilon_used"] == 1.0


class TestPredictionsV2:
    """Tests for ML prediction engine."""

    def test_prediction_accuracy_metrics(self, client):
        resp = client.get("/api/v1/predictions/v2/accuracy")
        assert resp.status_code == 200
        data = resp.json()
        assert "accuracy_rate" in data
        assert "avg_lead_time_days" in data
