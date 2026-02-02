"""Main pipeline runner."""

from __future__ import annotations

import logging

from .ai_processor import process_concepts
from .config import CSV_PATH
from .data_manager import load_existing_records, merge_records
from .email_notifier import send_email
from .scraper import collect_concepts


def main() -> None:
    """Run the complete DIAN concepts pipeline."""
    scraped = collect_concepts()
    if not scraped:
        logging.info("No se encontraron conceptos para procesar.")
        return

    existing = load_existing_records()
    fresh = _filter_new_concepts(scraped, existing)

    if not fresh:
        logging.info("No hay conceptos nuevos.")
        return

    processed = process_concepts(fresh)
    _save_and_notify(existing, processed)


def _filter_new_concepts(scraped, existing) -> list:
    """Filter out concepts that already exist."""
    existing_links = (
        set(existing["link"].dropna())
        if not existing.empty
        else set()
    )
    return [
        concept for concept in scraped
        if concept.link not in existing_links
    ]


def _save_and_notify(existing, processed) -> None:
    """Save processed concepts and send notification."""
    combined = merge_records(existing, processed)
    combined.to_csv(CSV_PATH, index=False)
    logging.info(
        "Archivo actualizado en %s con %s registros.",
        CSV_PATH,
        len(combined)
    )
    send_email(CSV_PATH, processed)


if __name__ == "__main__":
    main()
