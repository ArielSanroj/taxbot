"""CSV-based repository implementation with atomic writes and locking."""

from __future__ import annotations

import fcntl
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

from ..core.config import get_settings
from ..core.logging import get_scraper_logger
from ..models.concept import Concept, ConceptSearchRequest, ConceptSearchResponse
from .repository import ConceptNotFoundError, Repository, RepositoryError


class CsvRepository(Repository):
    """CSV-based repository with atomic writes and file locking."""

    def __init__(self, csv_path: Optional[Path] = None):
        """Initialize CSV repository."""
        self.settings = get_settings()
        self.logger = get_scraper_logger()
        self.csv_path = csv_path or self.settings.data_dir / "conceptos_dian.csv"
        self.lock_path = self.csv_path.with_suffix(".lock")
        
        # Ensure data directory exists
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

    def _acquire_lock(self) -> None:
        """Acquire file lock for atomic operations."""
        if self.lock_path.exists():
            raise RepositoryError("Repository is locked by another process")
        
        self.lock_path.touch()

    def _release_lock(self) -> None:
        """Release file lock."""
        if self.lock_path.exists():
            self.lock_path.unlink()

    def _load_dataframe(self) -> pd.DataFrame:
        """Load data from CSV file."""
        if not self.csv_path.exists():
            return pd.DataFrame(columns=[
                "title", "date", "theme", "descriptor", "link", "summary", "analysis"
            ])
        
        try:
            df = pd.read_csv(self.csv_path)
            if df.empty:
                return df
            
            # Convert date column to datetime
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading CSV file: {e}")
            raise RepositoryError(f"Failed to load data: {e}") from e

    def _save_dataframe(self, df: pd.DataFrame) -> None:
        """Save dataframe to CSV with atomic write."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.csv',
                delete=False,
                dir=self.csv_path.parent
            ) as temp_file:
                # Write to temporary file
                df.to_csv(temp_file.name, index=False)
                
                # Atomic move
                shutil.move(temp_file.name, self.csv_path)
                
        except Exception as e:
            self.logger.error(f"Error saving CSV file: {e}")
            raise RepositoryError(f"Failed to save data: {e}") from e

    def save_concept(self, concept: Concept) -> None:
        """Save a single concept."""
        self.save_concepts([concept])

    def save_concepts(self, concepts: List[Concept]) -> None:
        """Save multiple concepts with atomic write."""
        if not concepts:
            return
        
        self._acquire_lock()
        try:
            # Load existing data
            df = self._load_dataframe()
            
            # Convert concepts to records
            new_records = [concept.to_record() for concept in concepts]
            new_df = pd.DataFrame(new_records)
            
            if df.empty:
                # First time, just save new data
                combined_df = new_df
            else:
                # Merge with existing data
                combined_df = pd.concat([df, new_df], ignore_index=True)
                
                # Remove duplicates based on link, keeping the latest
                combined_df = combined_df.drop_duplicates(subset=["link"], keep="last")
                
                # Sort by theme and date
                combined_df = combined_df.sort_values(["theme", "date"], ascending=[True, False])
            
            # Convert date back to string for CSV
            combined_df["date"] = combined_df["date"].dt.strftime("%Y-%m-%d")
            
            # Fill NaN values
            combined_df = combined_df.fillna("")
            
            # Save atomically
            self._save_dataframe(combined_df)
            
            self.logger.info(f"Saved {len(concepts)} concepts to CSV")
            
        finally:
            self._release_lock()

    def get_concept_by_id(self, concept_id: str) -> Optional[Concept]:
        """Get concept by ID (link)."""
        try:
            df = self._load_dataframe()
            if df.empty:
                return None
            
            # Find concept by link
            concept_row = df[df["link"] == concept_id]
            if concept_row.empty:
                return None
            
            return Concept.from_record(concept_row.iloc[0].to_dict())
            
        except Exception as e:
            self.logger.error(f"Error getting concept by ID: {e}")
            raise RepositoryError(f"Failed to get concept: {e}") from e

    def get_concepts(
        self,
        limit: int = 10,
        offset: int = 0,
        theme: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Concept]:
        """Get concepts with filtering."""
        try:
            df = self._load_dataframe()
            if df.empty:
                return []
            
            # Apply filters
            if theme:
                df = df[df["theme"].str.contains(theme, case=False, na=False)]
            
            if date_from:
                df = df[pd.to_datetime(df["date"], errors="coerce") >= date_from]
            
            if date_to:
                df = df[pd.to_datetime(df["date"], errors="coerce") <= date_to]
            
            # Apply pagination
            df = df.iloc[offset:offset + limit]
            
            # Convert to concepts
            concepts = []
            for _, row in df.iterrows():
                try:
                    concept = Concept.from_record(row.to_dict())
                    concepts.append(concept)
                except Exception as e:
                    self.logger.warning(f"Error parsing concept row: {e}")
                    continue
            
            return concepts
            
        except Exception as e:
            self.logger.error(f"Error getting concepts: {e}")
            raise RepositoryError(f"Failed to get concepts: {e}") from e

    def search_concepts(self, request: ConceptSearchRequest) -> ConceptSearchResponse:
        """Search concepts with full-text search."""
        try:
            df = self._load_dataframe()
            if df.empty:
                return ConceptSearchResponse(
                    concepts=[],
                    total=0,
                    limit=request.limit,
                    offset=request.offset,
                    has_more=False
                )
            
            # Simple text search across title, theme, descriptor, summary, analysis
            search_columns = ["title", "theme", "descriptor", "summary", "analysis"]
            query_lower = request.query.lower()
            
            # Create search mask
            search_mask = pd.Series([False] * len(df))
            for col in search_columns:
                if col in df.columns:
                    search_mask |= df[col].str.contains(query_lower, case=False, na=False)
            
            # Apply search filter
            df_filtered = df[search_mask]
            
            # Apply additional filters
            if request.theme:
                df_filtered = df_filtered[df_filtered["theme"].str.contains(request.theme, case=False, na=False)]
            
            if request.date_from:
                df_filtered = df_filtered[pd.to_datetime(df_filtered["date"], errors="coerce") >= request.date_from]
            
            if request.date_to:
                df_filtered = df_filtered[pd.to_datetime(df_filtered["date"], errors="coerce") <= request.date_to]
            
            # Get total count
            total = len(df_filtered)
            
            # Apply pagination
            df_paginated = df_filtered.iloc[request.offset:request.offset + request.limit]
            
            # Convert to concepts
            concepts = []
            for _, row in df_paginated.iterrows():
                try:
                    concept = Concept.from_record(row.to_dict())
                    concepts.append(concept)
                except Exception as e:
                    self.logger.warning(f"Error parsing concept row: {e}")
                    continue
            
            return ConceptSearchResponse(
                concepts=concepts,
                total=total,
                limit=request.limit,
                offset=request.offset,
                has_more=request.offset + len(concepts) < total
            )
            
        except Exception as e:
            self.logger.error(f"Error searching concepts: {e}")
            raise RepositoryError(f"Failed to search concepts: {e}") from e

    def get_concept_count(self) -> int:
        """Get total number of concepts."""
        try:
            df = self._load_dataframe()
            return len(df)
        except Exception as e:
            self.logger.error(f"Error getting concept count: {e}")
            return 0

    def get_themes(self) -> List[str]:
        """Get list of unique themes."""
        try:
            df = self._load_dataframe()
            if df.empty:
                return []
            
            themes = df["theme"].dropna().unique().tolist()
            return sorted(themes)
            
        except Exception as e:
            self.logger.error(f"Error getting themes: {e}")
            return []

    def get_latest_concepts(self, limit: int = 10) -> List[Concept]:
        """Get latest concepts by date."""
        try:
            df = self._load_dataframe()
            if df.empty:
                return []
            
            # Sort by date descending
            df_sorted = df.sort_values("date", ascending=False)
            df_limited = df_sorted.head(limit)
            
            # Convert to concepts
            concepts = []
            for _, row in df_limited.iterrows():
                try:
                    concept = Concept.from_record(row.to_dict())
                    concepts.append(concept)
                except Exception as e:
                    self.logger.warning(f"Error parsing concept row: {e}")
                    continue
            
            return concepts
            
        except Exception as e:
            self.logger.error(f"Error getting latest concepts: {e}")
            return []

    def concept_exists(self, concept_id: str) -> bool:
        """Check if concept exists."""
        try:
            df = self._load_dataframe()
            if df.empty:
                return False
            
            return concept_id in df["link"].values
            
        except Exception as e:
            self.logger.error(f"Error checking concept existence: {e}")
            return False

    def delete_concept(self, concept_id: str) -> bool:
        """Delete a concept."""
        self._acquire_lock()
        try:
            df = self._load_dataframe()
            if df.empty:
                return False
            
            # Check if concept exists
            if concept_id not in df["link"].values:
                return False
            
            # Remove concept
            df_filtered = df[df["link"] != concept_id]
            
            # Save updated data
            self._save_dataframe(df_filtered)
            
            self.logger.info(f"Deleted concept: {concept_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting concept: {e}")
            raise RepositoryError(f"Failed to delete concept: {e}") from e
        finally:
            self._release_lock()

    def clear_all(self) -> None:
        """Clear all concepts."""
        self._acquire_lock()
        try:
            # Create empty dataframe
            empty_df = pd.DataFrame(columns=[
                "title", "date", "theme", "descriptor", "link", "summary", "analysis"
            ])
            
            # Save empty data
            self._save_dataframe(empty_df)
            
            self.logger.info("Cleared all concepts")
            
        except Exception as e:
            self.logger.error(f"Error clearing concepts: {e}")
            raise RepositoryError(f"Failed to clear concepts: {e}") from e
        finally:
            self._release_lock()

    def backup(self) -> str:
        """Create backup and return backup path."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.csv_path.parent / f"conceptos_dian_backup_{timestamp}.csv"
            
            # Copy current file to backup
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
            
            # Create backup of current file
            current_backup = self.backup()
            
            # Restore from backup
            shutil.copy2(backup_file, self.csv_path)
            
            self.logger.info(f"Restored from backup: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {e}")
            raise RepositoryError(f"Failed to restore from backup: {e}") from e
