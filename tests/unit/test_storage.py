"""Unit tests for storage components."""

import pytest
from datetime import datetime

from taxbot.models.concept import Concept
from taxbot.storage.csv_repository import CsvRepository


def test_csv_repository_creation(test_repository: CsvRepository):
    """Test CSV repository creation."""
    assert test_repository.csv_path.exists() is False


def test_save_and_get_concept(test_repository: CsvRepository, test_concept: Concept):
    """Test saving and retrieving a concept."""
    # Save concept
    test_repository.save_concept(test_concept)
    
    # Verify concept was saved
    assert test_repository.csv_path.exists()
    assert test_repository.get_concept_count() == 1
    
    # Retrieve concept
    retrieved = test_repository.get_concept_by_id(test_concept.link)
    assert retrieved is not None
    assert retrieved.title == test_concept.title
    assert retrieved.link == test_concept.link


def test_save_multiple_concepts(test_repository: CsvRepository, sample_concepts: list[Concept]):
    """Test saving multiple concepts."""
    # Save concepts
    test_repository.save_concepts(sample_concepts)
    
    # Verify concepts were saved
    assert test_repository.get_concept_count() == 2
    
    # Retrieve all concepts
    concepts = test_repository.get_concepts(limit=10)
    assert len(concepts) == 2


def test_concept_exists(test_repository: CsvRepository, test_concept: Concept):
    """Test concept existence check."""
    # Concept should not exist initially
    assert test_repository.concept_exists(test_concept.link) is False
    
    # Save concept
    test_repository.save_concept(test_concept)
    
    # Concept should exist now
    assert test_repository.concept_exists(test_concept.link) is True


def test_get_concepts_with_filtering(test_repository: CsvRepository, sample_concepts: list[Concept]):
    """Test getting concepts with filtering."""
    # Save concepts
    test_repository.save_concepts(sample_concepts)
    
    # Test theme filtering
    iva_concepts = test_repository.get_concepts(theme="IVA")
    assert len(iva_concepts) == 1
    assert iva_concepts[0].theme == "IVA"
    
    # Test limit
    limited_concepts = test_repository.get_concepts(limit=1)
    assert len(limited_concepts) == 1


def test_search_concepts(test_repository: CsvRepository, sample_concepts: list[Concept]):
    """Test concept search."""
    from taxbot.models.concept import ConceptSearchRequest
    
    # Save concepts
    test_repository.save_concepts(sample_concepts)
    
    # Search for concepts
    search_request = ConceptSearchRequest(query="Concept", limit=10)
    response = test_repository.search_concepts(search_request)
    
    assert len(response.concepts) == 2
    assert response.total == 2


def test_get_themes(test_repository: CsvRepository, sample_concepts: list[Concept]):
    """Test getting unique themes."""
    # Save concepts
    test_repository.save_concepts(sample_concepts)
    
    # Get themes
    themes = test_repository.get_themes()
    assert len(themes) == 2
    assert "IVA" in themes
    assert "Renta" in themes


def test_delete_concept(test_repository: CsvRepository, test_concept: Concept):
    """Test deleting a concept."""
    # Save concept
    test_repository.save_concept(test_concept)
    assert test_repository.get_concept_count() == 1
    
    # Delete concept
    success = test_repository.delete_concept(test_concept.link)
    assert success is True
    assert test_repository.get_concept_count() == 0
    
    # Try to delete non-existent concept
    success = test_repository.delete_concept("non-existent")
    assert success is False


def test_backup_and_restore(test_repository: CsvRepository, test_concept: Concept):
    """Test backup and restore functionality."""
    # Save concept
    test_repository.save_concept(test_concept)
    assert test_repository.get_concept_count() == 1
    
    # Create backup
    backup_path = test_repository.backup()
    assert Path(backup_path).exists()
    
    # Clear repository
    test_repository.clear_all()
    assert test_repository.get_concept_count() == 0
    
    # Restore from backup
    test_repository.restore(backup_path)
    assert test_repository.get_concept_count() == 1
    
    # Verify concept was restored
    restored = test_repository.get_concept_by_id(test_concept.link)
    assert restored is not None
    assert restored.title == test_concept.title
