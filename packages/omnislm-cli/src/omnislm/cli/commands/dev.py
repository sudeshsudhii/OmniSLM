"""omnislm dev — Developer tools."""

import shutil
import sys

import typer
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(help="Developer tools")


@app.command()
def doctor() -> None:
    """Check system requirements for OmniSLM."""
    table = Table(title="OmniSLM System Check")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)
    table.add_row(
        "Python",
        "✅" if py_ok else "❌",
        f"v{py_version} {'(3.11+ required)' if not py_ok else ''}",
    )

    # Docker
    docker_ok = shutil.which("docker") is not None
    table.add_row("Docker", "✅" if docker_ok else "⚠️", "Found" if docker_ok else "Not found (optional)")

    # Ollama
    ollama_ok = shutil.which("ollama") is not None
    table.add_row("Ollama", "✅" if ollama_ok else "⚠️", "Found" if ollama_ok else "Not found (optional)")

    # Key packages
    packages = ["fastapi", "pydantic", "httpx", "structlog"]
    for pkg in packages:
        try:
            mod = __import__(pkg)
            version = getattr(mod, "__version__", "installed")
            table.add_row(pkg, "✅", f"v{version}")
        except ImportError:
            table.add_row(pkg, "❌", "Not installed")

    console.print(table)


@app.command()
def inspect() -> None:
    """Show registered runtimes, plugins, and tools."""
    console.print("[bold]OmniSLM Inspection[/bold]")
    console.print("  Run this within a project to see registered components.")


@app.command()
def shell() -> None:
    """Open an interactive Python shell with OmniSLM context."""
    import code

    banner = "OmniSLM Interactive Shell\nType 'exit()' to quit.\n"
    try:
        from omnislm import OmniSLM

        local_vars = {"OmniSLM": OmniSLM}
        code.interact(banner=banner, local=local_vars)
    except ImportError:
        console.print("[red]omnislm not installed in this environment[/red]")
