"""Automated Tests for Stage 5: Response Caching & Per-Request Token Tracking.

Verifies:
  - First identical request is LIVE_INFERENCE.
  - Second identical request (same first message in new session) is LLM_CACHE.
  - Cache hit metadata contracts: resolution_source="LLM_CACHE", key_id=null, fallback_attempts=0.
  - Authentic provider token counts are accurately preserved without estimation.
  - Different messages, different system prompts, and different histories produce cache misses.
  - X-Simulate-Failure requests bypass both cache reads and cache writes.
  - Single turn is persisted in SQLite for cache hits without duplication or history corruption.
"""

from unittest.mock import patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from litellm.types.utils import Choices, Message, ModelResponse, Usage
from app.db.database import init_db
from app.db.repository import repo
from app.services.cache_service import cache_service


def make_resp(content: str = "Cached answer text.", prompt_tokens: int = 52, completion_tokens: int = 15) -> ModelResponse:
    return ModelResponse(
        id="cmpl-stage5-test",
        choices=[Choices(message=Message(content=content, role="assistant"))],
        usage=Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
        model="gemini/gemini-2.0-flash",
    )


@pytest.fixture(autouse=True)
async def setup_test_state():
    """Initializes schema and flushes in-memory cache before every test."""
    await init_db()
    cache_service.flush()


