"""Base scraper interface and common functionality."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import List, Protocol

from ..core.config import get_settings
from ..core.logging import get_scraper_logger
from ..models.concept import Concept


class ScraperError(Exception):
    """Base exception for scraper errors."""

    pass


class NetworkError(ScraperError):
    """Network-related scraper errors."""

    pass


class ParseError(ScraperError):
    """HTML parsing errors."""

    pass


class RateLimitError(ScraperError):
    """Rate limiting errors."""

    pass


class BaseScraper(ABC):
    """Abstract base class for scrapers."""

    def __init__(self):
        """Initialize scraper with configuration."""
        self.settings = get_settings()
        self.logger = get_scraper_logger()
        self._session = None

    @abstractmethod
    def scrape_concepts(self) -> List[Concept]:
        """Scrape concepts from the source."""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of the data source."""
        pass

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self.settings.scraper_delay > 0:
            time.sleep(self.settings.scraper_delay)

    def _validate_concept(self, concept: Concept) -> bool:
        """Validate scraped concept data."""
        if not concept.title or not concept.link:
            self.logger.warning("Invalid concept: missing title or link")
            return False
        
        if not concept.date:
            self.logger.warning("Invalid concept: missing date")
            return False
        
        return True

    def _clean_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """Clean and validate scraped concepts."""
        valid_concepts = []
        
        for concept in concepts:
            if self._validate_concept(concept):
                valid_concepts.append(concept)
            else:
                self.logger.warning(f"Skipping invalid concept: {concept.title}")
        
        self.logger.info(f"Scraped {len(valid_concepts)} valid concepts from {len(concepts)} total")
        return valid_concepts


class ScraperProtocol(Protocol):
    """Protocol for scraper implementations."""

    def scrape_concepts(self) -> List[Concept]:
        """Scrape concepts from the source."""
        ...

    def get_source_name(self) -> str:
        """Get the name of the data source."""
        ...
