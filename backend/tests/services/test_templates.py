"""Tests for compliance templates service."""

import pytest

from app.services.templates.registry import (
    ComplianceTemplate,
    TemplateCategory,
    TemplateParameter,
    TemplateRegistry,
)


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
        template_names = [t.name for t in templates]
        assert "GDPR Consent Manager" in template_names
        assert "HIPAA PHI Handler" in template_names
        assert "Data Subject Access Request Handler" in template_names
        assert "Compliance Audit Logger" in template_names
        assert "PCI-DSS Tokenization" in template_names

    def test_list_templates_by_regulation(self, registry):
        """Test filtering templates by regulation."""
        gdpr_templates = registry.list_templates(regulation="GDPR")

        assert len(gdpr_templates) >= 2
        for template in gdpr_templates:
            assert "GDPR" in template.regulations

    def test_list_templates_by_category(self, registry):
        """Test filtering templates by category."""
        consent_templates = registry.list_templates(category=TemplateCategory.CONSENT)

        assert len(consent_templates) >= 1
        for template in consent_templates:
            assert template.category == TemplateCategory.CONSENT

    def test_get_template(self, registry):
        """Test retrieving specific template."""
        # Find the consent template by name, then look up by ID
        consent = next(t for t in registry.list_templates() if t.name == "GDPR Consent Manager")
        template = registry.get_template(str(consent.id))

        assert template is not None
        assert template.name == "GDPR Consent Manager"
        assert "GDPR" in template.regulations
        assert len(template.parameters) > 0
        assert "typescript" in template.code or "python" in template.code

    def test_get_template_not_found(self, registry):
        """Test retrieving non-existent template."""
        template = registry.get_template("non-existent-template")

        assert template is None

    def test_gdpr_consent_template_structure(self, registry):
        """Test GDPR consent template structure."""
        template = next(t for t in registry.list_templates() if t.name == "GDPR Consent Manager")

        assert template is not None

        # Check parameters
        param_names = [p.name for p in template.parameters]
        assert "storage_backend" in param_names
        assert "custom_purposes" in param_names

        # Check code languages
        assert "typescript" in template.code
        code = template.code["typescript"]
        assert "ConsentManager" in code or "consent" in code.lower()

    def test_hipaa_phi_template_structure(self, registry):
        """Test HIPAA PHI handler template structure."""
        template = next(t for t in registry.list_templates() if t.name == "HIPAA PHI Handler")

        assert template is not None
        assert "HIPAA" in template.regulations

        # Check parameters
        param_names = [p.name for p in template.parameters]
        assert any("encryption" in p.lower() for p in param_names)

    def test_audit_logging_template_structure(self, registry):
        """Test audit logging template structure."""
        template = next(t for t in registry.list_templates() if t.name == "Compliance Audit Logger")

        assert template is not None
        # Should support multiple regulations
        assert len(template.regulations) >= 2

    def test_pci_tokenization_template_structure(self, registry):
        """Test PCI tokenization template structure."""
        template = next(t for t in registry.list_templates() if t.name == "PCI-DSS Tokenization")

        assert template is not None
        assert "PCI-DSS" in template.regulations

    def test_get_template_code(self, registry):
        """Test getting template code."""
        consent = next(t for t in registry.list_templates() if t.name == "GDPR Consent Manager")

        result = registry.get_template_code(
            template_id=str(consent.id),
            language="typescript",
        )

        assert result is not None
        assert "consent" in result.lower()

    def test_get_template_code_not_found(self, registry):
        """Test getting code for non-existent template."""
        result = registry.get_template_code(
            template_id="non-existent",
            language="python",
        )

        assert result is None

    def test_get_template_code_unsupported_language(self, registry):
        """Test getting code for unsupported language."""
        consent = next(t for t in registry.list_templates() if t.name == "GDPR Consent Manager")

        result = registry.get_template_code(
            template_id=str(consent.id),
            language="cobol",
        )

        assert result is None


class TestComplianceTemplate:
    """Test ComplianceTemplate dataclass."""

    def test_template_creation(self):
        """Test creating a template."""
        template = ComplianceTemplate(
            name="Test Template",
            description="A test template",
            category=TemplateCategory.CONSENT,
            regulations=["TEST-REG"],
            parameters=[
                TemplateParameter(
                    name="test_param",
                    type="string",
                    description="A test parameter",
                    required=True,
                )
            ],
            code={"python": "def test(): pass"},
            version="1.0.0",
        )

        assert template.id is not None
        assert len(template.parameters) == 1
        assert "python" in template.code


class TestTemplateParameter:
    """Test TemplateParameter dataclass."""

    def test_parameter_creation(self):
        """Test creating a parameter."""
        param = TemplateParameter(
            name="api_key",
            type="string",
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
            type="number",
            description="Request timeout",
            required=False,
            default=30,
        )

        assert param.default == 30
        assert param.required is False
