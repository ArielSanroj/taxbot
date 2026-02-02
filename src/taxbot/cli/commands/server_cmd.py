"""Server command for TaxBot CLI."""

from __future__ import annotations

import sys

import typer
import uvicorn
from rich.console import Console

from ...core.logging import setup_logging

console = Console()


def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    workers: int = typer.Option(
        1, "--workers", help="Number of worker processes"
    ),
    reload: bool = typer.Option(
        False, "--reload", help="Enable auto-reload for development"
    ),
) -> None:
    """Start the API server."""
    setup_logging()

    console.print(
        f"Starting TaxBot API server on {host}:{port}", style="bold blue"
    )

    try:
        uvicorn.run(
            "taxbot.api.app:app",
            host=host,
            port=port,
            workers=workers if not reload else 1,
            reload=reload,
            log_level="info",
        )
    except KeyboardInterrupt:
        console.print("\nServer stopped by user", style="yellow")
    except Exception as e:
        console.print(f"Server failed to start: {e}", style="bold red")
        sys.exit(1)