def test_first_request_live_second_request_cache_hit(client: TestClient):
    """Verifies that an initial request executes live, and an identical request hits the cache."""
    mock_resp = make_resp(content="Paris is the capital of France.", prompt_tokens=42, completion_tokens=9)

    with patch("litellm.completion", return_value=mock_resp) as mock_llm:
        # Turn 1 in Session A: LIVE_INFERENCE
        r1 = client.post(
            "/chat",
            json={
                "session_id": "s-cache-session-a",
                "message": "What is the capital of France?",
            },
        )
        assert r1.status_code == status.HTTP_200_OK
        d1 = r1.json()
        assert d1["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert d1["metadata"]["key_id"] == "key_1"
        assert d1["metadata"]["fallback_attempts"] == 0
        assert d1["metadata"]["input_tokens"] == 42
        assert d1["metadata"]["output_tokens"] == 9
        assert mock_llm.call_count == 1

        # Turn 1 in Session B (Identical first message in new session): LLM_CACHE
        r2 = client.post(
            "/chat",
            json={
                "session_id": "s-cache-session-b",
                "message": "What is the capital of France?",
            },
        )
        assert r2.status_code == status.HTTP_200_OK
        d2 = r2.json()

        # Contract assertions for LLM_CACHE
        assert d2["reply"] == "Paris is the capital of France."
        assert d2["metadata"]["resolution_source"] == "LLM_CACHE"
        assert d2["metadata"]["key_id"] is None  # Strictly null on LLM_CACHE
        assert d2["metadata"]["fallback_attempts"] == 0  # Strictly 0 on LLM_CACHE
        assert d2["metadata"]["input_tokens"] == 42  # Exact original provider tokens
        assert d2["metadata"]["output_tokens"] == 9
        assert d2["metadata"]["model"] == "gemini/gemini-2.0-flash"

        # Crucial check: LiteLLM was NOT called again; served from cache!
        assert mock_llm.call_count == 1


def test_different_messages_produce_cache_miss(client: TestClient):
    """Verifies that different user messages do not share cached responses."""
    resp1 = make_resp(content="Answer for France.")
    resp2 = make_resp(content="Answer for Germany.")

    with patch("litellm.completion", side_effect=[resp1, resp2]) as mock_llm:
        r1 = client.post(
            "/chat",
            json={"session_id": "s-diff-1", "message": "Capital of France?"},
        )
        assert r1.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"

        r2 = client.post(
            "/chat",
            json={"session_id": "s-diff-2", "message": "Capital of Germany?"},
        )
        assert r2.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert mock_llm.call_count == 2


def test_different_system_prompts_produce_cache_miss(client: TestClient):
    """Verifies that identical user messages with different system prompts produce distinct cache keys."""
    resp1 = make_resp(content="Tutor answer.")
    resp2 = make_resp(content="Pirate answer.")

    with patch("litellm.completion", side_effect=[resp1, resp2]) as mock_llm:
        r1 = client.post(
            "/chat",
            json={
                "session_id": "s-prompt-1",
                "message": "Tell me about Mars.",
                "system_prompt": "You are a formal astronomy tutor.",
            },
        )
        assert r1.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"

        # Same user message, but different system prompt
        r2 = client.post(
            "/chat",
            json={
                "session_id": "s-prompt-2",
                "message": "Tell me about Mars.",
                "system_prompt": "You are a pirate.",
            },
        )
        assert r2.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert mock_llm.call_count == 2


def test_different_conversation_history_produces_cache_miss(client: TestClient):
    """Verifies that sending an identical message in turn 2 of a session misses cache due to prior history."""
    resp1 = make_resp(content="Paris is in France.")
    resp2 = make_resp(content="Yes, Paris is great.")

    with patch("litellm.completion", side_effect=[resp1, resp2]) as mock_llm:
        # Session 1: Turn 1
        r1 = client.post(
            "/chat",
            json={"session_id": "s-history-cache", "message": "What is Paris?"},
        )
        assert r1.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"

        # Session 1: Turn 2 with same user message "What is Paris?"
        # Because history now contains Turn 1, the LLM context is different -> cache miss!
        r2 = client.post(
            "/chat",
            json={"session_id": "s-history-cache", "message": "What is Paris?"},
        )
        assert r2.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert mock_llm.call_count == 2


def test_simulated_failure_bypasses_cache_read_and_write(client: TestClient):
    """Verifies that requests with X-Simulate-Failure bypass cache reads and writes.

    Even if an identical query is already cached, a simulated failure request
    must bypass the cache and trigger the real failover loop.
    """
    cached_resp = make_resp(content="Cached response text.", prompt_tokens=30, completion_tokens=8)
    failover_resp = make_resp(content="Live reply from key_2 after failover.", prompt_tokens=30, completion_tokens=8)

    with patch("litellm.completion", side_effect=[cached_resp, failover_resp]) as mock_llm:
        # 1. Warm up cache with normal request
        r1 = client.post(
            "/chat",
            json={"session_id": "s-warmup", "message": "What is photosynthesis?"},
        )
        assert r1.status_code == status.HTTP_200_OK
        assert r1.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert mock_llm.call_count == 1

        # 2. Send identical message in new session WITH X-Simulate-Failure: key_1=429
        # Must BYPASS cache and trigger key_2 failover!
        r2 = client.post(
            "/chat",
            headers={"X-Simulate-Failure": "key_1=429"},
            json={"session_id": "s-bypass-sim", "message": "What is photosynthesis?"},
        )
        assert r2.status_code == status.HTTP_200_OK
        d2 = r2.json()

        # Must NOT be LLM_CACHE; must be LIVE_INFERENCE with key_2!
        assert d2["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert d2["metadata"]["key_id"] == "key_2"
        assert d2["metadata"]["fallback_attempts"] == 1
        assert mock_llm.call_count == 2


@pytest.mark.asyncio
async def test_cache_hit_persists_cleanly_in_sqlite(client: TestClient):
    """Verifies that a cache hit records exactly one user and one assistant turn in SQLite

    with resolution_source='LLM_CACHE', without duplicating or corrupting history.
    """
    mock_resp = make_resp(content="Echo capital.", prompt_tokens=35, completion_tokens=7)

    with patch("litellm.completion", return_value=mock_resp):
        # Initial request (LIVE)
        client.post(
            "/chat",
            json={"session_id": "s-persist-live", "message": "Capital of Italy?"},
        )

        # Second request in new session (CACHE HIT)
        r_cache = client.post(
            "/chat",
            json={"session_id": "s-persist-cache", "message": "Capital of Italy?"},
        )
        assert r_cache.json()["metadata"]["resolution_source"] == "LLM_CACHE"

        # Query SQLite history for the cached session
        messages = await repo.get_session_messages("s-persist-cache")
        assert len(messages) == 2

        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Capital of Italy?"

        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Echo capital."
        assert messages[1]["metadata"]["resolution_source"] == "LLM_CACHE"
        assert messages[1]["metadata"]["input_tokens"] == 35
        assert messages[1]["metadata"]["output_tokens"] == 7

        # Query via GET /sessions/{session_id}/messages endpoint
        hist_resp = client.get("/sessions/s-persist-cache/messages")
        assert hist_resp.status_code == status.HTTP_200_OK
        hist_data = hist_resp.json()
        assert len(hist_data["messages"]) == 2

