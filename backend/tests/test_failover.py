"""Automated Tests for Stage 4: API Key Failover and Failure Simulation Hook.

Tests:
  - Primary key success (fallback_attempts = 0, key_id = key_1).
  - Simulated failure hook (key_1=429, key_1=500) failing over to key_2.
  - Consecutive simulated failures (key_1=429,key_2=500) failing over to key_3.
  - Real upstream rate limit (429) triggering failover.
  - Real upstream quota exhaustion triggering failover.
  - Real upstream server errors (500, 502, 503) triggering failover.
  - Total exhaustion (*=429 and all keys failing) returning 503 without database writes.
  - Invalid simulation header resilience.
  - Simulation disabled switch (ENABLE_FAILURE_SIMULATION=false).
  - Zero API key leakage.
"""

from unittest.mock import patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from litellm.types.utils import Choices, Message, ModelResponse, Usage
import litellm
from app.config import settings
from app.db.database import init_db
from app.db.repository import repo


def make_response(content: str = "Reliable AI answer.", prompt_tokens: int = 40, completion_tokens: int = 12) -> ModelResponse:
    """Helper creating a valid LiteLLM ModelResponse."""
    return ModelResponse(
        id="mock-resp-id",
        choices=[Choices(message=Message(content=content, role="assistant"))],
        usage=Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
        model="gemini/gemini-2.0-flash",
    )


@pytest.fixture(autouse=True)
async def setup_db():
    """Initializes schema before each test."""
    await init_db()


