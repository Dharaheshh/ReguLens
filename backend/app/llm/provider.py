"""LLM Provider abstraction — CORRECTION-001 / CORRECTION-003.

Single OpenAI-compatible adapter that works with Groq, Gemini, and OpenRouter.
Implements: try primary → retry primary → try fallback → failure state.
"""
import logging
from typing import TypeVar

from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMCallError(Exception):
    """Raised when all LLM call attempts (primary + retry + fallback) fail."""
    pass


class LLMProvider:
    """OpenAI-compatible LLM provider adapter.

    Works with any provider that speaks the OpenAI chat completions wire
    format (Groq, Gemini via compat endpoint, OpenRouter).
    """

    def __init__(self, base_url: str, api_key: str, model: str):
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = model

    def call(
        self,
        system_prompt: str,
        user_content: str,
        response_model: type[T],
        temperature: float,
    ) -> T:
        """Make an LLM call and parse the response through a Pydantic model.

        Args:
            system_prompt: System message content.
            user_content: User message content.
            response_model: Pydantic model to validate the response against.
            temperature: Sampling temperature.

        Returns:
            Parsed and validated Pydantic model instance.

        Raises:
            ValidationError: If the response doesn't match the schema.
            APIError: If the API call itself fails.
        """
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        raw = response.choices[0].message.content
        return response_model.model_validate_json(raw)


def get_provider(use_fallback: bool = False) -> LLMProvider:
    """Get a configured LLMProvider instance.

    Args:
        use_fallback: If True, returns the fallback provider (Gemini).

    Returns:
        Configured LLMProvider.
    """
    if use_fallback:
        return LLMProvider(
            settings.LLM_FALLBACK_BASE_URL,
            settings.LLM_FALLBACK_API_KEY,
            settings.LLM_FALLBACK_MODEL,
        )
    return LLMProvider(
        settings.LLM_BASE_URL,
        settings.LLM_API_KEY,
        settings.LLM_MODEL,
    )


def call_with_retry_and_fallback(
    system_prompt: str,
    user_content: str,
    response_model: type[T],
    temperature: float,
) -> T:
    """Call LLM with retry-once on primary, then fallback provider.

    Sequence per RULES.md rule #13 + CORRECTION-003:
    1. Try primary provider
    2. On failure: retry primary once
    3. On second failure: try fallback provider once
    4. On third failure: raise LLMCallError

    Args:
        system_prompt: System message content.
        user_content: User message content.
        response_model: Pydantic model to validate against.
        temperature: Sampling temperature.

    Returns:
        Parsed Pydantic model instance.

    Raises:
        LLMCallError: If all attempts fail.
    """
    primary = get_provider(use_fallback=False)

    # Attempt 1: primary
    try:
        return primary.call(system_prompt, user_content, response_model, temperature)
    except (ValidationError, APIError, APIConnectionError, RateLimitError, Exception) as e:
        logger.warning("Primary LLM attempt 1 failed: %s", e)

    # Attempt 2: primary retry
    try:
        return primary.call(system_prompt, user_content, response_model, temperature)
    except (ValidationError, APIError, APIConnectionError, RateLimitError, Exception) as e:
        logger.warning("Primary LLM attempt 2 failed: %s", e)

    # Attempt 3: fallback provider
    fallback = get_provider(use_fallback=True)
    try:
        return fallback.call(system_prompt, user_content, response_model, temperature)
    except (ValidationError, APIError, APIConnectionError, RateLimitError, Exception) as e:
        logger.error("Fallback LLM attempt failed: %s", e)
        raise LLMCallError(f"All LLM attempts failed. Last error: {e}") from e
