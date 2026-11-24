"""Tests for Application Configuration and Safe Environment Parsing."""

from app.config import Settings, KeyConfig


def test_key_pool_parsing():
    """Verifies that comma-separated keys are parsed into key_1, key_2 aliases."""
    test_keys = "key_secret_one, key_secret_two, key_secret_three"
    settings = Settings(LLM_API_KEYS=test_keys)

    assert settings.keys_configured_count == 3
    pool = settings.key_pool
    assert len(pool) == 3

    assert pool[0].key_id == "key_1"
    assert pool[0].secret_key == "key_secret_one"

    assert pool[1].key_id == "key_2"
    assert pool[1].secret_key == "key_secret_two"

    assert pool[2].key_id == "key_3"
    assert pool[2].secret_key == "key_secret_three"


def test_key_config_repr_does_not_leak_secret():
    """Ensures string representation of KeyConfig redacts secret keys."""
    key = KeyConfig(key_id="key_1", secret_key="super_secret_value")
    representation = repr(key)

    assert "key_1" in representation
    assert "super_secret_value" not in representation
    assert "[REDACTED]" in representation


def test_cors_origins_parsing():
    """Verifies that comma-separated origins are split into list of clean strings."""
    settings = Settings(ALLOWED_ORIGINS="http://localhost:3000, https://deployed.app")
    origins = settings.cors_origins

    assert len(origins) == 2
    assert "http://localhost:3000" in origins
    assert "https://deployed.app" in origins


def test_empty_keys_handling():
    """Ensures empty LLM_API_KEYS string results in 0 keys without raising errors."""
    settings = Settings(LLM_API_KEYS="")
    assert settings.keys_configured_count == 0
    assert settings.key_pool == []

