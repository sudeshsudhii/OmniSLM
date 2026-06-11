"""
OmniSLM Test Configuration.

Pytest fixtures for testing.
"""

import pytest


@pytest.fixture
def app_settings():
    """Override settings for testing."""
    from src.config.settings import Settings

    return Settings(
        environment="testing",
        debug=True,
        database_url="postgresql+asyncpg://omnislm:omnislm@localhost:5432/omnislm_test",
        redis_url="redis://localhost:6379/1",
        jwt_secret_key="test-secret-key-not-for-production",
    )
