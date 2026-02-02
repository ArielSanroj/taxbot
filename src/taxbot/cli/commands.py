"""CLI commands for TaxBot.

This module maintains backwards compatibility by registering all commands
from the modular command files.

For new commands, create a new file in cli/commands/ directory.
"""

from __future__ import annotations

import typer

from .commands import (
    list_concepts,
    scrape,
    serve,
    status,
    test_email,
    test_ollama,
)

app = typer.Typer(
    name="taxbot",
    help="TaxBot Enterprise - DIAN concepts scraper and analyzer",
    add_completion=False,
)

# Register commands from modular files
app.command()(scrape)
app.command()(serve)
app.command()(status)
app.command(name="test-email")(test_email)
app.command(name="test-ollama")(test_ollama)
app.command(name="list")(list_concepts)


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
