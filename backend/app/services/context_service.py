"""Context Assembly Service.

Manages multi-turn conversation memory by combining:
1. Active session system prompt (stored separately in SQLite `sessions` table).
2. Chronological previous message history from `messages` table.
3. Current user message.

Guarantees system prompts are never exposed in public message history endpoints.
"""

import logging
from typing import Dict, List, Optional, Tuple
from app.db.repository import repo

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = "You are a helpful, resilient AI assistant."


async def assemble_context(
    session_id: str,
    message: str,
    system_prompt: Optional[str] = None,
) -> Tuple[List[Dict[str, str]], str]:
    """Assembles the full chronological message payload for an LLM request.

    Returns:
        Tuple of (llm_context_messages, active_system_prompt)
    """
    # 1. Create or retrieve session with persistent system prompt persona
    session = await repo.create_or_update_session(
        session_id=session_id,
        system_prompt=system_prompt,
    )
    active_system_prompt = session.get("system_prompt") or DEFAULT_SYSTEM_PROMPT

    # 2. Retrieve chronological prior message history (user and assistant only)
    history = await repo.get_session_messages(session_id)

    # 3. Construct LLM context: System -> History -> Current Message
    context: List[Dict[str, str]] = [
        {"role": "system", "content": active_system_prompt}
    ]

    for item in history:
        context.append({
            "role": item["role"],
            "content": item["content"],
        })

    # 4. Append current user message
    context.append({
        "role": "user",
        "content": message,
    })

    return context, active_system_prompt

