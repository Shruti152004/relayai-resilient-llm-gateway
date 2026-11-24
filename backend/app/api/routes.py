"""API Route Definitions for Health, Chat, and Session History.

Adheres strictly to the three-endpoint contract mandated by the assignment specification.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    SessionMessagesResponse,
)
from app.config import settings
from app.db.repository import repo
from app.services.llm_gateway import (
    execute_chat,
    AllKeysFailedError,
    TokenUsageUnavailableError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health and Readiness Probe",
    description="Returns 200 once app is running, DB is reachable, and key pool is loaded.",
)
async def get_health():
    """Health check endpoint confirming service status and key pool count."""
    return HealthResponse(
        status="ok",
        keys_configured=settings.keys_configured_count,
        cache_enabled=True,
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-turn Chat Completion with Key Failover and Caching",
)
async def post_chat(
    payload: ChatRequest,
    x_simulate_failure: Optional[str] = Header(None, alias="X-Simulate-Failure"),
):
    """Chat endpoint handler with automatic key failover and failure simulation test hook.

    When X-Simulate-Failure is sent (e.g. key_1=429), it forces chosen keys to fail
    inside that one request only, demonstrating failover without exhausting real keys.
    """
    try:
        return await execute_chat(
            session_id=payload.session_id,
            message=payload.message,
            system_prompt=payload.system_prompt,
            x_simulate_failure=x_simulate_failure,
        )
    except TokenUsageUnavailableError as exc:
        logger.error("Token metadata unavailable: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except AllKeysFailedError:
        logger.warning("All configured keys exhausted during chat request.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="all providers unavailable",
        )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=SessionMessagesResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Session History",
    description="Returns the stored history of one session from SQLite, oldest first, without the system prompt.",
)
async def get_session_messages(session_id: str):
    """Retrieves chronological message history for a session from SQLite.

    Returns 404 with {"detail": "session not found"} if the session is unknown.
    """
    exists = await repo.session_exists(session_id)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="session not found",
        )

    messages = await repo.get_session_messages(session_id)
    return SessionMessagesResponse(
        session_id=session_id,
        messages=messages,
    )
