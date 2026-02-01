"""Tests for compliance templates service."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.templates.registry import (
    TemplateRegistry,
    ComplianceTemplate,
    TemplateParameter,
)

pytestmark = pytest.mark.asyncio


class TestTemplateRegistry:
    """Test suite for TemplateRegistry."""

    @pytest.fixture
    def registry(self):
        """Create TemplateRegistry instance."""
        return TemplateRegistry()

    def test_list_templates(self, registry):
        """Test listing all templates."""
        templates = registry.list_templates()
        
        assert len(templates) >= 5
        template_ids = [t.template_id for t in templates]
        assert "gdpr-consent-banner" in template_ids
        assert "hipaa-phi-handler" in template_ids
        assert "gdpr-dsar-handler" in template_ids
        assert "compliance-audit-logging" in template_ids
        assert "pci-card-tokenization" in template_ids

    def test_list_templates_by_regulation(self, registry):
        """Test filtering templates by regulation."""
        gdpr_templates = registry.list_templates(regulation="gdpr")
        
        assert len(gdpr_templates) >= 2
        for template in gdpr_templates:
            assert "gdpr" in [r.lower() for r in template.regulations]

    def test_list_templates_by_category(self, registry):
        """Test filtering templates by category."""
        consent_templates = registry.list_templates(category="consent")
        
        assert len(consent_templates) >= 1
        for template in consent_templates:
            assert template.category.lower() == "consent"

    def test_get_template(self, registry):
        """Test retrieving specific template."""
        template = registry.get_template("gdpr-consent-banner")
        
        assert template is not None
        assert template.template_id == "gdpr-consent-banner"
        assert template.name == "GDPR Consent Banner"
        assert "GDPR" in template.regulations
        assert len(template.parameters) > 0
        assert "typescript" in template.code or "python" in template.code

    def test_get_template_not_found(self, registry):
        """Test retrieving non-existent template."""
        template = registry.get_template("non-existent-template")
        
        assert template is None

    def test_gdpr_consent_template_structure(self, registry):
        """Test GDPR consent template structure."""
        template = registry.get_template("gdpr-consent-banner")
        
        assert template is not None
        
        # Check parameters
        param_names = [p.name for p in template.parameters]
        assert "cookie_domain" in param_names
        assert "consent_version" in param_names
        
        # Check code languages
        assert "typescript" in template.code
        code = template.code["typescript"]
        assert "ConsentBanner" in code or "consent" in code.lower()

    def test_hipaa_phi_template_structure(self, registry):
        """Test HIPAA PHI handler template structure."""
        template = registry.get_template("hipaa-phi-handler")
        
        assert template is not None
        assert "HIPAA" in template.regulations
        
        # Check parameters
        param_names = [p.name for p in template.parameters]
        assert any("encryption" in p.lower() for p in param_names)

    def test_audit_logging_template_structure(self, registry):
        """Test audit logging template structure."""
        template = registry.get_template("compliance-audit-logging")
        
        assert template is not None
        # Should support multiple regulations
        assert len(template.regulations) >= 2

    def test_pci_tokenization_template_structure(self, registry):
        """Test PCI tokenization template structure."""
        template = registry.get_template("pci-card-tokenization")
        
        assert template is not None
        assert "PCI-DSS" in template.regulations

    async def test_generate_template(self, registry):
        """Test generating template code."""
        params = {
            "cookie_domain": "example.com",
            "consent_version": "1.0",
        }
        
        result = await registry.generate(
            template_id="gdpr-consent-banner",
            language="typescript",
            parameters=params,
        )
        
        assert result is not None
        assert "code" in result
        assert "example.com" in result["code"]

    async def test_generate_template_not_found(self, registry):
        """Test generating with non-existent template."""
        result = await registry.generate(
            template_id="non-existent",
            language="python",
            parameters={},
        )
        
        assert result is None or "error" in result

    async def test_generate_template_unsupported_language(self, registry):
        """Test generating with unsupported language."""
        result = await registry.generate(
            template_id="gdpr-consent-banner",
            language="cobol",
            parameters={},
        )
        
        # Should return None or error for unsupported language
        assert result is None or "error" in result


class TestComplianceTemplate:
    """Test ComplianceTemplate dataclass."""

    def test_template_creation(self):
        """Test creating a template."""
        template = ComplianceTemplate(
            template_id="test-template",
            name="Test Template",
            description="A test template",
            category="testing",
            regulations=["TEST-REG"],
            parameters=[
                TemplateParameter(
                    name="test_param",
                    param_type="string",
                    description="A test parameter",
                    required=True,
                )
            ],
            code={"python": "def test(): pass"},
            version="1.0.0",
        )
        
        assert template.template_id == "test-template"
        assert len(template.parameters) == 1
        assert "python" in template.code


class TestTemplateParameter:
    """Test TemplateParameter dataclass."""

    def test_parameter_creation(self):
        """Test creating a parameter."""
        param = TemplateParameter(
            name="api_key",
            param_type="string",
            description="API key for service",
            required=True,
            default=None,
        )
        
        assert param.name == "api_key"
        assert param.required is True

    def test_parameter_with_default(self):
        """Test parameter with default value."""
        param = TemplateParameter(
            name="timeout",
            param_type="number",
            description="Request timeout",
            required=False,
            default=30,
        )
        
        assert param.default == 30
        assert param.required is False
