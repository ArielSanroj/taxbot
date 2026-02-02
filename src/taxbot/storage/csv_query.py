"""CSV query operations for repository."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import pandas as pd

from ..core.logging import get_scraper_logger
from ..models.concept import Concept, ConceptSearchRequest, ConceptSearchResponse
from .repository import RepositoryError


class CsvQuery:
    """Handles query operations on CSV data."""

    def __init__(self, logger=None):
        """Initialize CSV query handler."""
        self.logger = logger or get_scraper_logger()

    def apply_date_filters(
        self,
        df: pd.DataFrame,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Apply date range filters to dataframe."""
        if date_from:
            df = df[pd.to_datetime(df["date"], errors="coerce") >= date_from]
        if date_to:
            df = df[pd.to_datetime(df["date"], errors="coerce") <= date_to]
        return df

    def apply_theme_filter(
        self, df: pd.DataFrame, theme: Optional[str]
    ) -> pd.DataFrame:
        """Apply theme filter to dataframe."""
        if theme:
            df = df[df["theme"].str.contains(theme, case=False, na=False)]
        return df

    def apply_pagination(
        self, df: pd.DataFrame, offset: int, limit: int
    ) -> pd.DataFrame:
        """Apply pagination to dataframe."""
        return df.iloc[offset:offset + limit]

    def dataframe_to_concepts(self, df: pd.DataFrame) -> List[Concept]:
        """Convert dataframe rows to Concept objects."""
        concepts = []
        for _, row in df.iterrows():
            try:
                concept = Concept.from_record(row.to_dict())
                concepts.append(concept)
            except Exception as e:
                self.logger.warning(f"Error parsing concept row: {e}")
                continue
        return concepts

    def get_concepts(
        self,
        df: pd.DataFrame,
        limit: int = 10,
        offset: int = 0,
        theme: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Concept]:
        """Get concepts with filtering."""
        try:
            if df.empty:
                return []

            df = self.apply_theme_filter(df, theme)
            df = self.apply_date_filters(df, date_from, date_to)
            df = self.apply_pagination(df, offset, limit)

            return self.dataframe_to_concepts(df)

        except Exception as e:
            self.logger.error(f"Error getting concepts: {e}")
            raise RepositoryError(f"Failed to get concepts: {e}") from e

    def search_concepts(
        self, df: pd.DataFrame, request: ConceptSearchRequest
    ) -> ConceptSearchResponse:
        """Search concepts with full-text search."""
        try:
            if df.empty:
                return self._empty_search_response(request)

            df_filtered = self._apply_text_search(df, request.query)
            df_filtered = self.apply_theme_filter(df_filtered, request.theme)
            df_filtered = self.apply_date_filters(
                df_filtered, request.date_from, request.date_to
            )

            total = len(df_filtered)
            df_paginated = self.apply_pagination(
                df_filtered, request.offset, request.limit
            )
            concepts = self.dataframe_to_concepts(df_paginated)

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

    def _apply_text_search(self, df: pd.DataFrame, query: str) -> pd.DataFrame:
        """Apply text search across multiple columns."""
        search_columns = ["title", "theme", "descriptor", "summary", "analysis"]
        query_lower = query.lower()

        search_mask = pd.Series([False] * len(df))
        for col in search_columns:
            if col in df.columns:
                search_mask |= df[col].str.contains(
                    query_lower, case=False, na=False
                )

        return df[search_mask]

    def _empty_search_response(
        self, request: ConceptSearchRequest
    ) -> ConceptSearchResponse:
        """Return empty search response."""
        return ConceptSearchResponse(
            concepts=[],
            total=0,
            limit=request.limit,
            offset=request.offset,
            has_more=False
        )

    def get_latest_concepts(
        self, df: pd.DataFrame, limit: int = 10
    ) -> List[Concept]:
        """Get latest concepts by date."""
        try:
            if df.empty:
                return []

            df_sorted = df.sort_values("date", ascending=False)
            df_limited = df_sorted.head(limit)

            return self.dataframe_to_concepts(df_limited)

        except Exception as e:
            self.logger.error(f"Error getting latest concepts: {e}")
            return []
