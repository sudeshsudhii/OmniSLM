"""
OmniSLM CLI — Command-line interface for the OmniSLM framework.

Commands:
    omnislm create <template>    Scaffold a new project
    omnislm run                  Start the app server
    omnislm plugin install       Install a plugin
    omnislm model pull           Pull a model
    omnislm config init          Generate configuration
    omnislm dev doctor           Check system requirements
"""

import typer
from rich.console import Console

from omnislm.cli.commands import create, run, plugin, model, config, dev

console = Console()

app = typer.Typer(
    name="omnislm",
    help="🚀 OmniSLM — The open-source AI framework for Small Language Models",
    add_completion=True,
    rich_markup_mode="rich",
)

app.add_typer(create.app, name="create", help="Scaffold a new OmniSLM project")
app.add_typer(plugin.app, name="plugin", help="Manage plugins")
app.add_typer(model.app, name="model", help="Manage AI models")
app.add_typer(config.app, name="config", help="Manage configuration")
app.add_typer(dev.app, name="dev", help="Developer tools")


@app.command()
def run_server(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of workers"),
    config_path: str = typer.Option(
        "omnislm.yaml", "--config", "-c", help="Config file path"
    ),
) -> None:
    """Start the OmniSLM application server."""
    from pathlib import Path

    config_file = Path(config_path)

    if config_file.exists():
        console.print(f"[green]Loading config from {config_file}[/green]")
        from omnislm import OmniSLM

        omnislm_app = OmniSLM.from_config(config_file)
    else:
        console.print("[yellow]No config file found, using defaults[/yellow]")
        from omnislm import OmniSLM

        omnislm_app = OmniSLM(debug=True)

    console.print(
        f"\n[bold blue]🚀 OmniSLM[/bold blue] v{omnislm_app.config.version}"
    )
    console.print(f"   Server: http://{host}:{port}")
    console.print(f"   Docs:   http://{host}:{port}/docs\n")

    omnislm_app.run(host=host, port=port, reload=reload, workers=workers)


@app.command()
def version() -> None:
    """Show the OmniSLM version."""
    console.print("[bold blue]OmniSLM[/bold blue] v0.1.0")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
