"""Tests for CodebaseAnalyzer._create_mapping and _format_structure."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.agents.codebase_analyzer import CodebaseAnalyzer
from app.models.codebase import ComplianceStatus


def _make_analyzer() -> CodebaseAnalyzer:
    """Create a CodebaseAnalyzer without real DB or Copilot."""
    return CodebaseAnalyzer.__new__(CodebaseAnalyzer)


def _make_repository(**overrides) -> MagicMock:
    repo = MagicMock()
    repo.id = overrides.get("id", uuid4())
    repo.full_name = overrides.get("full_name", "test/repo")
    repo.primary_language = overrides.get("primary_language", "python")
    repo.languages = overrides.get("languages", ["python"])
    repo.structure_cache = overrides.get("structure_cache", {})
    return repo


def _make_requirement(**overrides) -> MagicMock:
    req = MagicMock()
    req.id = overrides.get("id", uuid4())
    req.reference_id = overrides.get("reference_id", "REQ-001")
    req.title = overrides.get("title", "Test Requirement")
    req.description = overrides.get("description", "A test requirement")
    req.category = MagicMock()
    req.category.value = overrides.get("category", "data_storage")
    req.data_types = overrides.get("data_types", [])
    req.processes = overrides.get("processes", [])
    return req


# ---------------------------------------------------------------------------
# _create_mapping — compliance status determination
# ---------------------------------------------------------------------------


class TestCreateMappingComplianceStatus:
    """Test gap severity counting and compliance status logic."""

    def test_no_gaps_with_implementations_is_compliant(self):
        analyzer = _make_analyzer()
        repo = _make_repository()
        req = _make_requirement()
        result = analyzer._create_mapping(repo, req, {
            "gaps": [],
            "existing_implementations": [{"file": "auth.py"}],
            "confidence": 0.95,
        })
        assert result.compliance_status == ComplianceStatus.COMPLIANT
        assert result.gap_count == 0

    def test_no_gaps_no_implementations_is_pending_review(self):
        analyzer = _make_analyzer()
        repo = _make_repository()
        req = _make_requirement()
        result = analyzer._create_mapping(repo, req, {
            "gaps": [],
            "existing_implementations": [],
            "confidence": 0.5,
        })
        assert result.compliance_status == ComplianceStatus.PENDING_REVIEW

    def test_no_gaps_missing_implementations_key_is_pending_review(self):
        analyzer = _make_analyzer()
        repo = _make_repository()
        req = _make_requirement()
        result = analyzer._create_mapping(repo, req, {
            "gaps": [],
            "confidence": 0.5,
        })
        assert result.compliance_status == ComplianceStatus.PENDING_REVIEW

    def test_critical_gap_is_non_compliant(self):
        analyzer = _make_analyzer()
        repo = _make_repository()
        req = _make_requirement()
        result = analyzer._create_mapping(repo, req, {
            "gaps": [{"severity": "critical", "description": "missing encryption"}],
            "confidence": 0.9,
        })
        assert result.compliance_status == ComplianceStatus.NON_COMPLIANT
        assert result.critical_gaps == 1
        assert result.major_gaps == 0
        assert result.minor_gaps == 0

    def test_major_gap_only_is_partial(self):
        analyzer = _make_analyzer()
        repo = _make_repository()
        req = _make_requirement()
        result = analyzer._create_mapping(repo, req, {
            "gaps": [{"severity": "major", "description": "incomplete logging"}],
            "confidence": 0.8,
        })
        assert result.compliance_status == ComplianceStatus.PARTIAL
        assert result.critical_gaps == 0
        assert result.major_gaps == 1

    def test_minor_gap_only_is_partial(self):
        analyzer = _make_analyzer()
        repo = _make_repository()
        req = _make_requirement()
        result = analyzer._create_mapping(repo, req, {
            "gaps": [{"severity": "minor", "description": "missing comment"}],
            "confidence": 0.7,
        })
        assert result.compliance_status == ComplianceStatus.PARTIAL
        assert result.minor_gaps == 1

    def test_mixed_gaps_with_critical_is_non_compliant(self):
        analyzer = _make_analyzer()
        repo = _make_repository()
        req = _make_requirement()
        result = analyzer._create_mapping(repo, req, {
            "gaps": [
                {"severity": "critical", "description": "no auth"},
                {"severity": "major", "description": "weak logging"},
                {"severity": "minor", "description": "style"},
            ],
            "confidence": 0.85,
        })
        assert result.compliance_status == ComplianceStatus.NON_COMPLIANT
        assert result.gap_count == 3
        assert result.critical_gaps == 1
        assert result.major_gaps == 1
        assert result.minor_gaps == 1

    def test_unknown_severity_not_counted(self):
        analyzer = _make_analyzer()
        repo = _make_repository()
        req = _make_requirement()
        result = analyzer._create_mapping(repo, req, {
            "gaps": [{"severity": "info", "description": "fyi"}],
            "confidence": 0.5,
        })
        assert result.gap_count == 1
        assert result.critical_gaps == 0
        assert result.major_gaps == 0
        assert result.minor_gaps == 0
        # No critical gaps → PARTIAL
        assert result.compliance_status == ComplianceStatus.PARTIAL

    def test_mapping_carries_metadata(self):
        analyzer = _make_analyzer()
        repo = _make_repository()
        req = _make_requirement()
        result = analyzer._create_mapping(repo, req, {
            "gaps": [],
            "existing_implementations": [{"file": "x.py"}],
            "affected_files": ["a.py", "b.py"],
            "data_flows": [{"from": "api", "to": "db"}],
            "confidence": 0.92,
            "estimated_effort_hours": 4.0,
            "estimated_effort_description": "Small change",
            "risk_level": "low",
        })
        assert result.affected_files == ["a.py", "b.py"]
        assert result.mapping_confidence == 0.92
        assert result.estimated_effort_hours == 4.0
        assert result.risk_level == "low"
        assert result.repository_id == repo.id
        assert result.requirement_id == req.id


# ---------------------------------------------------------------------------
# _format_structure
# ---------------------------------------------------------------------------


class TestFormatStructure:
    def test_empty_structure(self):
        analyzer = _make_analyzer()
        assert analyzer._format_structure({}) == ""

    def test_dict_entries(self):
        analyzer = _make_analyzer()
        structure = {"src/": {"type": "dir"}, "tests/": {"type": "dir"}}
        result = analyzer._format_structure(structure)
        assert "src/" in result
        assert "tests/" in result

    def test_string_entries(self):
        analyzer = _make_analyzer()
        structure = {"README.md": "file", "setup.py": "file"}
        result = analyzer._format_structure(structure)
        assert "- README.md" in result
        assert "- setup.py" in result

    def test_truncation_at_200_entries(self):
        analyzer = _make_analyzer()
        structure = {f"file_{i}.py": "file" for i in range(300)}
        result = analyzer._format_structure(structure)
        lines = result.strip().split("\n")
        assert len(lines) == 200
