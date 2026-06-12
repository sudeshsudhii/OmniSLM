"""omnislm run — handled by main.py run_server command."""

import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def run() -> None:
    """Alias for the top-level run command."""
    typer.echo("Use: omnislm run-server (or just 'omnislm' at top level)")
