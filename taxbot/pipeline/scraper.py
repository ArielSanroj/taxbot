"""Web scraping functions for DIAN concepts."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .config import BASE_URL, LIST_URL, session
from .models import Concept


def clean_text(value: str) -> str:
    """Clean and normalize text."""
    return " ".join(value.replace("\xa0", " ").split())


def fetch_soup(url: str) -> BeautifulSoup:
    """Fetch URL and return BeautifulSoup object."""
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def discover_month_links() -> List[str]:
    """Discover links to monthly concept pages."""
    try:
        soup = fetch_soup(LIST_URL)
    except Exception as exc:
        logging.error("No se pudo obtener el indice %s: %s", LIST_URL, exc)
        return []

    anchors = soup.select("div.view-content a.btn")
    if not anchors:
        return [LIST_URL]

    links = []
    for anchor in anchors:
        href = anchor.get("href")
        if href:
            links.append(urljoin(BASE_URL, href))
    return links


def parse_date(value: str) -> Optional[datetime]:
    """Parse date string to datetime."""
    formats = ("%d/%m/%Y", "%Y-%m-%d")
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def strip_label(text: str, label: str) -> str:
    """Strip label prefix from text."""
    lower = text.lower()
    idx = lower.find(label)
    if idx == -1:
        return clean_text(text)
    remaining = text[idx + len(label):]
    remaining = remaining.lstrip(": ")
    return clean_text(remaining)


def extract_theme_descriptor(cell: BeautifulSoup) -> tuple[str, str]:
    """Extract theme and descriptor from table cell."""
    paragraphs = [
        clean_text(p.get_text(" ", strip=True))
        for p in cell.find_all("p")
        if p.get_text(strip=True)
    ]
    theme = "Sin tema"
    descriptor_parts: List[str] = []

    for text in paragraphs:
        lower = text.lower()
        if "tema" in lower:
            candidate = strip_label(text, "tema")
            if candidate:
                theme = candidate
        elif "descriptor" in lower:
            candidate = strip_label(text, "descriptor")
            if candidate:
                descriptor_parts.append(candidate)
        else:
            descriptor_parts.append(text)

    descriptor = " ".join(part for part in descriptor_parts if part).strip()
    return theme, descriptor


def fetch_full_text(url: str) -> str:
    """Fetch full text content from concept detail page."""
    try:
        soup = fetch_soup(url)
    except Exception as exc:
        logging.error("No se pudo obtener el detalle %s: %s", url, exc)
        return ""

    container = (
        soup.select_one("div.field--name-body")
        or soup.select_one("div.region-content")
    )
    if not container:
        return ""
    return clean_text(container.get_text(" ", strip=True))


def parse_month(url: str) -> List[Concept]:
    """Parse concepts from a monthly page."""
    try:
        soup = fetch_soup(url)
    except Exception as exc:
        logging.error("No se pudo procesar el mes %s: %s", url, exc)
        return []

    rows = soup.select("table.table tbody tr")
    concepts: List[Concept] = []

    for row in rows:
        concept = _parse_row(row)
        if concept:
            concepts.append(concept)

    return concepts


def _parse_row(row) -> Optional[Concept]:
    """Parse a single table row into a Concept."""
    cells = row.find_all("td")
    if len(cells) < 2:
        return None

    anchor = cells[0].find("a")
    if not anchor or not anchor.get("href"):
        return None

    title = clean_text(anchor.get_text(strip=True))
    link = urljoin(BASE_URL, anchor["href"])

    time_elem = cells[0].find("time")
    date_text = clean_text(time_elem.get_text()) if time_elem else ""
    date = parse_date(date_text) or datetime.utcnow()

    theme, descriptor = extract_theme_descriptor(cells[1])
    full_text = fetch_full_text(link)

    return Concept(
        title=title,
        date=date,
        theme=theme,
        descriptor=descriptor,
        link=link,
        full_text=full_text,
    )


def collect_concepts() -> List[Concept]:
    """Collect all concepts from all month pages."""
    months = discover_month_links()
    if not months:
        logging.info("No se encontraron enlaces de meses para procesar.")
        return []

    concepts: List[Concept] = []
    seen_links: set[str] = set()

    for month_url in months:
        for concept in parse_month(month_url):
            if concept.link not in seen_links:
                seen_links.add(concept.link)
                concepts.append(concept)

    return concepts
