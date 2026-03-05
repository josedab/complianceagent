"""Tests for RequirementExtractor with mocked Copilot."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.requirement_extractor import RequirementExtractor


def _make_regulation(**overrides) -> MagicMock:
    reg = MagicMock()
    reg.name = overrides.get("name", "GDPR")
    reg.jurisdiction = MagicMock()
    reg.jurisdiction.value = overrides.get("jurisdiction", "eu")
    reg.framework = MagicMock()
    reg.framework.value = overrides.get("framework", "gdpr")
    return reg


def _make_copilot(return_value=None, side_effect=None) -> AsyncMock:
    copilot = AsyncMock()
    copilot.analyze_legal_text = AsyncMock(
        return_value=return_value or [],
        side_effect=side_effect,
    )
    copilot.__aenter__ = AsyncMock(return_value=copilot)
    copilot.__aexit__ = AsyncMock(return_value=False)
    return copilot


class TestRequirementExtractor:
    @pytest.mark.asyncio
    async def test_extract_returns_requirements(self):
        reqs = [
            {"reference_id": "REQ-001", "title": "Data consent", "confidence": 0.9},
            {"reference_id": "REQ-002", "title": "Right to erasure", "confidence": 0.85},
        ]
        copilot = _make_copilot(return_value=reqs)
        extractor = RequirementExtractor(copilot)

        result = await extractor.extract(_make_regulation(), "Article 7: Consent...")
        assert len(result) == 2
        assert result[0]["reference_id"] == "REQ-001"

    @pytest.mark.asyncio
    async def test_extract_empty_content(self):
        copilot = _make_copilot(return_value=[])
        extractor = RequirementExtractor(copilot)

        result = await extractor.extract(_make_regulation(), "")
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_passes_regulation_metadata(self):
        copilot = _make_copilot(return_value=[])
        extractor = RequirementExtractor(copilot)
        regulation = _make_regulation(name="HIPAA", jurisdiction="us", framework="hipaa")

        await extractor.extract(regulation, "Health data regulation text")

        copilot.analyze_legal_text.assert_called_once()
        call_kwargs = copilot.analyze_legal_text.call_args.kwargs
        assert call_kwargs["regulation_name"] == "HIPAA"
        assert call_kwargs["jurisdiction"] == "us"
        assert call_kwargs["framework"] == "hipaa"

    @pytest.mark.asyncio
    async def test_extract_propagates_copilot_error(self):
        from app.core.exceptions import CopilotError

        copilot = _make_copilot(side_effect=CopilotError("API failure"))
        extractor = RequirementExtractor(copilot)

        with pytest.raises(CopilotError, match="API failure"):
            await extractor.extract(_make_regulation(), "Some text")
