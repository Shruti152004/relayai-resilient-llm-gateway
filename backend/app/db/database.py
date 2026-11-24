"""SQLite Database Connection and Schema Management.

Configures Write-Ahead Logging (WAL), foreign key constraints, busy timeout,
and automatic schema creation on startup.
Supports file persistence under Docker volume (/data/app.db), shared memory URIs,
and test databases.
"""

from contextlib import asynccontextmanager
import logging
import os
from typing import AsyncGenerator, Optional
import aiosqlite
from app.config import settings

logger = logging.getLogger(__name__)


def parse_sqlite_path(db_url: str) -> str:
    """Extracts raw file path or URI from a SQLite connection string.

    Supports formats like:
      - sqlite:///./data/app.db -> ./data/app.db
      - sqlite:////data/app.db  -> /data/app.db
      - sqlite:///file:mem?mode=memory&cache=shared -> file:mem?mode=memory&cache=shared
      - sqlite:///:memory:     -> :memory:
    """
    if db_url.startswith("sqlite:///"):
        return db_url[len("sqlite:///"):]
    return db_url


@asynccontextmanager
async def get_db(db_path: Optional[str] = None) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async context manager that yields a configured aiosqlite connection.

    Enforces:
      - PRAGMA foreign_keys = ON
      - PRAGMA journal_mode = WAL (file databases only)
      - PRAGMA busy_timeout = 5000
    """
    target_path = db_path if db_path is not None else parse_sqlite_path(settings.DATABASE_URL)
    is_uri = target_path.startswith("file:")
    is_memory = target_path == ":memory:" or "mode=memory" in target_path

    # Ensure parent directory exists for file-based databases
    if not is_memory and not is_uri:
        dir_name = os.path.dirname(os.path.abspath(target_path))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    conn = await aiosqlite.connect(target_path, uri=is_uri)
    conn.row_factory = aiosqlite.Row

    try:
        # Enforce foreign key constraints
        await conn.execute("PRAGMA foreign_keys = ON;")
        # Set busy timeout to 5000ms to avoid locking conflicts
        await conn.execute("PRAGMA busy_timeout = 5000;")
        # Enable WAL mode for high concurrency (for file-based databases)
        if not is_memory:
            await conn.execute("PRAGMA journal_mode = WAL;")

        yield conn
    finally:
        await conn.close()


async def init_db(db_path: Optional[str] = None):
    """Creates tables and indexes on application startup if they do not exist."""
    target_path = db_path if db_path is not None else parse_sqlite_path(settings.DATABASE_URL)
    logger.info("Initializing SQLite database schema at %s", target_path)

    async with get_db(target_path) as conn:
        # Table 1: Sessions (Stores session metadata and system prompt personas separately)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                system_prompt TEXT,
                created_at TEXT NOT NULL
            );
        """)

        # Table 2: Messages (Stores user and assistant conversational turns)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
        """)

        # Performance index for fast chronological message retrieval by session
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id_id
            ON messages (session_id, id ASC);
        """)

        await conn.commit()

    logger.info("SQLite database schema initialized successfully.")
