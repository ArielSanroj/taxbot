"""DIAN Pipeline - Modular scraping and processing pipeline."""

from .config import (
    BASE_URL,
    CSV_PATH,
    DATA_DIR,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENTS,
    EMAIL_SENDER,
    LIST_URL,
    LOG_PATH,
    OLLAMA_MODEL,
    configure_logging,
    session,
)
from .models import Concept
from .scraper import (
    clean_text,
    collect_concepts,
    discover_month_links,
    extract_theme_descriptor,
    fetch_full_text,
    fetch_soup,
    parse_date,
    parse_month,
    strip_label,
)
from .ai_processor import (
    complementary_analysis,
    process_concepts,
    summarize_text,
)
from .data_manager import (
    load_existing_records,
    merge_records,
)
from .email_notifier import send_email
from .runner import main

__all__ = [
    # Config
    "BASE_URL",
    "CSV_PATH",
    "DATA_DIR",
    "EMAIL_PASSWORD",
    "EMAIL_RECIPIENTS",
    "EMAIL_SENDER",
    "LIST_URL",
    "LOG_PATH",
    "OLLAMA_MODEL",
    "configure_logging",
    "session",
    # Models
    "Concept",
    # Scraper
    "clean_text",
    "collect_concepts",
    "discover_month_links",
    "extract_theme_descriptor",
    "fetch_full_text",
    "fetch_soup",
    "parse_date",
    "parse_month",
    "strip_label",
    # AI Processor
    "complementary_analysis",
    "process_concepts",
    "summarize_text",
    # Data Manager
    "load_existing_records",
    "merge_records",
    # Email
    "send_email",
    # Runner
    "main",
]
