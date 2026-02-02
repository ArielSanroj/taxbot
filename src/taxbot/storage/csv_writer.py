"""CSV writing operations for repository."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

from ..core.logging import get_scraper_logger
from ..models.concept import Concept
from .repository import RepositoryError


class CsvWriter:
    """Handles writing operations to CSV files."""

    def __init__(self, csv_path: Path, logger=None):
        """Initialize CSV writer."""
        self.csv_path = csv_path
        self.lock_path = csv_path.with_suffix(".lock")
        self.logger = logger or get_scraper_logger()

        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

    def acquire_lock(self) -> None:
        """Acquire file lock for atomic operations."""
        if self.lock_path.exists():
            raise RepositoryError("Repository is locked by another process")
        self.lock_path.touch()

    def release_lock(self) -> None:
        """Release file lock."""
        if self.lock_path.exists():
            self.lock_path.unlink()

    def save_dataframe(self, df: pd.DataFrame) -> None:
        """Save dataframe to CSV with atomic write."""
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.csv',
                delete=False,
                dir=self.csv_path.parent
            ) as temp_file:
                df.to_csv(temp_file.name, index=False)
                shutil.move(temp_file.name, self.csv_path)

        except Exception as e:
            self.logger.error(f"Error saving CSV file: {e}")
            raise RepositoryError(f"Failed to save data: {e}") from e

    def prepare_dataframe_for_save(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare dataframe for saving (format dates, fill NaN)."""
        df = df.copy()
        if "date" in df.columns:
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        df = df.fillna("")
        return df

    def merge_concepts(
        self,
        existing_df: pd.DataFrame,
        concepts: List[Concept]
    ) -> pd.DataFrame:
        """Merge new concepts with existing data."""
        new_records = [concept.to_record() for concept in concepts]
        new_df = pd.DataFrame(new_records)

        if existing_df.empty:
            return new_df

        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(
            subset=["link"], keep="last"
        )
        combined_df = combined_df.sort_values(
            ["theme", "date"], ascending=[True, False]
        )

        return combined_df

    def backup(self) -> str:
        """Create backup and return backup path."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"conceptos_dian_backup_{timestamp}.csv"
            backup_path = self.csv_path.parent / backup_name

            shutil.copy2(self.csv_path, backup_path)

            self.logger.info(f"Created backup: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise RepositoryError(f"Failed to create backup: {e}") from e

    def restore(self, backup_path: str) -> None:
        """Restore from backup."""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise RepositoryError(f"Backup file not found: {backup_path}")

            current_backup = self.backup()
            shutil.copy2(backup_file, self.csv_path)

            self.logger.info(f"Restored from backup: {backup_path}")

        except RepositoryError:
            raise
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {e}")
            raise RepositoryError(f"Failed to restore: {e}") from e
