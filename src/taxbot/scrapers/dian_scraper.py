"""DIAN concepts scraper with retry logic and rate limiting."""

from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..core.config import get_settings
from ..core.logging import get_scraper_logger
from ..models.concept import Concept
from .base import BaseScraper, NetworkError, ParseError, RateLimitError, ScraperError


class DianScraper(BaseScraper):
    """DIAN concepts scraper with enhanced error handling."""

    BASE_URL = "https://cijuf.org.co"
    LIST_URL = "https://cijuf.org.co/normatividad/conceptos-y-oficios-dian/2025"
    
    def __init__(self):
        """Initialize DIAN scraper."""
        super().__init__()
        self._session = None
        self._seen_links: Set[str] = set()

    def get_source_name(self) -> str:
        """Get the name of the data source."""
        return "DIAN Concepts"

    def scrape_concepts(self) -> List[Concept]:
        """Scrape DIAN concepts with retry logic."""
        self.logger.info("Starting DIAN concepts scraping")
        
        try:
            # Discover month links
            month_links = self._discover_month_links()
            if not month_links:
                self.logger.warning("No month links found")
                return []

            # Scrape concepts from each month
            all_concepts = []
            for month_url in month_links:
                try:
                    concepts = self._parse_month(month_url)
                    all_concepts.extend(concepts)
                    self._apply_rate_limit()
                except Exception as e:
                    self.logger.error(f"Error scraping month {month_url}: {e}")
                    continue

            # Clean and validate concepts
            valid_concepts = self._clean_concepts(all_concepts)
            
            self.logger.info(f"Successfully scraped {len(valid_concepts)} concepts")
            return valid_concepts

        except Exception as e:
            self.logger.error(f"Failed to scrape DIAN concepts: {e}")
            raise ScraperError(f"Scraping failed: {e}") from e

    @retry(
        retry=retry_if_exception_type((requests.RequestException, NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _fetch_soup(self, url: str) -> BeautifulSoup:
        """Fetch and parse HTML with retry logic."""
        if not self._session:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "TaxBot/1.0 (Enterprise DIAN Scraper)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            })

        try:
            response = self._session.get(
                url,
                timeout=self.settings.scraper_timeout,
                allow_redirects=True,
            )
            response.raise_for_status()
            
            # Check for rate limiting
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", 60))
                self.logger.warning(f"Rate limited, waiting {wait_time} seconds")
                time.sleep(wait_time)
                raise RateLimitError("Rate limited by server")
            
            return BeautifulSoup(response.text, "html.parser")
            
        except requests.Timeout:
            raise NetworkError(f"Request timeout for {url}")
        except requests.ConnectionError:
            raise NetworkError(f"Connection error for {url}")
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limited: {e}")
            raise NetworkError(f"HTTP error {e.response.status_code} for {url}")

    def _discover_month_links(self) -> List[str]:
        """Discover month links from the main page."""
        try:
            soup = self._fetch_soup(self.LIST_URL)
        except Exception as e:
            self.logger.error(f"Failed to fetch main page: {e}")
            return [self.LIST_URL]  # Fallback to main URL

        anchors = soup.select("div.view-content a.btn")
        if not anchors:
            self.logger.warning("No month links found, using main URL")
            return [self.LIST_URL]

        links = []
        for anchor in anchors:
            href = anchor.get("href")
            if href:
                full_url = urljoin(self.BASE_URL, href)
                links.append(full_url)

        self.logger.info(f"Found {len(links)} month links")
        return links

    def _parse_month(self, url: str) -> List[Concept]:
        """Parse concepts from a month page."""
        try:
            soup = self._fetch_soup(url)
        except Exception as e:
            self.logger.error(f"Failed to parse month {url}: {e}")
            return []

        rows = soup.select("table.table tbody tr")
        concepts = []

        for row in rows:
            try:
                concept = self._parse_concept_row(row)
                if concept and concept.link not in self._seen_links:
                    self._seen_links.add(concept.link)
                    concepts.append(concept)
            except Exception as e:
                self.logger.warning(f"Failed to parse concept row: {e}")
                continue

        self.logger.info(f"Parsed {len(concepts)} concepts from {url}")
        return concepts

    def _parse_concept_row(self, row) -> Optional[Concept]:
        """Parse a single concept row."""
        cells = row.find_all("td")
        if len(cells) < 2:
            return None

        # Extract title and link
        anchor = cells[0].find("a")
        if not anchor or not anchor.get("href"):
            return None

        title = self._clean_text(anchor.get_text(strip=True))
        link = urljoin(self.BASE_URL, anchor["href"])

        # Extract date
        date_text = ""
        time_tag = cells[0].find("time")
        if time_tag:
            date_text = self._clean_text(time_tag.get_text())
        
        date = self._parse_date(date_text) or datetime.utcnow()

        # Extract theme and descriptor
        theme, descriptor = self._extract_theme_descriptor(cells[1])

        # Fetch full text
        full_text = self._fetch_full_text(link)

        return Concept(
            title=title,
            date=date,
            theme=theme,
            descriptor=descriptor,
            link=link,
            full_text=full_text,
        )

    def _clean_text(self, text: str) -> str:
        """Clean text content."""
        if not text:
            return ""
        return " ".join(text.replace("\xa0", " ").split())

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from text."""
        if not date_text:
            return None

        formats = ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y")
        for fmt in formats:
            try:
                return datetime.strptime(date_text.strip(), fmt)
            except ValueError:
                continue
        return None

    def _extract_theme_descriptor(self, cell) -> tuple[str, str]:
        """Extract theme and descriptor from cell."""
        paragraphs = [
            self._clean_text(p.get_text(" ", strip=True))
            for p in cell.find_all("p")
            if p.get_text(strip=True)
        ]

        theme = "Sin tema"
        descriptor_parts = []

        for text in paragraphs:
            lower = text.lower()
            if "tema" in lower:
                candidate = self._strip_label(text, "tema")
                if candidate:
                    theme = candidate
            elif "descriptor" in lower:
                candidate = self._strip_label(text, "descriptor")
                if candidate:
                    descriptor_parts.append(candidate)
            else:
                descriptor_parts.append(text)

        descriptor = " ".join(part for part in descriptor_parts if part).strip()
        return theme, descriptor

    def _strip_label(self, text: str, label: str) -> str:
        """Strip label from text."""
        lower = text.lower()
        idx = lower.find(label)
        if idx == -1:
            return self._clean_text(text)
        
        remaining = text[idx + len(label):]
        remaining = remaining.lstrip(": ")
        return self._clean_text(remaining)

    def _fetch_full_text(self, url: str) -> str:
        """Fetch full text content from concept URL."""
        try:
            soup = self._fetch_soup(url)
        except Exception as e:
            self.logger.warning(f"Failed to fetch full text from {url}: {e}")
            return ""

        # Try multiple selectors for content
        selectors = [
            "div.field--name-body",
            "div.region-content",
            "div.content",
            "main",
            "article",
        ]

        for selector in selectors:
            container = soup.select_one(selector)
            if container:
                text = self._clean_text(container.get_text(" ", strip=True))
                if text and len(text) > 100:  # Ensure we have substantial content
                    return text

        return ""

    def __del__(self):
        """Clean up session on destruction."""
        if self._session:
            self._session.close()
