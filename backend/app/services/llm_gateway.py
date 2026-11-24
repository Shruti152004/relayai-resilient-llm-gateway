"""LiteLLM Gateway Service with Response Caching, Automatic Failover & Simulation.

Features:
  - Response caching via LiteLLM local cache keyed on (model, complete message context).
  - Cache hits return resolution_source="LLM_CACHE", key_id=null, fallback_attempts=0.
  - Complete cache read and write bypass on requests with X-Simulate-Failure.
  - Automatic fallback on HTTP 429, quota exhaustion, and 5xx errors.
  - Failover testing hook (X-Simulate-Failure) active when ENABLE_FAILURE_SIMULATION=true.
  - Accurate tracking of fallback_attempts.
  - HTTP 503 ('all providers unavailable') and database rollback when all keys fail.
  - Authentic provider token extraction without heuristic estimates.
"""

import logging
import time
from typing import Dict, List, Optional
import litellm
from app.api.schemas import ChatMetadata, ChatResponse
from app.config import KeyConfig, settings
from app.db.repository import repo
from app.services.cache_service import cache_service
from app.services.context_service import assemble_context

logger = logging.getLogger(__name__)

ALLOWED_SIMULATED_STATUSES = {429, 500, 502, 503}


class TokenUsageUnavailableError(Exception):
    """Raised when upstream provider response lacks authentic token usage metrics."""
    pass


class AllKeysFailedError(Exception):
    """Raised when all configured API keys have failed (rate-limited, quota, or 5xx)."""
    pass


def parse_simulate_failure_header(
    header_val: Optional[str],
    key_pool: List[KeyConfig],
) -> Dict[str, int]:
    """Parses X-Simulate-Failure header into a mapping of key_id -> status_code.

    Supports:
      - key_1=429
      - key_1=500
      - key_1=429,key_2=500
      - *=429 (applies to all keys in the pool)

    Allowed status codes: 429, 500, 502, 503.
    Honored strictly when ENABLE_FAILURE_SIMULATION=true.
    """
    if not header_val or not settings.ENABLE_FAILURE_SIMULATION:
        return {}

    simulated: Dict[str, int] = {}
    tokens = [t.strip() for t in header_val.split(",") if t.strip()]

    for token in tokens:
        if "=" not in token:
            continue
        target, status_str = token.split("=", 1)
        target = target.strip()
        status_str = status_str.strip()

        try:
            status_code = int(status_str)
        except ValueError:
            logger.warning("Invalid status code in simulation header: %s", status_str)
            continue

        if status_code not in ALLOWED_SIMULATED_STATUSES:
            logger.warning("Status code %d not in allowed simulation set %s", status_code, ALLOWED_SIMULATED_STATUSES)
            continue

        if target == "*":
            for k in key_pool:
                simulated[k.key_id] = status_code
        else:
            simulated[target] = status_code

    return simulated


def is_failover_trigger(exc: Exception) -> bool:
    """Determines whether an upstream exception warrants failing over to the next key.

    Triggers on HTTP 429, quota exhaustion, or 5xx server errors.
    """
    if isinstance(exc, (litellm.RateLimitError, litellm.InternalServerError, litellm.ServiceUnavailableError, litellm.APIConnectionError)):
        return True

    status_code = getattr(exc, "status_code", None)
    if status_code in (429, 500, 502, 503, 504):
        return True

    exc_str = str(exc).lower()
    if any(pattern in exc_str for pattern in ("429", "500", "502", "503", "quota", "rate limit", "overloaded")):
        return True

    return False


