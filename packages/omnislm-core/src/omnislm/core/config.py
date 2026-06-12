"""
OmniSLM Configuration.

Hierarchical configuration system supporting:
- Python dict
- YAML files (omnislm.yaml)
- Environment variables
- Pydantic settings
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeConfig(BaseSettings):
    """Configuration for an LLM runtime."""

    model_config = SettingsConfigDict(extra="allow")

    default: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "qwen2.5:7b"
    vllm_base_url: str = "http://localhost:8000/v1"


class AuthConfig(BaseSettings):
    """Configuration for authentication."""

    model_config = SettingsConfigDict(extra="allow")

    enabled: bool = True
    provider: str = "jwt"
    secret_key: str = "change-this-to-a-random-64-char-string-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7


class DatabaseConfig(BaseSettings):
    """Configuration for database connections."""

    model_config = SettingsConfigDict(extra="allow")

    url: str = "postgresql+asyncpg://omnislm:omnislm@localhost:5432/omnislm"
    pool_size: int = 20
    max_overflow: int = 10


class MemoryConfig(BaseSettings):
    """Configuration for the memory subsystem."""

    model_config = SettingsConfigDict(extra="allow")

    enabled: bool = False
    backend: str = "redis"
    redis_url: str = "redis://localhost:6379/0"


class RAGConfig(BaseSettings):
    """Configuration for the RAG pipeline."""

    model_config = SettingsConfigDict(extra="allow")

    enabled: bool = False
    vector_store: str = "qdrant"
    qdrant_url: str = "http://localhost:6333"
    embedder: str = "sentence-transformers"
    embedder_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200


class AgentConfig(BaseSettings):
    """Configuration for the agent framework."""

    model_config = SettingsConfigDict(extra="allow")

    enabled: bool = False
    default_strategy: str = "react"
    max_iterations: int = 10


class ObservabilityConfig(BaseSettings):
    """Configuration for observability."""

    model_config = SettingsConfigDict(extra="allow")

    metrics: bool = True
    tracing: bool = False
    log_level: str = "INFO"
    log_format: str = "console"  # console | json


class PluginConfig(BaseSettings):
    """Configuration for a single plugin."""

    model_config = SettingsConfigDict(extra="allow")

    name: str
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class OmniSLMConfig(BaseSettings):
    """Root configuration for an OmniSLM application.

    Can be loaded from:
    - A Python dict
    - A YAML file (omnislm.yaml)
    - Environment variables (OMNISLM_ prefix)
    """

    model_config = SettingsConfigDict(
        env_prefix="OMNISLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # ---- Application ----
    name: str = "OmniSLM App"
    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    # ---- Server ----
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"]
    )

    # ---- Subsystems ----
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    plugins: list[PluginConfig] = Field(default_factory=list)

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @classmethod
    def from_yaml(cls, path: str | Path) -> "OmniSLMConfig":
        """Load configuration from a YAML file.

        Args:
            path: Path to the omnislm.yaml file.

        Returns:
            An OmniSLMConfig instance.
        """
        import yaml

        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OmniSLMConfig":
        """Load configuration from a Python dictionary."""
        return cls(**data)
