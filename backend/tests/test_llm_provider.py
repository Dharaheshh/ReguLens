"""Tests for LLMProvider — TASK-011 / CORRECTION-001 / CORRECTION-003.

All tests use mocked LLM responses — no real network calls.
"""
import os
import sys
import json
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pydantic import BaseModel, ValidationError

from app.llm.provider import LLMProvider, get_provider, call_with_retry_and_fallback, LLMCallError


# ── Simple test schema ──

class SimpleOutput(BaseModel):
    message: str
    count: int


def _mock_completion(content: str):
    """Create a mock OpenAI chat completion response."""
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


# ── Tests ──

def test_provider_parses_valid_json():
    """Mock client returns valid JSON matching schema → parses correctly."""
    provider = LLMProvider(
        base_url="http://fake.test/v1",
        api_key="fake-key",
        model="fake-model",
    )
    valid_json = json.dumps({"message": "hello", "count": 42})
    provider._client = MagicMock()
    provider._client.chat.completions.create.return_value = _mock_completion(valid_json)

    result = provider.call(
        system_prompt="test",
        user_content="test",
        response_model=SimpleOutput,
        temperature=0.2,
    )

    assert isinstance(result, SimpleOutput)
    assert result.message == "hello"
    assert result.count == 42


def test_provider_raises_on_malformed_json():
    """Mock client returns malformed JSON → raises ValidationError."""
    provider = LLMProvider(
        base_url="http://fake.test/v1",
        api_key="fake-key",
        model="fake-model",
    )
    provider._client = MagicMock()
    provider._client.chat.completions.create.return_value = _mock_completion("not json at all")

    with pytest.raises(ValidationError):
        provider.call(
            system_prompt="test",
            user_content="test",
            response_model=SimpleOutput,
            temperature=0.2,
        )


def test_retry_triggers_on_validation_failure():
    """Malformed JSON on first call → retry succeeds on second call."""
    valid_json = json.dumps({"message": "retry worked", "count": 1})

    with patch("app.llm.provider.get_provider") as mock_get:
        mock_primary = MagicMock()
        mock_fallback = MagicMock()

        # Primary: first call fails, second call succeeds
        mock_primary.call.side_effect = [
            ValidationError.from_exception_data(
                title="SimpleOutput",
                line_errors=[],
            ),
            SimpleOutput(message="retry worked", count=1),
        ]
        mock_fallback.call.return_value = SimpleOutput(message="fallback", count=2)

        mock_get.side_effect = lambda use_fallback=False: (
            mock_fallback if use_fallback else mock_primary
        )

        result = call_with_retry_and_fallback(
            system_prompt="test",
            user_content="test",
            response_model=SimpleOutput,
            temperature=0.2,
        )

        assert result.message == "retry worked"
        assert mock_primary.call.call_count == 2
        assert mock_fallback.call.call_count == 0


def test_fallback_called_when_primary_fails_twice():
    """Primary fails twice → fallback provider is called and its response used."""
    with patch("app.llm.provider.get_provider") as mock_get:
        mock_primary = MagicMock()
        mock_fallback = MagicMock()

        mock_primary.call.side_effect = Exception("primary down")
        mock_fallback.call.return_value = SimpleOutput(message="from fallback", count=99)

        mock_get.side_effect = lambda use_fallback=False: (
            mock_fallback if use_fallback else mock_primary
        )

        result = call_with_retry_and_fallback(
            system_prompt="test",
            user_content="test",
            response_model=SimpleOutput,
            temperature=0.2,
        )

        assert result.message == "from fallback"
        assert result.count == 99
        assert mock_primary.call.call_count == 2
        assert mock_fallback.call.call_count == 1


def test_all_attempts_fail_raises_llm_call_error():
    """Primary fails twice, fallback fails once → LLMCallError raised."""
    with patch("app.llm.provider.get_provider") as mock_get:
        mock_primary = MagicMock()
        mock_fallback = MagicMock()

        mock_primary.call.side_effect = Exception("primary down")
        mock_fallback.call.side_effect = Exception("fallback also down")

        mock_get.side_effect = lambda use_fallback=False: (
            mock_fallback if use_fallback else mock_primary
        )

        with pytest.raises(LLMCallError):
            call_with_retry_and_fallback(
                system_prompt="test",
                user_content="test",
                response_model=SimpleOutput,
                temperature=0.2,
            )

        assert mock_primary.call.call_count == 2
        assert mock_fallback.call.call_count == 1
