"""Tests for Sensitive Data Logging Redaction Filter."""

import logging
from app.logging_config import SensitiveDataFilter


def test_sensitive_data_filter_redaction():
    """Ensures secret tokens and known API key patterns are masked."""
    secret = "AIzaSySecretTestKeyValue1234567890"
    filter_instance = SensitiveDataFilter([secret])

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg=f"Calling model with key: {secret}",
        args=(),
        exc_info=None,
    )

    filter_instance.filter(record)

    assert secret not in record.msg
    assert "[REDACTED" in record.msg

