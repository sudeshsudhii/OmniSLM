"""
Unit tests for configuration module.
"""

from src.config.settings import Settings


def test_settings_defaults():
    """Test that default settings are loaded correctly."""
    settings = Settings(
        jwt_secret_key="test-key",
        database_url="postgresql+asyncpg://test:test@localhost/test",
    )
    assert settings.app_name == "OmniSLM"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.port == 8000
    assert settings.rate_limit_per_minute == 60


def test_settings_is_development():
    """Test environment detection."""
    settings = Settings(
        environment="development",
        jwt_secret_key="test",
        database_url="postgresql+asyncpg://test:test@localhost/test",
    )
    assert settings.is_development is True
    assert settings.is_production is False


def test_settings_is_production():
    """Test production environment detection."""
    settings = Settings(
        environment="production",
        jwt_secret_key="test",
        database_url="postgresql+asyncpg://test:test@localhost/test",
    )
    assert settings.is_development is False
    assert settings.is_production is True


def test_settings_log_level_validation():
    """Test log level validation."""
    settings = Settings(
        log_level="debug",
        jwt_secret_key="test",
        database_url="postgresql+asyncpg://test:test@localhost/test",
    )
    assert settings.log_level == "DEBUG"


def test_cors_origins_default():
    """Test default CORS origins."""
    settings = Settings(
        jwt_secret_key="test",
        database_url="postgresql+asyncpg://test:test@localhost/test",
    )
    assert "http://localhost:3000" in settings.cors_origins
    assert "http://localhost:8000" in settings.cors_origins
