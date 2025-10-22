"""Unit tests for domain models."""

import pytest
from datetime import datetime

from taxbot.models.concept import Concept, ConceptSearchRequest


def test_concept_creation():
    """Test concept creation and validation."""
    concept = Concept(
        title="Test Concept",
        date=datetime(2025, 1, 1),
        theme="Test Theme",
        descriptor="Test descriptor",
        link="https://example.com/test",
        full_text="Test content",
    )
    
    assert concept.title == "Test Concept"
    assert concept.date == datetime(2025, 1, 1)
    assert concept.theme == "Test Theme"
    assert concept.link == "https://example.com/test"


def test_concept_validation():
    """Test concept validation."""
    # Test empty title
    with pytest.raises(ValueError):
        Concept(
            title="",
            date=datetime(2025, 1, 1),
            theme="Test",
            descriptor="Test",
            link="https://example.com/test",
        )
    
    # Test invalid URL
    with pytest.raises(ValueError):
        Concept(
            title="Test",
            date=datetime(2025, 1, 1),
            theme="Test",
            descriptor="Test",
            link="invalid-url",
        )


def test_concept_to_record():
    """Test concept to record conversion."""
    concept = Concept(
        title="Test Concept",
        date=datetime(2025, 1, 1),
        theme="Test Theme",
        descriptor="Test descriptor",
        link="https://example.com/test",
        full_text="Test content",
        summary="Test summary",
        analysis="Test analysis",
    )
    
    record = concept.to_record()
    
    assert record["title"] == "Test Concept"
    assert record["date"] == "2025-01-01"
    assert record["theme"] == "Test Theme"
    assert record["summary"] == "Test summary"
    assert record["analysis"] == "Test analysis"


def test_concept_from_record():
    """Test concept creation from record."""
    record = {
        "title": "Test Concept",
        "date": "2025-01-01",
        "theme": "Test Theme",
        "descriptor": "Test descriptor",
        "link": "https://example.com/test",
        "summary": "Test summary",
        "analysis": "Test analysis",
    }
    
    concept = Concept.from_record(record)
    
    assert concept.title == "Test Concept"
    assert concept.date == datetime(2025, 1, 1)
    assert concept.theme == "Test Theme"
    assert concept.summary == "Test summary"
    assert concept.analysis == "Test analysis"


def test_concept_has_ai_content():
    """Test AI content detection."""
    concept_with_ai = Concept(
        title="Test",
        date=datetime(2025, 1, 1),
        theme="Test",
        descriptor="Test",
        link="https://example.com/test",
        summary="Summary",
        analysis="Analysis",
    )
    
    concept_without_ai = Concept(
        title="Test",
        date=datetime(2025, 1, 1),
        theme="Test",
        descriptor="Test",
        link="https://example.com/test",
    )
    
    assert concept_with_ai.has_ai_content() is True
    assert concept_without_ai.has_ai_content() is False


def test_concept_search_request():
    """Test concept search request validation."""
    request = ConceptSearchRequest(
        query="test query",
        limit=10,
        offset=0,
    )
    
    assert request.query == "test query"
    assert request.limit == 10
    assert request.offset == 0
    
    # Test empty query
    with pytest.raises(ValueError):
        ConceptSearchRequest(query="")
    
    # Test invalid limit
    with pytest.raises(ValueError):
        ConceptSearchRequest(query="test", limit=0)
    
    # Test invalid offset
    with pytest.raises(ValueError):
        ConceptSearchRequest(query="test", offset=-1)
