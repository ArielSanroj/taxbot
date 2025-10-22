"""CLI commands for TaxBot."""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from ..core.config import get_settings
from ..core.logging import setup_logging, get_scraper_logger
from ..notifications.email_service import EmailService
from ..processors.ollama_processor import OllamaProcessor
from ..scrapers.dian_scraper import DianScraper
from ..storage.csv_repository import CsvRepository

app = typer.Typer(
    name="taxbot",
    help="TaxBot Enterprise - DIAN concepts scraper and analyzer",
    add_completion=False,
)
console = Console()


@app.command()
def scrape(
    dry_run: bool = typer.Option(False, "--dry-run", help="Run without saving data"),
    notify: bool = typer.Option(True, "--notify/--no-notify", help="Send email notifications"),
    process_ai: bool = typer.Option(True, "--ai/--no-ai", help="Process with AI analysis"),
):
    """Scrape DIAN concepts."""
    setup_logging()
    logger = get_scraper_logger()
    
    try:
        console.print("🔍 Starting DIAN concepts scraping...", style="bold blue")
        
        # Initialize components
        scraper = DianScraper()
        repository = CsvRepository()
        
        # Scrape concepts
        concepts = scraper.scrape_concepts()
        
        if not concepts:
            console.print("❌ No concepts found", style="bold red")
            return
        
        console.print(f"✅ Found {len(concepts)} concepts", style="bold green")
        
        if dry_run:
            console.print("🔍 Dry run mode - not saving data", style="yellow")
            for concept in concepts[:5]:  # Show first 5
                console.print(f"  • {concept.title} ({concept.theme})")
            return
        
        # Filter new concepts
        existing_links = set()
        try:
            existing_concepts = repository.get_concepts(limit=10000)
            existing_links = {c.link for c in existing_concepts}
        except Exception as e:
            logger.warning(f"Error getting existing concepts: {e}")
        
        new_concepts = [c for c in concepts if c.link not in existing_links]
        
        if not new_concepts:
            console.print("ℹ️ No new concepts to process", style="blue")
            return
        
        console.print(f"🆕 Found {len(new_concepts)} new concepts", style="bold green")
        
        # Process with AI if enabled
        if process_ai:
            console.print("🤖 Processing with AI analysis...", style="bold blue")
            ai_processor = OllamaProcessor()
            
            if ai_processor.is_available():
                new_concepts = ai_processor.process_concepts_batch(new_concepts)
                console.print("✅ AI processing completed", style="bold green")
            else:
                console.print("⚠️ Ollama not available, skipping AI processing", style="yellow")
        
        # Save concepts
        repository.save_concepts(new_concepts)
        console.print(f"💾 Saved {len(new_concepts)} concepts to database", style="bold green")
        
        # Send notifications
        if notify and new_concepts:
            console.print("📧 Sending email notifications...", style="bold blue")
            email_service = EmailService()
            
            if email_service.is_configured():
                csv_path = repository.csv_path
                success = email_service.send_concept_notification(new_concepts, csv_path)
                
                if success:
                    console.print("✅ Email notifications sent", style="bold green")
                else:
                    console.print("❌ Failed to send email notifications", style="bold red")
            else:
                console.print("⚠️ Email not configured, skipping notifications", style="yellow")
        
        console.print("🎉 Scraping completed successfully!", style="bold green")
        
    except KeyboardInterrupt:
        console.print("\n⏹️ Scraping interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Scraping failed: {e}", style="bold red")
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    workers: int = typer.Option(1, "--workers", help="Number of worker processes"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
):
    """Start the API server."""
    setup_logging()
    
    console.print(f"🚀 Starting TaxBot API server on {host}:{port}", style="bold blue")
    
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
        console.print("\n⏹️ Server stopped by user", style="yellow")
    except Exception as e:
        console.print(f"❌ Server failed to start: {e}", style="bold red")
        sys.exit(1)


