"""
Tests for health endpoint
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    """Test that health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_correct_structure():
    """Test that health endpoint returns expected JSON structure"""
    response = client.get("/health")
    data = response.json()

    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert data["status"] == "healthy"


def test_root_endpoint_returns_200():
    """Test that root endpoint returns 200 OK"""
    response = client.get("/")
    assert response.status_code == 200


def test_security_headers_present():
    """Test that security headers are present in response"""
    response = client.get("/health")
    headers = response.headers

    assert "X-Content-Type-Options" in headers
    assert headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] == "DENY"

    assert "X-XSS-Protection" in headers

    assert "Strict-Transport-Security" in headers

    assert "Content-Security-Policy" in headers
