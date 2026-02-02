"""Status command for TaxBot CLI."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from ...core.config import get_settings
from ...core.logging import setup_logging
from ...notifications.email_service import EmailService
from ...processors.ollama_processor import OllamaProcessor
from ...storage.csv_repository import CsvRepository

console = Console()


def status() -> None:
    """Show system status."""
    setup_logging()

    console.print("TaxBot System Status", style="bold blue")

    _show_configuration()
    _show_database_status()
    _show_ollama_status()
    _show_email_status()


def _show_configuration() -> None:
    """Display configuration settings."""
    settings = get_settings()
    console.print("\nConfiguration:", style="bold")

    config_table = Table(show_header=True, header_style="bold magenta")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")

    config_table.add_row("API Host", settings.api_host)
    config_table.add_row("API Port", str(settings.api_port))
    config_table.add_row("Data Directory", str(settings.data_dir))
    config_table.add_row("Ollama Model", settings.ollama_model)
    config_table.add_row("Ollama URL", settings.ollama_base_url)
    config_table.add_row(
        "Email Configured", "[green]Yes[/]" if settings.email_sender else "[red]No[/]"
    )

    console.print(config_table)


def _show_database_status() -> None:
    """Display database status."""
    console.print("\nDatabase Status:", style="bold")

    try:
        repository = CsvRepository()
        concept_count = repository.get_concept_count()
        themes = repository.get_themes()

        db_table = Table(show_header=True, header_style="bold magenta")
        db_table.add_column("Metric", style="cyan")
        db_table.add_column("Value", style="green")

        db_table.add_row("Total Concepts", str(concept_count))
        db_table.add_row("Unique Themes", str(len(themes)))
        db_table.add_row("Database File", str(repository.csv_path))

        console.print(db_table)

    except Exception as e:
        console.print(f"Database error: {e}", style="bold red")


def _show_ollama_status() -> None:
    """Display Ollama status."""
    console.print("\nOllama Status:", style="bold")

    try:
        ai_processor = OllamaProcessor()
        if ai_processor.is_available():
            model_info = ai_processor.get_model_info()
            console.print("Ollama is available", style="bold green")
            console.print(
                f"  Model: {model_info.get('current_model', 'Unknown')}"
            )
            console.print(
                f"  Available models: {len(model_info.get('models', []))}"
            )
        else:
            console.print("Ollama is not available", style="bold red")
    except Exception as e:
        console.print(f"Ollama error: {e}", style="bold red")


def _show_email_status() -> None:
    """Display email status."""
    console.print("\nEmail Status:", style="bold")

    try:
        email_service = EmailService()
        if email_service.is_configured():
            console.print("Email is configured", style="bold green")
        else:
            console.print("Email is not configured", style="bold red")
    except Exception as e:
        console.print(f"Email error: {e}", style="bold red")
