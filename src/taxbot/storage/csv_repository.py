"""CSV-based repository implementation with atomic writes and locking."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

from ..core.config import get_settings
from ..core.logging import get_scraper_logger
from ..models.concept import Concept, ConceptSearchRequest, ConceptSearchResponse
from .csv_query import CsvQuery
from .csv_reader import CsvReader
from .csv_writer import CsvWriter
from .repository import ConceptNotFoundError, Repository, RepositoryError


class CsvRepository(Repository):
    """CSV-based repository with atomic writes and file locking."""

    def __init__(self, csv_path: Optional[Path] = None):
        """Initialize CSV repository."""
        self.settings = get_settings()
        self.logger = get_scraper_logger()
        self.csv_path = csv_path or self.settings.data_dir / "conceptos_dian.csv"

        self._reader = CsvReader(self.csv_path, self.logger)
        self._writer = CsvWriter(self.csv_path, self.logger)
        self._query = CsvQuery(self.logger)

    def save_concept(self, concept: Concept) -> None:
        """Save a single concept."""
        self.save_concepts([concept])

    def save_concepts(self, concepts: List[Concept]) -> None:
        """Save multiple concepts with atomic write."""
        if not concepts:
            return

        self._writer.acquire_lock()
        try:
            df = self._reader.load_dataframe()
            combined_df = self._writer.merge_concepts(df, concepts)
            combined_df = self._writer.prepare_dataframe_for_save(combined_df)
            self._writer.save_dataframe(combined_df)
            self.logger.info(f"Saved {len(concepts)} concepts to CSV")
        finally:
            self._writer.release_lock()

    def get_concept_by_id(self, concept_id: str) -> Optional[Concept]:
        """Get concept by ID (link)."""
        return self._reader.get_concept_by_id(concept_id)

    def get_concepts(
        self,
        limit: int = 10,
        offset: int = 0,
        theme: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Concept]:
        """Get concepts with filtering."""
        df = self._reader.load_dataframe()
        return self._query.get_concepts(
            df, limit, offset, theme, date_from, date_to
        )

    def search_concepts(
        self, request: ConceptSearchRequest
    ) -> ConceptSearchResponse:
        """Search concepts with full-text search."""
        df = self._reader.load_dataframe()
        return self._query.search_concepts(df, request)

    def get_concept_count(self) -> int:
        """Get total number of concepts."""
        return self._reader.get_concept_count()

    def get_themes(self) -> List[str]:
        """Get list of unique themes."""
        return self._reader.get_themes()

    def get_latest_concepts(self, limit: int = 10) -> List[Concept]:
        """Get latest concepts by date."""
        df = self._reader.load_dataframe()
        return self._query.get_latest_concepts(df, limit)

    def concept_exists(self, concept_id: str) -> bool:
        """Check if concept exists."""
        return self._reader.concept_exists(concept_id)

    def delete_concept(self, concept_id: str) -> bool:
        """Delete a concept."""
        self._writer.acquire_lock()
        try:
            df = self._reader.load_dataframe()
            if df.empty or concept_id not in df["link"].values:
                return False

            df_filtered = df[df["link"] != concept_id]
            self._writer.save_dataframe(df_filtered)
            self.logger.info(f"Deleted concept: {concept_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting concept: {e}")
            raise RepositoryError(f"Failed to delete concept: {e}") from e
        finally:
            self._writer.release_lock()

    def clear_all(self) -> None:
        """Clear all concepts."""
        self._writer.acquire_lock()
        try:
            empty_df = pd.DataFrame(columns=self._reader.get_columns())
            self._writer.save_dataframe(empty_df)
            self.logger.info("Cleared all concepts")
        except Exception as e:
            self.logger.error(f"Error clearing concepts: {e}")
            raise RepositoryError(f"Failed to clear concepts: {e}") from e
        finally:
            self._writer.release_lock()

    def backup(self) -> str:
        """Create backup and return backup path."""
        return self._writer.backup()

    def restore(self, backup_path: str) -> None:
        """Restore from backup."""
        self._writer.restore(backup_path)
