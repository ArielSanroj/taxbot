"""Main pipeline for TaxBot Enterprise with modular components."""

from __future__ import annotations

import fcntl
import signal
import sys
from pathlib import Path
from typing import List, Optional

from .core.config import get_settings
from .core.logging import setup_logging, get_scraper_logger
from .models.concept import Concept
from .notifications.email_service import EmailService
from .processors.ollama_processor import OllamaProcessor
from .scrapers.dian_scraper import DianScraper
from .storage.csv_repository import CsvRepository


class TaxBotPipeline:
    """Main TaxBot pipeline with graceful shutdown and lock file support."""

    def __init__(self):
        """Initialize pipeline."""
        self.settings = get_settings()
        self.logger = get_scraper_logger()
        self.lock_file: Optional[Path] = None
        self._shutdown_requested = False
        
        # Initialize components
        self.scraper = DianScraper()
        self.repository = CsvRepository()
        self.ai_processor = OllamaProcessor()
        self.email_service = EmailService()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._shutdown_requested = True

    def _acquire_lock(self) -> bool:
        """Acquire lock file to prevent concurrent executions."""
        lock_path = self.settings.data_dir / "taxbot.lock"
        
        try:
            # Create lock file
            self.lock_file = lock_path.open("w")
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_file.write(str(Path.cwd()))
            self.lock_file.flush()
            
            self.logger.info("Acquired lock file")
            return True
            
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to acquire lock: {e}")
            return False

    def _release_lock(self) -> None:
        """Release lock file."""
        if self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                if self.lock_file.name and Path(self.lock_file.name).exists():
                    Path(self.lock_file.name).unlink()
                self.logger.info("Released lock file")
            except Exception as e:
                self.logger.warning(f"Error releasing lock: {e}")

    def run(self, dry_run: bool = False, notify: bool = True, process_ai: bool = True) -> bool:
        """Run the complete pipeline."""
        try:
            # Setup logging
            setup_logging()
            self.logger.info("Starting TaxBot pipeline")
            
            # Acquire lock
            if not self._acquire_lock():
                self.logger.error("Another instance is already running")
                return False
            
            # Check for shutdown
            if self._shutdown_requested:
                self.logger.info("Shutdown requested before processing")
                return False
            
            # Step 1: Scrape concepts
            self.logger.info("Step 1: Scraping concepts")
            concepts = self._scrape_concepts()
            
            if not concepts:
                self.logger.warning("No concepts found during scraping")
                return True
            
            self.logger.info(f"Scraped {len(concepts)} concepts")
            
            # Check for shutdown
            if self._shutdown_requested:
                self.logger.info("Shutdown requested after scraping")
                return False
            
            # Step 2: Filter new concepts
            self.logger.info("Step 2: Filtering new concepts")
            new_concepts = self._filter_new_concepts(concepts)
            
            if not new_concepts:
                self.logger.info("No new concepts to process")
                return True
            
            self.logger.info(f"Found {len(new_concepts)} new concepts")
            
            # Check for shutdown
            if self._shutdown_requested:
                self.logger.info("Shutdown requested after filtering")
                return False
            
            # Step 3: Process with AI (if enabled and available)
            if process_ai and not dry_run:
                self.logger.info("Step 3: Processing with AI")
                new_concepts = self._process_with_ai(new_concepts)
            
            # Check for shutdown
            if self._shutdown_requested:
                self.logger.info("Shutdown requested after AI processing")
                return False
            
            # Step 4: Save concepts (if not dry run)
            if not dry_run:
                self.logger.info("Step 4: Saving concepts")
                self._save_concepts(new_concepts)
            
            # Check for shutdown
            if self._shutdown_requested:
                self.logger.info("Shutdown requested after saving")
                return False
            
            # Step 5: Send notifications (if enabled and not dry run)
            if notify and not dry_run and new_concepts:
                self.logger.info("Step 5: Sending notifications")
                self._send_notifications(new_concepts)
            
            self.logger.info("Pipeline completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False
            
        finally:
            self._release_lock()

    def _scrape_concepts(self) -> List[Concept]:
        """Scrape concepts from DIAN."""
        try:
            return self.scraper.scrape_concepts()
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            raise

    def _filter_new_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """Filter out concepts that already exist."""
        try:
            # Get existing concepts
            existing_links = set()
            try:
                existing_concepts = self.repository.get_concepts(limit=10000)
                existing_links = {c.link for c in existing_concepts}
            except Exception as e:
                self.logger.warning(f"Error getting existing concepts: {e}")
            
            # Filter new concepts
            new_concepts = [c for c in concepts if c.link not in existing_links]
            
            self.logger.info(f"Filtered {len(new_concepts)} new concepts from {len(concepts)} total")
            return new_concepts
            
        except Exception as e:
            self.logger.error(f"Error filtering concepts: {e}")
            raise

    def _process_with_ai(self, concepts: List[Concept]) -> List[Concept]:
        """Process concepts with AI analysis."""
        try:
            if not self.ai_processor.is_available():
                self.logger.warning("Ollama not available, skipping AI processing")
                return concepts
            
            self.logger.info(f"Processing {len(concepts)} concepts with AI")
            processed_concepts = self.ai_processor.process_concepts_batch(concepts)
            
            self.logger.info("AI processing completed")
            return processed_concepts
            
        except Exception as e:
            self.logger.error(f"AI processing failed: {e}")
            # Return original concepts without AI processing
            return concepts

    def _save_concepts(self, concepts: List[Concept]) -> None:
        """Save concepts to repository."""
        try:
            self.repository.save_concepts(concepts)
            self.logger.info(f"Saved {len(concepts)} concepts to repository")
        except Exception as e:
            self.logger.error(f"Failed to save concepts: {e}")
            raise

    def _send_notifications(self, concepts: List[Concept]) -> None:
        """Send email notifications."""
        try:
            if not self.email_service.is_configured():
                self.logger.warning("Email not configured, skipping notifications")
                return
            
            csv_path = self.repository.csv_path
            success = self.email_service.send_concept_notification(concepts, csv_path)
            
            if success:
                self.logger.info("Email notifications sent successfully")
            else:
                self.logger.error("Failed to send email notifications")
                
        except Exception as e:
            self.logger.error(f"Notification failed: {e}")

    def get_status(self) -> dict:
        """Get pipeline status."""
        try:
            return {
                "is_running": self.lock_file is not None,
                "total_concepts": self.repository.get_concept_count(),
                "ollama_available": self.ai_processor.is_available(),
                "email_configured": self.email_service.is_configured(),
                "data_directory": str(self.settings.data_dir),
            }
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {"error": str(e)}


def main():
    """Main entry point for the pipeline."""
    pipeline = TaxBotPipeline()
    
    try:
        success = pipeline.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
