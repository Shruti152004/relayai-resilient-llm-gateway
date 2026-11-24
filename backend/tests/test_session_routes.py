"""Automated API Integration Tests for Session Messages Endpoint."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from app.db.database import init_db
from app.db.repository import repo
from app.main import app


@pytest.fixture(autouse=True)
async def prepare_test_db():
    """Initializes the database schema before each endpoint test."""
    await init_db()


def test_unknown_session_returns_404(client: TestClient):
    """Verifies that querying a non-existent session strictly returns HTTP 404

    with {"detail": "session not found"} as required by the assignment specification.
    """
    response = client.get("/sessions/unknown-session-uuid-9999/messages")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "session not found"


@pytest.mark.asyncio
async def test_existing_session_history_200(client: TestClient):
    """Verifies that GET /sessions/{session_id}/messages returns 200 with chronological history

    and strictly excludes the stored system prompt.
    """
    session_id = "s-existing-test-42"
    # Seed session and messages in SQLite
    await repo.create_or_update_session(
        session_id=session_id,
        system_prompt="You are an expert French translator.",
    )
    await repo.save_message(
        session_id=session_id,
        role="user",
        content="What is the capital of France?",
    )
    await repo.save_message(
        session_id=session_id,
        role="assistant",
        content="The capital of France is Paris.",
        metadata={
            "resolution_source": "LIVE_INFERENCE",
            "input_tokens": 42,
            "output_tokens": 9,
        },
    )

    response = client.get(f"/sessions/{session_id}/messages")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["session_id"] == session_id
    assert "messages" in data
    messages = data["messages"]
    assert len(messages) == 2

    # User message verification
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What is the capital of France?"
    assert messages[0].get("metadata") is None

    # Assistant message verification
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "The capital of France is Paris."
    assert messages[1]["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert messages[1]["metadata"]["input_tokens"] == 42
    assert messages[1]["metadata"]["output_tokens"] == 9

    # System prompt strictly excluded
    for msg in messages:
        assert "French translator" not in msg["content"]
        assert msg["role"] != "system"

