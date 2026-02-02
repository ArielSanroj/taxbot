"""Test commands for TaxBot CLI."""

from __future__ import annotations

from rich.console import Console

from ...core.logging import setup_logging
from ...notifications.email_service import EmailService
from ...processors.ollama_processor import OllamaProcessor

console = Console()


def test_email() -> None:
    """Test email configuration."""
    setup_logging()

    console.print("Testing email configuration...", style="bold blue")

    try:
        email_service = EmailService()

        if not email_service.is_configured():
            console.print("Email not configured", style="bold red")
            return

        success = email_service.send_test_email()

        if success:
            console.print("Test email sent successfully", style="bold green")
        else:
            console.print("Failed to send test email", style="bold red")

    except Exception as e:
        console.print(f"Email test failed: {e}", style="bold red")


def test_ollama() -> None:
    """Test Ollama connection."""
    setup_logging()

    console.print("Testing Ollama connection...", style="bold blue")

    try:
        ai_processor = OllamaProcessor()
        result = ai_processor.test_connection()

        if result["status"] == "success":
            console.print("Ollama connection successful", style="bold green")
            console.print(f"  {result['details']}")
        else:
            console.print("Ollama connection failed", style="bold red")
            console.print(f"  {result['details']}")

    except Exception as e:
        console.print(f"Ollama test failed: {e}", style="bold red")
