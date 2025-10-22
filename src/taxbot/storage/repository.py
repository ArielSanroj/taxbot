"""Repository interface for concept storage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..models.concept import Concept, ConceptSearchRequest, ConceptSearchResponse


class RepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class ConceptNotFoundError(RepositoryError):
    """Exception raised when concept is not found."""

    pass


class Repository(ABC):
    """Abstract repository interface for concept storage."""

    @abstractmethod
    def save_concept(self, concept: Concept) -> None:
        """Save a single concept."""
        pass

    @abstractmethod
    def save_concepts(self, concepts: List[Concept]) -> None:
        """Save multiple concepts."""
        pass

    @abstractmethod
    def get_concept_by_id(self, concept_id: str) -> Optional[Concept]:
        """Get concept by ID (link)."""
        pass

    @abstractmethod
    def get_concepts(
        self,
        limit: int = 10,
        offset: int = 0,
        theme: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Concept]:
        """Get concepts with filtering."""
        pass

    @abstractmethod
    def search_concepts(self, request: ConceptSearchRequest) -> ConceptSearchResponse:
        """Search concepts with full-text search."""
        pass

    @abstractmethod
    def get_concept_count(self) -> int:
        """Get total number of concepts."""
        pass

    @abstractmethod
    def get_themes(self) -> List[str]:
        """Get list of unique themes."""
        pass

    @abstractmethod
    def get_latest_concepts(self, limit: int = 10) -> List[Concept]:
        """Get latest concepts by date."""
        pass

    @abstractmethod
    def concept_exists(self, concept_id: str) -> bool:
        """Check if concept exists."""
        pass

    @abstractmethod
    def delete_concept(self, concept_id: str) -> bool:
        """Delete a concept."""
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """Clear all concepts."""
        pass

    @abstractmethod
    def backup(self) -> str:
        """Create backup and return backup path."""
        pass

    @abstractmethod
    def restore(self, backup_path: str) -> None:
        """Restore from backup."""
        pass