def test_primary_key_success(client: TestClient):
    """Verifies that under normal conditions key_1 succeeds with fallback_attempts = 0."""
    resp = make_response(content="Primary key succeeded.")

    with patch("litellm.completion", return_value=resp):
        response = client.post(
            "/chat",
            json={
                "session_id": "s-primary-key",
                "message": "Hello from primary",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["metadata"]["key_id"] == "key_1"
        assert data["metadata"]["fallback_attempts"] == 0
        assert data["metadata"]["resolution_source"] == "LIVE_INFERENCE"


def test_simulated_failure_key1_429(client: TestClient):
    """Verifies X-Simulate-Failure: key_1=429 triggers failover to key_2 with fallback_attempts = 1.

    Matches PDF Table:
    Header: key_1=429 -> Expected: 200, key_id = key_2
    """
    resp = make_response(content="Answer from key_2.")

    with patch("litellm.completion", return_value=resp):
        response = client.post(
            "/chat",
            headers={"X-Simulate-Failure": "key_1=429"},
            json={
                "session_id": "s-sim-429",
                "message": "What is the speed of sound?",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["reply"] == "Answer from key_2."
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1
        assert data["metadata"]["resolution_source"] == "LIVE_INFERENCE"


def test_simulated_failure_key1_500(client: TestClient):
    """Verifies X-Simulate-Failure: key_1=500 triggers failover to key_2 with fallback_attempts = 1.

    Matches PDF Table:
    Header: key_1=500 -> Expected: 200, key_id = key_2
    """
    resp = make_response(content="Server error recovered on key_2.")

    with patch("litellm.completion", return_value=resp):
        response = client.post(
            "/chat",
            headers={"X-Simulate-Failure": "key_1=500"},
            json={
                "session_id": "s-sim-500",
                "message": "How does gravity work?",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1


def test_consecutive_simulated_failures_key1_key2(client: TestClient):
    """Verifies X-Simulate-Failure: key_1=429,key_2=500 fails over to key_3."""
    resp = make_response(content="Answer from third key.")

    with patch.object(settings, "LLM_API_KEYS", "secret1,secret2,secret3"):
        with patch("litellm.completion", return_value=resp):
            response = client.post(
                "/chat",
                headers={"X-Simulate-Failure": "key_1=429,key_2=500"},
                json={
                    "session_id": "s-consecutive",
                    "message": "Test multi-failover",
                },
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["metadata"]["key_id"] == "key_3"
            assert data["metadata"]["fallback_attempts"] == 2


@pytest.mark.asyncio
async def test_simulated_total_failure_wildcard_429(client: TestClient):
    """Verifies X-Simulate-Failure: *=429 returns 503 and writes nothing to SQLite.

    Matches PDF Table:
    Header: *=429 -> Expected: 503 {"detail": "all providers unavailable"}, nothing added to history
    """
    response = client.post(
        "/chat",
        headers={"X-Simulate-Failure": "*=429"},
        json={
            "session_id": "s-exhaust-sim",
            "message": "This will fail all keys",
        },
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "all providers unavailable"}

    # Confirm zero messages in SQLite
    messages = await repo.get_session_messages("s-exhaust-sim")
    assert len(messages) == 0


def test_real_upstream_rate_limit_failover(client: TestClient):
    """Verifies that an authentic upstream 429 exception on key_1 triggers failover to key_2."""
    rate_limit_err = litellm.RateLimitError(
        message="Rate limit exceeded on key 1",
        model="gemini/gemini-2.0-flash",
        llm_provider="gemini",
    )
    success_resp = make_response(content="Recovered from real 429.")

    with patch("litellm.completion", side_effect=[rate_limit_err, success_resp]):
        response = client.post(
            "/chat",
            json={
                "session_id": "s-real-429",
                "message": "Trigger real rate limit",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1


def test_real_upstream_quota_error_failover(client: TestClient):
    """Verifies that a quota exhausted error string on key_1 triggers failover to key_2."""
    quota_err = Exception("Resource has been exhausted (e.g. check quota).")
    success_resp = make_response(content="Recovered from quota error.")

    with patch("litellm.completion", side_effect=[quota_err, success_resp]):
        response = client.post(
            "/chat",
            json={
                "session_id": "s-quota-failover",
                "message": "Testing quota error recovery",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1


def test_real_upstream_503_server_error_failover(client: TestClient):
    """Verifies that an upstream 503 Service Unavailable triggers failover to key_2."""
    server_err = litellm.ServiceUnavailableError(
        message="Model is temporarily overloaded",
        model="gemini/gemini-2.0-flash",
        llm_provider="gemini",
    )
    success_resp = make_response(content="Recovered from 503 overload.")

    with patch("litellm.completion", side_effect=[server_err, success_resp]):
        response = client.post(
            "/chat",
            json={
                "session_id": "s-503-failover",
                "message": "Testing 503 overload recovery",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1


@pytest.mark.asyncio
async def test_all_real_keys_failing_returns_503(client: TestClient):
    """Verifies that when all configured keys raise real provider exceptions,

    returns 503 {"detail": "all providers unavailable"} and commits nothing to DB.
    """
    err1 = Exception("HTTP 500 Internal Server Error")
    err2 = Exception("HTTP 503 Service Unavailable")

    with patch("litellm.completion", side_effect=[err1, err2]):
        response = client.post(
            "/chat",
            json={
                "session_id": "s-all-real-fail",
                "message": "Testing total real outage",
            },
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json() == {"detail": "all providers unavailable"}

        # Verify nothing persisted to database
        messages = await repo.get_session_messages("s-all-real-fail")
        assert len(messages) == 0


def test_invalid_simulation_header_handled_gracefully(client: TestClient):
    """Verifies that malformed simulation headers do not crash the endpoint."""
    resp = make_response(content="Handled malformed header cleanly.")

    with patch("litellm.completion", return_value=resp):
        response = client.post(
            "/chat",
            headers={"X-Simulate-Failure": "malformed_token,key_1=invalid,key_1=999"},
            json={
                "session_id": "s-malformed-hdr",
                "message": "Testing malformed simulation headers",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["metadata"]["key_id"] == "key_1"


def test_simulation_disabled_switch(client: TestClient):
    """Verifies that when ENABLE_FAILURE_SIMULATION=false, X-Simulate-Failure is ignored."""
    resp = make_response(content="Simulation disabled, key 1 used.")

    with patch.object(settings, "ENABLE_FAILURE_SIMULATION", False):
        with patch("litellm.completion", return_value=resp):
            response = client.post(
                "/chat",
                headers={"X-Simulate-Failure": "key_1=429"},
                json={
                    "session_id": "s-sim-disabled",
                    "message": "Simulation switch test",
                },
            )
            assert response.status_code == status.HTTP_200_OK
            # With simulation disabled, key_1 is NOT simulated to fail
            assert response.json()["metadata"]["key_id"] == "key_1"
            assert response.json()["metadata"]["fallback_attempts"] == 0


def test_api_key_security_during_failover(client: TestClient):
    """Verifies that raw API secrets never leak into failover response metadata."""
    resp = make_response(content="Secret security verified.")

    with patch("litellm.completion", return_value=resp):
        response = client.post(
            "/chat",
            headers={"X-Simulate-Failure": "key_1=429"},
            json={
                "session_id": "s-sec-failover",
                "message": "Security audit",
            },
        )
        raw_text = response.text
        assert "key_2" in raw_text
        assert "test_mock_key_alpha" not in raw_text
        assert "test_mock_key_beta" not in raw_text

