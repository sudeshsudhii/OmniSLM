"""omnislm config — Manage OmniSLM configuration."""

from pathlib import Path

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Manage configuration")


@app.command()
def init(
    directory: str = typer.Option(".", "--dir", "-d", help="Output directory"),
) -> None:
    """Generate a default omnislm.yaml configuration file."""
    config_path = Path(directory) / "omnislm.yaml"

    if config_path.exists():
        overwrite = typer.confirm("omnislm.yaml already exists. Overwrite?")
        if not overwrite:
            raise typer.Exit()

    default_config = '''# OmniSLM Configuration
# Docs: https://docs.omnislm.dev/configuration

name: "My OmniSLM App"
version: "0.1.0"
debug: true

runtime:
  default: ollama
  ollama_base_url: http://localhost:11434
  ollama_default_model: "qwen2.5:7b"

auth:
  enabled: true
  provider: jwt
  secret_key: ${JWT_SECRET_KEY:-change-this}

database:
  url: ${DATABASE_URL:-postgresql+asyncpg://omnislm:omnislm@localhost:5432/omnislm}

memory:
  enabled: false
  backend: redis
  redis_url: ${REDIS_URL:-redis://localhost:6379/0}

rag:
  enabled: false
  vector_store: qdrant
  qdrant_url: http://localhost:6333
  embedder: sentence-transformers
  embedder_model: "all-MiniLM-L6-v2"

agents:
  enabled: false
  default_strategy: react
  max_iterations: 10

observability:
  metrics: true
  tracing: false
  log_level: "INFO"
  log_format: "console"

plugins: []
'''
    config_path.write_text(default_config, encoding="utf-8")
    console.print(f"[green]✅ Generated {config_path}[/green]")


@app.command()
def validate(
    config_path: str = typer.Option("omnislm.yaml", "--config", "-c"),
) -> None:
    """Validate an omnislm.yaml configuration file."""
    from omnislm.core.config import OmniSLMConfig

    path = Path(config_path)
    if not path.exists():
        console.print(f"[red]Config file not found: {path}[/red]")
        raise typer.Exit(1)

    try:
        cfg = OmniSLMConfig.from_yaml(path)
        console.print(f"[green]✅ Config is valid![/green]")
        console.print(f"   Name: {cfg.name}")
        console.print(f"   Version: {cfg.version}")
        console.print(f"   Runtime: {cfg.runtime.default}")
    except Exception as e:
        console.print(f"[red]❌ Config validation failed: {e}[/red]")
        raise typer.Exit(1)
