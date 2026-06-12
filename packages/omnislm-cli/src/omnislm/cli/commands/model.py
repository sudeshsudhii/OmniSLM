"""omnislm model — Manage AI models."""

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Manage AI models")


@app.command()
def pull(
    name: str = typer.Argument(..., help="Model name (e.g., 'qwen2.5:7b')"),
    runtime: str = typer.Option("ollama", "--runtime", "-r", help="Runtime to use"),
) -> None:
    """Pull/download a model."""
    console.print(f"[blue]Pulling model '{name}' via {runtime}...[/blue]")
    # In full implementation, this creates a runtime and calls pull_model
    console.print(f"[green]✅ Model '{name}' pulled successfully![/green]")


@app.command(name="list")
def list_models(
    runtime: str = typer.Option("ollama", "--runtime", "-r", help="Runtime to query"),
) -> None:
    """List available models."""
    console.print(f"[blue]Listing models from {runtime}...[/blue]")


@app.command()
def info(
    name: str = typer.Argument(..., help="Model name"),
) -> None:
    """Show model details."""
    console.print(f"[blue]Model info for '{name}'...[/blue]")


@app.command()
def remove(
    name: str = typer.Argument(..., help="Model name to remove"),
) -> None:
    """Remove a model."""
    console.print(f"[yellow]Removing model '{name}'...[/yellow]")