@app.command()
def status():
    """Show system status."""
    setup_logging()
    
    console.print("📊 TaxBot System Status", style="bold blue")
    
    # Check configuration
    settings = get_settings()
    console.print("\n🔧 Configuration:", style="bold")
    
    config_table = Table(show_header=True, header_style="bold magenta")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("API Host", settings.api_host)
    config_table.add_row("API Port", str(settings.api_port))
    config_table.add_row("Data Directory", str(settings.data_dir))
    config_table.add_row("Ollama Model", settings.ollama_model)
    config_table.add_row("Ollama URL", settings.ollama_base_url)
    config_table.add_row("Email Configured", "✅" if settings.email_sender else "❌")
    
    console.print(config_table)
    
    # Check repository
    console.print("\n💾 Database Status:", style="bold")
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
        console.print(f"❌ Database error: {e}", style="bold red")
    
    # Check Ollama
    console.print("\n🤖 Ollama Status:", style="bold")
    try:
        ai_processor = OllamaProcessor()
        if ai_processor.is_available():
            model_info = ai_processor.get_model_info()
            console.print("✅ Ollama is available", style="bold green")
            console.print(f"  Model: {model_info.get('current_model', 'Unknown')}")
            console.print(f"  Available models: {len(model_info.get('models', []))}")
        else:
            console.print("❌ Ollama is not available", style="bold red")
    except Exception as e:
        console.print(f"❌ Ollama error: {e}", style="bold red")
    
    # Check email
    console.print("\n📧 Email Status:", style="bold")
    try:
        email_service = EmailService()
        if email_service.is_configured():
            console.print("✅ Email is configured", style="bold green")
        else:
            console.print("❌ Email is not configured", style="bold red")
    except Exception as e:
        console.print(f"❌ Email error: {e}", style="bold red")


@app.command()
def test_email():
    """Test email configuration."""
    setup_logging()
    
    console.print("📧 Testing email configuration...", style="bold blue")
    
    try:
        email_service = EmailService()
        
        if not email_service.is_configured():
            console.print("❌ Email not configured", style="bold red")
            return
        
        success = email_service.send_test_email()
        
        if success:
            console.print("✅ Test email sent successfully", style="bold green")
        else:
            console.print("❌ Failed to send test email", style="bold red")
            
    except Exception as e:
        console.print(f"❌ Email test failed: {e}", style="bold red")


@app.command()
def test_ollama():
    """Test Ollama connection."""
    setup_logging()
    
    console.print("🤖 Testing Ollama connection...", style="bold blue")
    
    try:
        ai_processor = OllamaProcessor()
        result = ai_processor.test_connection()
        
        if result["status"] == "success":
            console.print("✅ Ollama connection successful", style="bold green")
            console.print(f"  {result['details']}")
        else:
            console.print("❌ Ollama connection failed", style="bold red")
            console.print(f"  {result['details']}")
            
    except Exception as e:
        console.print(f"❌ Ollama test failed: {e}", style="bold red")


@app.command()
def list_concepts(
    limit: int = typer.Option(10, "--limit", help="Maximum number of concepts to show"),
    theme: str = typer.Option(None, "--theme", help="Filter by theme"),
):
    """List concepts from database."""
    setup_logging()
    
    console.print("📋 Listing concepts...", style="bold blue")
    
    try:
        repository = CsvRepository()
        concepts = repository.get_concepts(limit=limit, theme=theme)
        
        if not concepts:
            console.print("No concepts found", style="yellow")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Date", style="cyan")
        table.add_column("Theme", style="green")
        table.add_column("Title", style="white")
        table.add_column("Link", style="blue")
        
        for concept in concepts:
            table.add_row(
                concept.date.strftime("%Y-%m-%d"),
                concept.theme,
                concept.title[:50] + "..." if len(concept.title) > 50 else concept.title,
                concept.link[:30] + "..." if len(concept.link) > 30 else concept.link,
            )
        
        console.print(table)
        console.print(f"\nShowing {len(concepts)} concepts", style="dim")
        
    except Exception as e:
        console.print(f"❌ Failed to list concepts: {e}", style="bold red")


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