async def execute_chat(
    session_id: str,
    message: str,
    system_prompt: Optional[str] = None,
    x_simulate_failure: Optional[str] = None,
) -> ChatResponse:
    """Executes a chat request with response caching and automatic key failover.

    Behavior:
      1. Assembles full context: system prompt + message history + current message.
      2. If X-Simulate-Failure is present, bypasses cache reads and writes.
      3. If no simulation: checks LiteLLM cache. On cache hit:
           returns resolution_source="LLM_CACHE", key_id=null, fallback_attempts=0.
      4. On cache miss or simulation: executes failover loop across key pool.
      5. On live success: adds response to cache (if simulation was not active).
      6. On total failure: raises AllKeysFailedError with zero database writes.
    """
    start_time = time.perf_counter()

    # 1. Assemble context (system prompt + history + current message)
    context, _ = await assemble_context(
        session_id=session_id,
        message=message,
        system_prompt=system_prompt,
    )

    key_pool = settings.key_pool
    if not key_pool:
        logger.error("No API keys configured in LLM_API_KEYS pool.")
        raise AllKeysFailedError("all providers unavailable")

    # 2. Check failure simulation header
    simulated_failures = parse_simulate_failure_header(x_simulate_failure, key_pool)
    is_simulation_active = bool(simulated_failures)

    # 3. Cache Read Check (bypassed if failure simulation is active)
    if not is_simulation_active:
        cached_result = cache_service.get_cached_response(
            model=settings.LLM_MODEL,
            messages=context,
        )
        if cached_result is not None:
            reply_text, prompt_tokens, completion_tokens = cached_result
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Persist turn to SQLite for this session
            await repo.save_message(
                session_id=session_id,
                role="user",
                content=message,
            )
            await repo.save_message(
                session_id=session_id,
                role="assistant",
                content=reply_text,
                metadata={
                    "resolution_source": "LLM_CACHE",
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens,
                },
            )

            # Contract: key_id is strictly null on LLM_CACHE, fallback_attempts is 0
            metadata = ChatMetadata(
                resolution_source="LLM_CACHE",
                model=settings.LLM_MODEL,
                latency_ms=latency_ms,
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                key_id=None,
                fallback_attempts=0,
            )
            return ChatResponse(
                session_id=session_id,
                reply=reply_text,
                metadata=metadata,
            )

    # 4. Failover Loop across configured key pool
    fallback_attempts = 0
    successful_response = None
    successful_key = None
    last_error: Optional[str] = None

    for key_config in key_pool:
        # Check if current key is configured to simulate failure
        if key_config.key_id in simulated_failures:
            sim_code = simulated_failures[key_config.key_id]
            logger.info("Simulating HTTP %d failure on key %s", sim_code, key_config.key_id)
            fallback_attempts += 1
            last_error = f"Simulated HTTP {sim_code} on {key_config.key_id}"
            continue

        # Real inference attempt with this key
        try:
            logger.info("Attempting LLM inference with key alias: %s", key_config.key_id)
            response = litellm.completion(
                model=settings.LLM_MODEL,
                messages=context,
                api_key=key_config.secret_key if key_config.secret_key else None,
            )
            successful_response = response
            successful_key = key_config
            break
        except Exception as exc:
            logger.warning("Key %s failed with exception: %s", key_config.key_id, str(exc))
            fallback_attempts += 1
            last_error = str(exc)
            continue

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    # 5. Total Failure: Every key failed
    if successful_response is None or successful_key is None:
        logger.error(
            "All %d configured keys exhausted. Total fallback attempts: %d. Last error: %s",
            len(key_pool),
            fallback_attempts,
            last_error,
        )
        # CRITICAL: Zero messages recorded to SQLite history on total failure
        raise AllKeysFailedError("all providers unavailable")

    # 6. Extract and validate authentic provider-reported token usage
    usage = getattr(successful_response, "usage", None)
    if usage is None:
        raise TokenUsageUnavailableError("Token usage information is missing from provider response.")

    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)

    if prompt_tokens is None or completion_tokens is None:
        raise TokenUsageUnavailableError("Incomplete token counts reported by provider.")

    # 7. Extract assistant completion text
    if not getattr(successful_response, "choices", None) or len(successful_response.choices) == 0:
        raise AllKeysFailedError("all providers unavailable")

    choice = successful_response.choices[0]
    message_obj = getattr(choice, "message", None)
    reply_content = getattr(message_obj, "content", None) if message_obj else None

    if not reply_content or not reply_content.strip():
        raise AllKeysFailedError("all providers unavailable")

    reply_text = reply_content.strip()

    # 8. Cache Write (strictly skipped if simulation is active)
    if not is_simulation_active:
        cache_service.add_cached_response(
            model=settings.LLM_MODEL,
            messages=context,
            response=successful_response,
        )

    # 9. Persist successful conversational turn to SQLite
    await repo.save_message(
        session_id=session_id,
        role="user",
        content=message,
    )
    await repo.save_message(
        session_id=session_id,
        role="assistant",
        content=reply_text,
        metadata={
            "resolution_source": "LIVE_INFERENCE",
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
        },
    )

    # 10. Return response contract for live inference
    metadata = ChatMetadata(
        resolution_source="LIVE_INFERENCE",
        model=settings.LLM_MODEL,
        latency_ms=latency_ms,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
        key_id=successful_key.key_id,
        fallback_attempts=fallback_attempts,
    )

    return ChatResponse(
        session_id=session_id,
        reply=reply_text,
        metadata=metadata,
    )
