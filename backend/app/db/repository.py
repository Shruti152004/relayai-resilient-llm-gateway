"""Data Access Layer (Repository) for Sessions and Messages.

All queries use parameterized SQL statements to eliminate any SQL injection risk.
Stores system prompts separately in the sessions table to ensure they are never exposed
in public message history endpoints.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
import aiosqlite
from app.db.database import get_db

logger = logging.getLogger(__name__)


def current_iso_timestamp() -> str:
    """Returns the current server time in ISO-8601 UTC format."""
    return datetime.now(timezone.utc).isoformat()


class MessageRepository:
    """Repository handling all database operations for chat sessions and messages."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    async def create_or_update_session(
        self,
        session_id: str,
        system_prompt: Optional[str] = None,
        conn: Optional[aiosqlite.Connection] = None,
    ) -> Dict[str, Any]:
        """Creates a new session record or updates its system prompt if provided.

        System prompt is stored in the sessions table and is never inserted into
        the messages table.
        """
        async def _execute(c: aiosqlite.Connection):
            async with c.execute(
                "SELECT session_id, system_prompt, created_at FROM sessions WHERE session_id = ?",
                (session_id,),
            ) as cursor:
                existing = await cursor.fetchone()

            if existing:
                # If an explicit override system_prompt is supplied, update it
                if system_prompt is not None and system_prompt.strip():
                    await c.execute(
                        "UPDATE sessions SET system_prompt = ? WHERE session_id = ?",
                        (system_prompt.strip(), session_id),
                    )
                    await c.commit()
                    return {
                        "session_id": session_id,
                        "system_prompt": system_prompt.strip(),
                        "created_at": existing["created_at"],
                    }
                return dict(existing)

            # Insert new session
            created_at = current_iso_timestamp()
            prompt_val = system_prompt.strip() if system_prompt else None
            await c.execute(
                "INSERT INTO sessions (session_id, system_prompt, created_at) VALUES (?, ?, ?)",
                (session_id, prompt_val, created_at),
            )
            await c.commit()
            return {
                "session_id": session_id,
                "system_prompt": prompt_val,
                "created_at": created_at,
            }

        if conn is not None:
            return await _execute(conn)
        async with get_db(self.db_path) as connection:
            return await _execute(connection)

    async def get_session(
        self,
        session_id: str,
        conn: Optional[aiosqlite.Connection] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieves session record by session_id, or None if unknown."""
        async def _execute(c: aiosqlite.Connection):
            async with c.execute(
                "SELECT session_id, system_prompt, created_at FROM sessions WHERE session_id = ?",
                (session_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

        if conn is not None:
            return await _execute(conn)
        async with get_db(self.db_path) as connection:
            return await _execute(connection)

    async def session_exists(
        self,
        session_id: str,
        conn: Optional[aiosqlite.Connection] = None,
    ) -> bool:
        """Returns True if the session exists in SQLite, False otherwise."""
        session = await self.get_session(session_id, conn=conn)
        return session is not None

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        conn: Optional[aiosqlite.Connection] = None,
    ) -> int:
        """Saves a user or assistant message to SQLite.

        Metadata is stored as a JSON string for assistant messages only.
        Foreign key constraint automatically validates that session_id exists.
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid message role '{role}'. Must be 'user' or 'assistant'.")

        metadata_str = None
        if role == "assistant" and metadata is not None:
            metadata_str = json.dumps(metadata)

        created_at = current_iso_timestamp()

        async def _execute(c: aiosqlite.Connection):
            cursor = await c.execute(
                """
                INSERT INTO messages (session_id, role, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, role, content, metadata_str, created_at),
            )
            await c.commit()
            return cursor.lastrowid

        if conn is not None:
            return await _execute(conn)
        async with get_db(self.db_path) as connection:
            return await _execute(connection)

    async def get_session_messages(
        self,
        session_id: str,
        conn: Optional[aiosqlite.Connection] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves the chronological message history for a session (oldest first).

        The system prompt is never stored in the messages table and is strictly
        excluded from this output.
        """
        async def _execute(c: aiosqlite.Connection):
            async with c.execute(
                """
                SELECT id, role, content, metadata, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()

            messages = []
            for row in rows:
                row_dict = dict(row)
                meta_val = None
                if row_dict["role"] == "assistant" and row_dict["metadata"]:
                    try:
                        meta_val = json.loads(row_dict["metadata"])
                    except Exception:
                        meta_val = None

                item = {
                    "role": row_dict["role"],
                    "content": row_dict["content"],
                }
                if meta_val:
                    item["metadata"] = meta_val
                messages.append(item)
            return messages

        if conn is not None:
            return await _execute(conn)
        async with get_db(self.db_path) as connection:
            return await _execute(connection)


# Default repository instance
repo = MessageRepository()

