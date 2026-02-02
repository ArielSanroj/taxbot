"""Scrape command for TaxBot CLI."""

from __future__ import annotations

import sys

import typer
from rich.console import Console

from ...core.logging import setup_logging, get_scraper_logger
from ...notifications.email_service import EmailService
from ...processors.ollama_processor import OllamaProcessor
from ...scrapers.dian_scraper import DianScraper
from ...storage.csv_repository import CsvRepository

console = Console()


def scrape(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Run without saving data"
    ),
    notify: bool = typer.Option(
        True, "--notify/--no-notify", help="Send email notifications"
    ),
    process_ai: bool = typer.Option(
        True, "--ai/--no-ai", help="Process with AI analysis"
    ),
) -> None:
    """Scrape DIAN concepts."""
    setup_logging()
    logger = get_scraper_logger()

    try:
        console.print(
            "Starting DIAN concepts scraping...", style="bold blue"
        )

        concepts = _scrape_concepts()
        if not concepts:
            return

        if dry_run:
            _show_dry_run_results(concepts)
            return

        new_concepts = _filter_new_concepts(concepts, logger)
        if not new_concepts:
            return

        new_concepts = _process_with_ai(new_concepts, process_ai)
        _save_concepts(new_concepts)
        _send_notifications(new_concepts, notify)

        console.print("Scraping completed successfully!", style="bold green")

    except KeyboardInterrupt:
        console.print("\nScraping interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"Scraping failed: {e}", style="bold red")
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)


def _scrape_concepts():
    """Execute the scraping process."""
    scraper = DianScraper()
    concepts = scraper.scrape_concepts()

    if not concepts:
        console.print("No concepts found", style="bold red")
        return None

    console.print(f"Found {len(concepts)} concepts", style="bold green")
    return concepts


def _show_dry_run_results(concepts) -> None:
    """Display dry run results."""
    console.print("Dry run mode - not saving data", style="yellow")
    for concept in concepts[:5]:
        console.print(f"  - {concept.title} ({concept.theme})")


def _filter_new_concepts(concepts, logger):
    """Filter out existing concepts."""
    repository = CsvRepository()
    existing_links = set()

    try:
        existing_concepts = repository.get_concepts(limit=10000)
        existing_links = {c.link for c in existing_concepts}
    except Exception as e:
        logger.warning(f"Error getting existing concepts: {e}")

    new_concepts = [c for c in concepts if c.link not in existing_links]

    if not new_concepts:
        console.print("No new concepts to process", style="blue")
        return None

    console.print(
        f"Found {len(new_concepts)} new concepts", style="bold green"
    )
    return new_concepts


def _process_with_ai(concepts, process_ai: bool):
    """Process concepts with AI if enabled."""
    if not process_ai:
        return concepts

    console.print("Processing with AI analysis...", style="bold blue")
    ai_processor = OllamaProcessor()

    if ai_processor.is_available():
        concepts = ai_processor.process_concepts_batch(concepts)
        console.print("AI processing completed", style="bold green")
    else:
        console.print(
            "Ollama not available, skipping AI processing", style="yellow"
        )

    return concepts


def _save_concepts(concepts) -> None:
    """Save concepts to repository."""
    repository = CsvRepository()
    repository.save_concepts(concepts)
    console.print(
        f"Saved {len(concepts)} concepts to database", style="bold green"
    )


def _send_notifications(concepts, notify: bool) -> None:
    """Send email notifications if enabled."""
    if not notify or not concepts:
        return

    console.print("Sending email notifications...", style="bold blue")
    email_service = EmailService()

    if not email_service.is_configured():
        console.print(
            "Email not configured, skipping notifications", style="yellow"
        )
        return

    repository = CsvRepository()
    success = email_service.send_concept_notification(
        concepts, repository.csv_path
    )

    if success:
        console.print("Email notifications sent", style="bold green")
    else:
        console.print("Failed to send email notifications", style="bold red")
