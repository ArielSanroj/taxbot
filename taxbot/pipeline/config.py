"""Pipeline configuration and constants."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import requests

BASE_URL = "https://cijuf.org.co"
LIST_URL = "https://cijuf.org.co/normatividad/conceptos-y-oficios-dian/2025"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CSV_PATH = DATA_DIR / "conceptos_dian.csv"
LOG_PATH = DATA_DIR / "dian_pipeline.log"

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
EMAIL_SENDER = os.getenv("DIAN_EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("DIAN_EMAIL_PASSWORD")
EMAIL_RECIPIENTS = [
    addr.strip()
    for addr in os.getenv("DIAN_EMAIL_RECIPIENTS", "").split(",")
    if addr.strip()
]


def configure_logging() -> None:
    """Configure logging for the pipeline."""
    if logging.getLogger().handlers:
        return
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logging.basicConfig(
        level=logging.INFO, handlers=[file_handler, stream_handler]
    )


configure_logging()

session = requests.Session()
session.headers.update({"User-Agent": "taxbot/1.0"})
