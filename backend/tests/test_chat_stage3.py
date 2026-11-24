"""Automated Tests for Stage 3: LiteLLM Integration, Context Assembly & POST /chat.

Uses mocked LiteLLM responses to ensure tests never consume real API credits.
"""

from unittest.mock import patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from litellm.types.utils import Choices, Message, ModelResponse, Usage
from app.db.database import init_db
from app.db.repository import repo


def make_mock_response(content: str = "Paris is the capital of France.", prompt_tokens: int = 42, completion_tokens: int = 9) -> ModelResponse:
    """Helper creating a valid LiteLLM ModelResponse fixture."""
    return ModelResponse(
        id="mock-cmpl-123",
        choices=[Choices(message=Message(content=content, role="assistant"))],
        usage=Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
        model="gemini/gemini-2.0-flash",
    )


@pytest.fixture(autouse=True)
async def setup_db():
    """Initializes schema before every test."""
    await init_db()


def test_successful_baseline_chat(client: TestClient):
    """Verifies baseline POST /chat endpoint execution with mocked LiteLLM."""
    mock_resp = make_mock_response(content="The capital of France is Paris.", prompt_tokens=42, completion_tokens=9)

    with patch("litellm.completion", return_value=mock_resp) as mock_llm:
        response = client.post(
            "/chat",
            json={
                "session_id": "s-stage3-success",
                "message": "What is the capital of France?",
                "system_prompt": "You are a concise tutor.",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["session_id"] == "s-stage3-success"
        assert data["reply"] == "The capital of France is Paris."

        meta = data["metadata"]
        assert meta["resolution_source"] == "LIVE_INFERENCE"
        assert meta["model"] == "gemini/gemini-2.0-flash"
        assert meta["input_tokens"] == 42
        assert meta["output_tokens"] == 9
        assert meta["key_id"] == "key_1"
        assert meta["fallback_attempts"] == 0
        assert isinstance(meta["latency_ms"], int)
        assert meta["latency_ms"] >= 0

        # Assert LiteLLM was called once
        assert mock_llm.call_count == 1


def test_context_assembly_and_multi_turn_memory(client: TestClient):
    """Verifies that Turn 2 includes system prompt, Turn 1 history, and Turn 2 user message."""
    resp1 = make_mock_response(content="Paris is the capital.", prompt_tokens=25, completion_tokens=6)
    resp2 = make_mock_response(content="Its population is about 2.1 million.", prompt_tokens=45, completion_tokens=10)

    with patch("litellm.completion", side_effect=[resp1, resp2]) as mock_llm:
        # Turn 1
        r1 = client.post(
            "/chat",
            json={
                "session_id": "s-multiturn",
                "message": "What is the capital of France?",
                "system_prompt": "You are a geography expert.",
            },
        )
        assert r1.status_code == status.HTTP_200_OK

        # Turn 2 (omitting system_prompt)
        r2 = client.post(
            "/chat",
            json={
                "session_id": "s-multiturn",
                "message": "What is its population?",
            },
        )
        assert r2.status_code == status.HTTP_200_OK

        # Inspect the messages payload passed to LiteLLM on Turn 2
        assert mock_llm.call_count == 2
        call_args_turn2 = mock_llm.call_args_list[1]
        sent_messages = call_args_turn2.kwargs.get("messages")

        assert len(sent_messages) == 4
        # 1. System prompt (persisted from Turn 1)
        assert sent_messages[0]["role"] == "system"
        assert sent_messages[0]["content"] == "You are a geography expert."

        # 2. Turn 1 user message
        assert sent_messages[1]["role"] == "user"
        assert sent_messages[1]["content"] == "What is the capital of France?"

        # 3. Turn 1 assistant message
        assert sent_messages[2]["role"] == "assistant"
        assert sent_messages[2]["content"] == "Paris is the capital."

        # 4. Turn 2 user message
        assert sent_messages[3]["role"] == "user"
        assert sent_messages[3]["content"] == "What is its population?"


def test_system_prompt_exclusion_from_public_history_after_chat(client: TestClient):
    """Verifies that while system prompts persist for LLM context,

    GET /sessions/{session_id}/messages excludes them from public history.
    """
    mock_resp = make_mock_response(content="Bonjour!", prompt_tokens=20, completion_tokens=3)

    with patch("litellm.completion", return_value=mock_resp):
        client.post(
            "/chat",
            json={
                "session_id": "s-history-check",
                "message": "Hi",
                "system_prompt": "SECRET_SYSTEM_INSTRUCTION: Always speak French.",
            },
        )

        hist_res = client.get("/sessions/s-history-check/messages")
        assert hist_res.status_code == status.HTTP_200_OK
        data = hist_res.json()

        assert len(data["messages"]) == 2
        for msg in data["messages"]:
            assert "SECRET_SYSTEM_INSTRUCTION" not in msg["content"]
            assert msg["role"] in ("user", "assistant")


@pytest.mark.asyncio
async def test_database_persistence_after_chat(client: TestClient):
    """Verifies that successful chat interactions are persisted in SQLite."""
    mock_resp = make_mock_response(content="Persisted assistant answer.", prompt_tokens=30, completion_tokens=5)

    with patch("litellm.completion", return_value=mock_resp):
        client.post(
            "/chat",
            json={
                "session_id": "s-db-verify",
                "message": "Persisted user question.",
            },
        )

        messages = await repo.get_session_messages("s-db-verify")
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Persisted user question."
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Persisted assistant answer."
        assert messages[1]["metadata"]["resolution_source"] == "LIVE_INFERENCE"


def test_missing_token_usage_error_handling(client: TestClient):
    """Verifies that missing token usage raises HTTP 502 rather than returning fake estimates."""
    broken_resp = ModelResponse(
        id="broken-resp",
        choices=[Choices(message=Message(content="Hello", role="assistant"))],
        usage=None,  # Missing usage object
    )

    with patch("litellm.completion", return_value=broken_resp):
        response = client.post(
            "/chat",
            json={
                "session_id": "s-missing-tokens",
                "message": "Hello without tokens",
            },
        )
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert "Token usage information is missing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_provider_error_handling_and_no_db_persistence(client: TestClient):
    """Verifies that provider errors return 503 and do not persist messages to history."""
    with patch("litellm.completion", side_effect=Exception("API connection refused")):
        response = client.post(
            "/chat",
            json={
                "session_id": "s-failed-req",
                "message": "This request fails upstream",
            },
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json() == {"detail": "all providers unavailable"}

        # Crucial check: neither user message nor assistant message is saved
        messages = await repo.get_session_messages("s-failed-req")
        assert len(messages) == 0


def test_api_key_security_in_response(client: TestClient):
    """Verifies that raw API keys are never exposed in response payloads."""
    mock_resp = make_mock_response()

    with patch("litellm.completion", return_value=mock_resp):
        response = client.post(
            "/chat",
            json={
                "session_id": "s-security-check",
                "message": "Testing secret safety",
            },
        )
        raw_text = response.text

        # Verify only alias is returned
        assert "key_1" in raw_text
        # Verify mock secret is not in text
        assert "test_mock_key_alpha" not in raw_text
        assert "test_mock_key_beta" not in raw_text

