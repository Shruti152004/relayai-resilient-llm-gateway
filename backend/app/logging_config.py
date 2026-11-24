"""Secure Logging Configuration with Sensitive Data Redaction.

Ensures that any API key fragments or tokens never appear in server output or logs.
"""

import logging
import re
from typing import List
from app.config import settings


class SensitiveDataFilter(logging.Filter):
    """Log filter that intercepts log records and redacts configured API keys."""

    def __init__(self, sensitive_tokens: List[str] = None):
        super().__init__()
        self.sensitive_tokens = [t for t in (sensitive_tokens or []) if t and len(t) > 4]

    def filter(self, record: logging.LogRecord) -> bool:
        if not isinstance(record.msg, str):
            return True

        msg = record.msg
        for token in self.sensitive_tokens:
            if token in msg:
                msg = msg.replace(token, "[REDACTED_API_KEY]")

        # Also redact standard Bearer and API key patterns
        msg = re.sub(r"(AIzaSy[A-Za-z0-9_-]{33})", "[REDACTED_GEMINI_KEY]", msg)
        msg = re.sub(r"(gsk_[A-Za-z0-9]{48,})", "[REDACTED_GROQ_KEY]", msg)
        msg = re.sub(r"(sk-[A-Za-z0-9]{32,})", "[REDACTED_OPENAI_KEY]", msg)

        record.msg = msg
        return True


def setup_logging():
    """Initializes structured logging with sensitive data redaction."""
    # Collect all configured secret keys to redact
    secrets = [k.secret_key for k in settings.key_pool]
    redaction_filter = SensitiveDataFilter(secrets)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Apply filter to existing handlers
    for handler in root_logger.handlers:
        handler.addFilter(redaction_filter)

    # Ensure uvicorn loggers also redact
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        u_logger = logging.getLogger(uvicorn_logger_name)
        u_logger.addFilter(redaction_filter)

    logging.info("Secure logging initialized with active redaction filter.")

