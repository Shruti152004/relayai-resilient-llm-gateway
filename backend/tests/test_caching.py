"""Tests verifying LiteLLM Cache mechanics and exact token preservation."""

import pytest
import litellm
from litellm.caching.caching import Cache
from litellm.types.utils import ModelResponse, Usage, Choices, Message


def test_litellm_cache_token_preservation_and_isolation():
    """Verifies that LiteLLM local cache preserves exact provider-reported tokens

    and never substitutes estimated values or leaks across distinct messages.
    """
    litellm.cache = Cache(type="local")
    model = "gemini/gemini-2.0-flash"

    # Simulated provider response with exact token metadata
    expected_prompt_tokens = 57
    expected_completion_tokens = 14

    original_response = ModelResponse(
        id="test-resp-uuid",
        choices=[Choices(message=Message(content="The capital of France is Paris.", role="assistant"))],
        usage=Usage(
            prompt_tokens=expected_prompt_tokens,
            completion_tokens=expected_completion_tokens,
        ),
        model=model,
    )

    msg_a = [{"role": "user", "content": "What is the capital of France?"}]
    msg_b = [{"role": "user", "content": "What is the capital of Germany?"}]

    # Populate cache for msg_a
    litellm.cache.add_cache(result=original_response, model=model, messages=msg_a)

    # 1. msg_a MUST hit cache
    cached_hit = litellm.cache.get_cache(model=model, messages=msg_a)
    assert cached_hit is not None, "Identical message should produce cache hit"

    usage = cached_hit.get("usage") if isinstance(cached_hit, dict) else cached_hit.usage
    actual_prompt_tokens = usage["prompt_tokens"] if isinstance(usage, dict) else usage.prompt_tokens
    actual_completion_tokens = usage["completion_tokens"] if isinstance(usage, dict) else usage.completion_tokens

    # Verify exact token preservation (no estimations)
    assert actual_prompt_tokens == expected_prompt_tokens
    assert actual_completion_tokens == expected_completion_tokens

    # 2. msg_b MUST miss cache (different prompt)
    miss_result = litellm.cache.get_cache(model=model, messages=msg_b)
    assert miss_result is None, "Different message must never hit cache"

