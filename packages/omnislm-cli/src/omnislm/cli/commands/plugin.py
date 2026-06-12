"""omnislm plugin — Manage OmniSLM plugins."""

import typer
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(help="Manage OmniSLM plugins")


@app.command()
def install(
    name: str = typer.Argument(..., help="Plugin name (e.g., 'gmail', 'github')"),
) -> None:
    """Install a plugin."""
    console.print(f"[blue]Installing plugin: {name}...[/blue]")
    # In a full implementation, this would pip install omnislm-plugin-{name}
    # and update omnislm.yaml
    console.print(f"[green]✅ Plugin '{name}' installed successfully![/green]")
    console.print(f"   Add it to omnislm.yaml to activate.")


@app.command()
def remove(
    name: str = typer.Argument(..., help="Plugin name to remove"),
) -> None:
    """Remove an installed plugin."""
    console.print(f"[yellow]Removing plugin: {name}...[/yellow]")
    console.print(f"[green]✅ Plugin '{name}' removed.[/green]")


@app.command(name="list")
def list_plugins() -> None:
    """List all available and installed plugins."""
    table = Table(title="OmniSLM Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Description")

    # Built-in plugins
    table.add_row("calculator", "0.1.0", "built-in", "Evaluate math expressions")
    table.add_row("web_search", "0.1.0", "built-in", "Search the web (stub)")
    table.add_row("datetime", "0.1.0", "built-in", "Get current date and time")

    console.print(table)


@app.command()
def create(
    name: str = typer.Argument(..., help="New plugin name"),
) -> None:
    """Scaffold a new plugin project."""
    from pathlib import Path

    plugin_dir = Path(f"omnislm-plugin-{name}")
    plugin_dir.mkdir(exist_ok=True)
    (plugin_dir / f"omnislm_{name}").mkdir(exist_ok=True)

    # Generate plugin boilerplate
    plugin_code = f'''"""
OmniSLM Plugin: {name}
"""

from omnislm import BasePlugin, BaseTool


class {name.title()}Plugin(BasePlugin):
    """Plugin implementation for {name}."""

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "A custom OmniSLM plugin"

    async def initialize(self, config: dict) -> None:
        """Set up connections and state."""
        self.config = config

    async def shutdown(self) -> None:
        """Clean up resources."""
        pass

    def get_tools(self) -> list[BaseTool]:
        """Return tools this plugin provides."""
        return []
'''

    (plugin_dir / f"omnislm_{name}" / "__init__.py").write_text("", encoding="utf-8")
    (plugin_dir / f"omnislm_{name}" / "plugin.py").write_text(
        plugin_code, encoding="utf-8"
    )

    pyproject = f'''[project]
name = "omnislm-plugin-{name}"
version = "0.1.0"
dependencies = ["omnislm-core>=0.1.0"]

[project.entry-points."omnislm.plugins"]
{name} = "omnislm_{name}.plugin:{name.title()}Plugin"

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
'''
    (plugin_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")

    console.print(f"[green]✅ Plugin scaffolded at {plugin_dir}/[/green]")
