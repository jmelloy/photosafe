"""Tests for version endpoint"""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_version_endpoint():
    """Test that /api/version endpoint returns version"""
    response = client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)
    assert data["version"] != "unknown"
    # Should match semantic version pattern
    assert len(data["version"].split(".")) >= 2


def test_root_endpoint_includes_version():
    """Test that root endpoint includes version"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)
    assert data["version"] != "unknown"
