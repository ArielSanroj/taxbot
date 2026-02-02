"""CSV reading operations for repository."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd

from ..core.logging import get_scraper_logger
from ..models.concept import Concept
from .repository import RepositoryError


class CsvReader:
    """Handles reading operations from CSV files."""

    def __init__(self, csv_path: Path, logger=None):
        """Initialize CSV reader."""
        self.csv_path = csv_path
        self.logger = logger or get_scraper_logger()

    def get_columns(self) -> List[str]:
        """Return the standard columns for the CSV file."""
        return [
            "title", "date", "theme", "descriptor",
            "link", "summary", "analysis"
        ]

    def load_dataframe(self) -> pd.DataFrame:
        """Load data from CSV file."""
        if not self.csv_path.exists():
            return pd.DataFrame(columns=self.get_columns())

        try:
            df = pd.read_csv(self.csv_path)
            if df.empty:
                return df

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            return df

        except Exception as e:
            self.logger.error(f"Error loading CSV file: {e}")
            raise RepositoryError(f"Failed to load data: {e}") from e

    def get_concept_by_id(self, concept_id: str) -> Optional[Concept]:
        """Get concept by ID (link)."""
        try:
            df = self.load_dataframe()
            if df.empty:
                return None

            concept_row = df[df["link"] == concept_id]
            if concept_row.empty:
                return None

            return Concept.from_record(concept_row.iloc[0].to_dict())

        except Exception as e:
            self.logger.error(f"Error getting concept by ID: {e}")
            raise RepositoryError(f"Failed to get concept: {e}") from e

    def get_concept_count(self) -> int:
        """Get total number of concepts."""
        try:
            df = self.load_dataframe()
            return len(df)
        except Exception as e:
            self.logger.error(f"Error getting concept count: {e}")
            return 0

    def get_themes(self) -> List[str]:
        """Get list of unique themes."""
        try:
            df = self.load_dataframe()
            if df.empty:
                return []

            themes = df["theme"].dropna().unique().tolist()
            return sorted(themes)

        except Exception as e:
            self.logger.error(f"Error getting themes: {e}")
            return []

    def concept_exists(self, concept_id: str) -> bool:
        """Check if concept exists."""
        try:
            df = self.load_dataframe()
            if df.empty:
                return False

            return concept_id in df["link"].values

        except Exception as e:
            self.logger.error(f"Error checking concept existence: {e}")
            return False
