"""Data management functions for CSV operations."""

from __future__ import annotations

import logging
from typing import List

import pandas as pd

from .config import CSV_PATH
from .models import Concept


def load_existing_records() -> pd.DataFrame:
    """Load existing records from CSV file."""
    columns = [
        "title", "date", "theme", "descriptor",
        "link", "summary", "analysis"
    ]

    if not CSV_PATH.exists():
        return pd.DataFrame(columns=columns)

    try:
        return pd.read_csv(CSV_PATH)
    except Exception as exc:
        logging.error("No se pudo leer %s: %s", CSV_PATH, exc)
        return pd.DataFrame(columns=columns)


def merge_records(
    existing: pd.DataFrame,
    new_records: List[Concept]
) -> pd.DataFrame:
    """Merge new records with existing data."""
    new_df = pd.DataFrame([concept.to_record() for concept in new_records])

    if existing.empty:
        combined = new_df
    else:
        combined = pd.concat([existing, new_df], ignore_index=True)

    combined.drop_duplicates(subset=["link"], keep="last", inplace=True)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
    combined.sort_values(
        ["theme", "date"], ascending=[True, False], inplace=True
    )
    combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")
    combined.fillna("", inplace=True)

    return combined
