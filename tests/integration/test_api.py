"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from taxbot.models.concept import ConceptSearchRequest


def test_health_endpoint(test_client: TestClient):
    """Test health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_metrics_endpoint(test_client: TestClient):
    """Test metrics endpoint."""
    response = test_client.get("/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert "concepts" in data
    assert "api" in data


def test_list_concepts(test_client: TestClient):
    """Test listing concepts."""
    response = test_client.get("/api/v1/concepts")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_list_concepts_with_params(test_client: TestClient):
    """Test listing concepts with parameters."""
    response = test_client.get("/api/v1/concepts?limit=5&offset=0")
    assert response.status_code == 200


def test_search_concepts(test_client: TestClient):
    """Test searching concepts."""
    search_request = {
        "query": "test",
        "limit": 10,
        "offset": 0
    }
    
    response = test_client.post("/api/v1/concepts/search", json=search_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "concepts" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


def test_get_themes(test_client: TestClient):
    """Test getting themes."""
    response = test_client.get("/api/v1/concepts/themes")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_get_latest_concepts(test_client: TestClient):
    """Test getting latest concepts."""
    response = test_client.get("/api/v1/concepts/latest")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_admin_status(test_client: TestClient):
    """Test admin status endpoint."""
    response = test_client.get("/api/v1/admin/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "is_running" in data
    assert "total_concepts" in data


def test_admin_scrape_unauthorized(test_client: TestClient):
    """Test admin scrape endpoint without API key."""
    response = test_client.post("/api/v1/admin/scrape")
    assert response.status_code == 401


def test_admin_scrape_authorized(test_client: TestClient):
    """Test admin scrape endpoint with API key."""
    headers = {"X-API-Key": "test_api_key"}
    response = test_client.post("/api/v1/admin/scrape", headers=headers)
    assert response.status_code in [200, 409]  # 409 if already running


def test_admin_reprocess_unauthorized(test_client: TestClient):
    """Test admin reprocess endpoint without API key."""
    response = test_client.post("/api/v1/admin/reprocess")
    assert response.status_code == 401


def test_admin_reprocess_authorized(test_client: TestClient):
    """Test admin reprocess endpoint with API key."""
    headers = {"X-API-Key": "test_api_key"}
    response = test_client.post("/api/v1/admin/reprocess", headers=headers)
    assert response.status_code == 200


def test_admin_backup_unauthorized(test_client: TestClient):
    """Test admin backup endpoint without API key."""
    response = test_client.post("/api/v1/admin/backup")
    assert response.status_code == 401


def test_admin_backup_authorized(test_client: TestClient):
    """Test admin backup endpoint with API key."""
    headers = {"X-API-Key": "test_api_key"}
    response = test_client.post("/api/v1/admin/backup", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "backup_path" in data
