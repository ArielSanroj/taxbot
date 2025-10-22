"""Test configuration and fixtures."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from taxbot.api.app import create_app
from taxbot.core.config import Settings
from taxbot.models.concept import Concept
from taxbot.storage.csv_repository import CsvRepository


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    """Create test settings."""
    return Settings(
        data_dir=temp_dir,
        ollama_model="llama3",
        ollama_base_url="http://localhost:11434",
        email_sender="test@example.com",
        email_password="test_password",
        email_recipients=["recipient@example.com"],
        jwt_secret_key="test_secret_key",
        api_key="test_api_key",
        debug=True,
    )


@pytest.fixture
def test_concept() -> Concept:
    """Create test concept."""
    from datetime import datetime
    
    return Concept(
        title="Test Concept",
        date=datetime(2025, 1, 1),
        theme="Test Theme",
        descriptor="Test descriptor",
        link="https://example.com/test",
        full_text="Test full text content",
        summary="Test summary",
        analysis="Test analysis",
    )


@pytest.fixture
def test_repository(temp_dir: Path) -> CsvRepository:
    """Create test repository."""
    csv_path = temp_dir / "test_concepts.csv"
    return CsvRepository(csv_path)


@pytest.fixture
def test_app(test_settings: Settings):
    """Create test FastAPI app."""
    # Override settings for testing
    import taxbot.core.config
    taxbot.core.config.settings = test_settings
    
    app = create_app()
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def sample_concepts() -> list[Concept]:
    """Create sample concepts for testing."""
    from datetime import datetime
    
    return [
        Concept(
            title="Concept 1",
            date=datetime(2025, 1, 1),
            theme="IVA",
            descriptor="Test descriptor 1",
            link="https://example.com/concept1",
            full_text="Full text 1",
        ),
        Concept(
            title="Concept 2",
            date=datetime(2025, 1, 2),
            theme="Renta",
            descriptor="Test descriptor 2",
            link="https://example.com/concept2",
            full_text="Full text 2",
        ),
    ]
