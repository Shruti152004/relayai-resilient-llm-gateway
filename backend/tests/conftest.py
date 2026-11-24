"""Shared Pytest Test Configuration and Fixtures."""

import glob
import os
import pytest
from fastapi.testclient import TestClient

# Ensure test environment variables are loaded prior to app initialization
TEST_DB_FILE = "./test_app.db"
os.environ["LLM_API_KEYS"] = "test_mock_key_alpha,test_mock_key_beta"
os.environ["LLM_MODEL"] = "gemini/gemini-2.0-flash"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"
os.environ["ENABLE_FAILURE_SIMULATION"] = "true"

from app.main import app
from app.config import Settings
from app.db.database import init_db


@pytest.fixture(scope="session", autouse=True)
def clean_test_database():
    """Removes any temporary test database files before and after the test session."""
    def _cleanup():
        for f in glob.glob(f"{TEST_DB_FILE}*"):
            try:
                os.remove(f)
            except OSError:
                pass

    _cleanup()
    yield
    _cleanup()


@pytest.fixture
def client():
    """Provides a synchronous FastAPI TestClient for endpoint testing."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def custom_settings():
    """Provides a factory to instantiate test settings with custom env mappings."""
    def _create(**kwargs):
        return Settings(**kwargs)
    return _create
