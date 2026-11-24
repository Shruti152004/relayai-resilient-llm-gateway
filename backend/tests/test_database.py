"""Automated Unit Tests for SQLite Database Initialization, Schema, and Repository."""

import os
import tempfile
import pytest
import aiosqlite
from app.db.database import get_db, init_db, parse_sqlite_path
from app.db.repository import MessageRepository


@pytest.fixture
def temp_db_path():
    """Provides a temporary SQLite database file path that is cleaned up after testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.mark.asyncio
async def test_database_initialization_and_tables(temp_db_path):
    """Verifies that init_db creates sessions and messages tables, indexes, and pragmas."""
    await init_db(temp_db_path)

    async with get_db(temp_db_path) as conn:
        # Check tables existence
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('sessions', 'messages')"
        ) as cursor:
            tables = [row[0] for row in await cursor.fetchall()]

        assert "sessions" in tables
        assert "messages" in tables

        # Check index existence
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name = 'idx_messages_session_id_id'"
        ) as cursor:
            idx = await cursor.fetchone()
        assert idx is not None

        # Verify PRAGMA settings
        async with conn.execute("PRAGMA foreign_keys") as cursor:
            fk = await cursor.fetchone()
            assert fk[0] == 1  # Foreign keys active


@pytest.mark.asyncio
async def test_session_creation_and_update(temp_db_path):
    """Verifies session creation and system prompt update logic."""
    await init_db(temp_db_path)
    repo = MessageRepository(temp_db_path)

    # Create session with initial system prompt
    s1 = await repo.create_or_update_session("s-test-1", system_prompt="You are a helpful tutor.")
    assert s1["session_id"] == "s-test-1"
    assert s1["system_prompt"] == "You are a helpful tutor."

    # Update system prompt on existing session
    s2 = await repo.create_or_update_session("s-test-1", system_prompt="You are a pirate.")
    assert s2["system_prompt"] == "You are a pirate."

    # Retrieve session
    fetched = await repo.get_session("s-test-1")
    assert fetched is not None
    assert fetched["system_prompt"] == "You are a pirate."


@pytest.mark.asyncio
async def test_message_insertion_and_retrieval(temp_db_path):
    """Verifies insertion of user and assistant messages with metadata serialization."""
    await init_db(temp_db_path)
    repo = MessageRepository(temp_db_path)

    await repo.create_or_update_session("s-test-2")

    user_msg_id = await repo.save_message("s-test-2", role="user", content="Hello!")
    assert user_msg_id > 0

    assistant_meta = {
        "resolution_source": "LIVE_INFERENCE",
        "input_tokens": 15,
        "output_tokens": 8,
    }
    asst_msg_id = await repo.save_message(
        "s-test-2",
        role="assistant",
        content="Hello, human!",
        metadata=assistant_meta,
    )
    assert asst_msg_id > user_msg_id

    messages = await repo.get_session_messages("s-test-2")
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello!"
    assert "metadata" not in messages[0] or messages[0].get("metadata") is None

    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hello, human!"
    assert messages[1]["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert messages[1]["metadata"]["input_tokens"] == 15
    assert messages[1]["metadata"]["output_tokens"] == 8


@pytest.mark.asyncio
async def test_chronological_ordering(temp_db_path):
    """Ensures messages are strictly returned in chronological order (oldest first)."""
    await init_db(temp_db_path)
    repo = MessageRepository(temp_db_path)

    await repo.create_or_update_session("s-chrono")

    for i in range(5):
        await repo.save_message("s-chrono", role="user", content=f"Message {i}")

    messages = await repo.get_session_messages("s-chrono")
    assert len(messages) == 5
    for i in range(5):
        assert messages[i]["content"] == f"Message {i}"


@pytest.mark.asyncio
async def test_foreign_key_enforcement(temp_db_path):
    """Verifies that inserting a message for an uncreated session raises IntegrityError."""
    await init_db(temp_db_path)
    repo = MessageRepository(temp_db_path)

    with pytest.raises(aiosqlite.IntegrityError):
        # Session "non-existent-session" was never created in sessions table
        await repo.save_message("non-existent-session", role="user", content="Ghost message")


@pytest.mark.asyncio
async def test_system_prompt_exclusion_from_messages(temp_db_path):
    """Verifies that system prompts are never returned in public message history."""
    await init_db(temp_db_path)
    repo = MessageRepository(temp_db_path)

    await repo.create_or_update_session(
        "s-secret-prompt",
        system_prompt="CRITICAL: This is a confidential system instruction.",
    )
    await repo.save_message("s-secret-prompt", role="user", content="Tell me a joke.")
    await repo.save_message("s-secret-prompt", role="assistant", content="Why did the chicken cross the road?")

    history = await repo.get_session_messages("s-secret-prompt")

    # History must contain exactly the user and assistant turns
    assert len(history) == 2
    for msg in history:
        assert "CRITICAL" not in msg["content"]
        assert msg["role"] in ("user", "assistant")


@pytest.mark.asyncio
async def test_database_persistence_across_reconnections(temp_db_path):
    """Verifies that data stored in SQLite persists across connection closes and reopens."""
    await init_db(temp_db_path)

    # 1. First connection: write data
    repo1 = MessageRepository(temp_db_path)
    await repo1.create_or_update_session("s-persist", system_prompt="Persona 1")
    await repo1.save_message("s-persist", role="user", content="Persistent data")

    # 2. Second independent connection to the same file
    repo2 = MessageRepository(temp_db_path)
    session = await repo2.get_session("s-persist")
    messages = await repo2.get_session_messages("s-persist")

    assert session is not None
    assert session["system_prompt"] == "Persona 1"
    assert len(messages) == 1
    assert messages[0]["content"] == "Persistent data"

