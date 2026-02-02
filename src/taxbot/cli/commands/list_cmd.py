"""List command for TaxBot CLI."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ...core.logging import setup_logging
from ...storage.csv_repository import CsvRepository

console = Console()


def list_concepts(
    limit: int = typer.Option(
        10, "--limit", help="Maximum number of concepts to show"
    ),
    theme: str = typer.Option(None, "--theme", help="Filter by theme"),
) -> None:
    """List concepts from database."""
    setup_logging()

    console.print("Listing concepts...", style="bold blue")

    try:
        repository = CsvRepository()
        concepts = repository.get_concepts(limit=limit, theme=theme)

        if not concepts:
            console.print("No concepts found", style="yellow")
            return

        _display_concepts_table(concepts)
        console.print(f"\nShowing {len(concepts)} concepts", style="dim")

    except Exception as e:
        console.print(f"Failed to list concepts: {e}", style="bold red")


def _display_concepts_table(concepts) -> None:
    """Display concepts in a formatted table."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Date", style="cyan")
    table.add_column("Theme", style="green")
    table.add_column("Title", style="white")
    table.add_column("Link", style="blue")

    for concept in concepts:
        title = _truncate_text(concept.title, 50)
        link = _truncate_text(concept.link, 30)

        table.add_row(
            concept.date.strftime("%Y-%m-%d"),
            concept.theme,
            title,
            link,
        )

    console.print(table)


def _truncate_text(text: str, max_length: int) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text
