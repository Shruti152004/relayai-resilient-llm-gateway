"""Tests for GET /health endpoint contract compliance."""

from fastapi import status


def test_get_health_contract(client):
    """Verifies that GET /health strictly follows the assignment contract:

    { "status": "ok", "keys_configured": 2, "cache_enabled": true }
    """
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Exact contract assertions
    assert "status" in data
    assert data["status"] == "ok"

    assert "keys_configured" in data
    assert isinstance(data["keys_configured"], int)
    assert data["keys_configured"] >= 2  # At least 2 configured keys in test environment

    assert "cache_enabled" in data
    assert data["cache_enabled"] is True

