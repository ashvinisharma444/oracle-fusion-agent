"""Unit tests for GeminiAdapter."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AIParseError, AIRateLimitError
from app.domain.models.diagnostic import DiagnosticModule, Severity


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    monkeypatch.setenv("GEMINI_TEMPERATURE", "0.1")
    monkeypatch.setenv("GEMINI_MAX_OUTPUT_TOKENS", "8192")


class TestGeminiAdapter:
    def test_parse_json_response_clean(self):
        from app.infrastructure.ai.gemini_adapter import GeminiAdapter
        adapter = GeminiAdapter.__new__(GeminiAdapter)
        result = adapter._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_response_with_markdown(self):
        from app.infrastructure.ai.gemini_adapter import GeminiAdapter
        adapter = GeminiAdapter.__new__(GeminiAdapter)
        text = '```json\n{"key": "value"}\n```'
        result = adapter._parse_json_response(text)
        assert result == {"key": "value"}

    def test_parse_json_response_invalid_raises(self):
        from app.infrastructure.ai.gemini_adapter import GeminiAdapter
        adapter = GeminiAdapter.__new__(GeminiAdapter)
        with pytest.raises(AIParseError):
            adapter._parse_json_response("not valid json at all")

    def test_build_rca_report_valid_severity(self):
        from app.infrastructure.ai.gemini_adapter import GeminiAdapter
        from app.domain.models.diagnostic import RCAReport
        adapter = GeminiAdapter.__new__(GeminiAdapter)
        parsed = {
            "root_cause": "Test root cause",
            "impacted_modules": ["subscription"],
            "severity": "HIGH",
            "recommended_diagnostics": ["Check logs"],
            "confidence_score": 0.9,
            "evidence": ["Evidence 1"],
            "knowledge_sources": [],
        }
        rca = adapter._build_rca_report(parsed, '{"raw": true}')
        assert isinstance(rca, RCAReport)
        assert rca.severity == Severity.HIGH
        assert rca.confidence_score == 0.9

    def test_build_rca_report_unknown_severity_defaults_medium(self):
        from app.infrastructure.ai.gemini_adapter import GeminiAdapter
        adapter = GeminiAdapter.__new__(GeminiAdapter)
        parsed = {
            "root_cause": "Test",
            "impacted_modules": [],
            "severity": "UNKNOWN_SEVERITY",
            "recommended_diagnostics": [],
            "confidence_score": 0.5,
        }
        rca = adapter._build_rca_report(parsed, "")
        assert rca.severity == Severity.MEDIUM
