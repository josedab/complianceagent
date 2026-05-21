"""Regression tests for silent-failure hardening across services."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.infrastructure.cloudformation import analyze_cloudformation_directory
from app.services.sbom.generator import SBOMGenerator


pytestmark = pytest.mark.asyncio


async def test_sbom_parse_npm_invalid_json_logs_warning():
    gen = SBOMGenerator()
    with patch("app.services.sbom.generator.logger") as mock_logger:
        result = gen._parse_npm("not valid json {{{{")
    assert result == []
    mock_logger.warning.assert_called_once()
    assert "package.json" in mock_logger.warning.call_args[0][0]


async def test_sbom_parse_pipfile_lock_invalid_json_logs_warning():
    gen = SBOMGenerator()
    with patch("app.services.sbom.generator.logger") as mock_logger:
        result = gen._parse_pipfile_lock("definitely not json")
    assert result == []
    mock_logger.warning.assert_called_once()
    assert "Pipfile.lock" in mock_logger.warning.call_args[0][0]


async def test_nl_query_handle_general_logs_on_ai_failure():
    from app.services.nl_query.service import NLQueryService

    mock_copilot = MagicMock()
    mock_copilot.analyze_legal_text = AsyncMock(side_effect=ValueError("AI down"))
    service = NLQueryService.__new__(NLQueryService)
    service.copilot = mock_copilot
    service.db = None
    with patch("app.services.nl_query.service.logger") as mock_logger:
        answer, _sources = await service._handle_general("what is GDPR?")
    assert "compliance queries" in answer.lower()
    mock_logger.warning.assert_called_once()
    assert "AI call failed" in mock_logger.warning.call_args[0][0]


def test_cfn_directory_logs_on_unparseable_file(tmp_path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("AWSTemplateFormatVersion: '2010-09-09'\nResources: {}")
    with patch("app.services.infrastructure.cloudformation.logger") as mock_logger:
        with patch.object(Path, "read_text", side_effect=OSError("disk error")):
            analyze_cloudformation_directory(str(tmp_path))
    mock_logger.warning.assert_called()
    assert any(
        "skipping unparseable template file" in str(c) for c in mock_logger.warning.call_args_list
    )


async def test_policy_marketplace_invalid_language_filter_returns_list():
    from app.services.policy_marketplace.service import PolicyMarketplaceService

    service = PolicyMarketplaceService(db=None)
    result = await service.list_packs(language="not_a_real_language")
    assert isinstance(result, list)


def test_pr_bot_comment_generator_instantiation():
    from app.services.pr_bot.comments import CommentGenerator

    gen = CommentGenerator()
    mock_result = MagicMock()
    mock_result.violations_found = 3
    mock_result.critical_count = 1
    mock_result.high_count = 1
    mock_result.medium_count = 1
    summary = gen.generate_summary_comment(mock_result)
    assert isinstance(summary, str)
