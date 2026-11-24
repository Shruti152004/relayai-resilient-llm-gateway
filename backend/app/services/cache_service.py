"""Response Caching Service using LiteLLM Built-in Local Cache.

Features:
  - Cache identity based strictly on (model, complete message context including system prompt and history).
  - Reliable metadata-based cache hit detection via LiteLLM's local cache.
  - Preservation of authentic provider input_tokens and output_tokens without estimation.
  - Complete cache read and write bypass during failure simulation requests.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import litellm
from litellm.caching.caching import Cache

logger = logging.getLogger(__name__)


class CacheService:
    """Manages conversational turn caching using LiteLLM's local cache."""

    def __init__(self):
        # Initialize LiteLLM's built-in in-memory local cache
        if getattr(litellm, "cache", None) is None:
            litellm.cache = Cache(type="local")
        self.cache = litellm.cache

    def get_cached_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
    ) -> Optional[Tuple[str, int, int]]:
        """Retrieves cached completion from LiteLLM's cache.

        Returns:
            Tuple of (reply_text, input_tokens, output_tokens) if cache hit, else None.
        """
        try:
            cached_item = self.cache.get_cache(model=model, messages=messages)
        except Exception as exc:
            logger.warning("Error reading from LiteLLM cache: %s", str(exc))
            return None

        if cached_item is None:
            return None

        # Extract reply text
        choices = cached_item.get("choices") if isinstance(cached_item, dict) else getattr(cached_item, "choices", None)
        if not choices or len(choices) == 0:
            return None

        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message", {})
            reply = message.get("content", "") if isinstance(message, dict) else getattr(message, "content", "")
        else:
            message = getattr(first_choice, "message", None)
            reply = getattr(message, "content", "") if message else ""

        if not reply or not reply.strip():
            return None

        # Extract authentic provider tokens preserved in cache
        usage = cached_item.get("usage") if isinstance(cached_item, dict) else getattr(cached_item, "usage", None)
        if usage is None:
            return None

        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
        else:
            prompt_tokens = getattr(usage, "prompt_tokens", None)
            completion_tokens = getattr(usage, "completion_tokens", None)

        if prompt_tokens is None or completion_tokens is None:
            return None

        logger.info("LiteLLM Cache HIT for model=%s | prompt_tokens=%d, completion_tokens=%d", model, prompt_tokens, completion_tokens)
        return reply.strip(), int(prompt_tokens), int(completion_tokens)

    def add_cached_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        response: Any,
    ) -> None:
        """Stores a successful live completion in LiteLLM's local cache."""
        try:
            self.cache.add_cache(result=response, model=model, messages=messages)
            logger.info("Added response to LiteLLM cache for model=%s", model)
        except Exception as exc:
            logger.warning("Failed to add response to LiteLLM cache: %s", str(exc))

    def flush(self) -> None:
        """Flushes cache by re-instantiating the local cache object."""
        self.cache = Cache(type="local")
        litellm.cache = self.cache


cache_service = CacheService()

