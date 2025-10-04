# ABOUTME: Unit tests for the health endpoint and request ID middleware
# ABOUTME: Validates API status responses and request ID injection functionality

from fastapi.testclient import TestClient

from app.main import app


class TestHealthEndpoint:
    """Test suite for the /health endpoint."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)

    def test_health_endpoint_returns_200(self):
        """Test that /health returns HTTP 200."""
        response = self.client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self):
        """Test that /health returns valid JSON with expected structure."""
        response = self.client.get("/health")
        json_data = response.json()

        assert "status" in json_data
        assert "version" in json_data
        assert json_data["status"] == "ok"
        assert json_data["version"] == "0.1.0"

    def test_health_endpoint_has_request_id_header(self):
        """Test that response includes X-Request-ID header."""
        response = self.client.get("/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_health_endpoint_preserves_existing_request_id(self):
        """Test that existing X-Request-ID is preserved."""
        custom_id = "test-request-123"
        response = self.client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.headers["X-Request-ID"] == custom_id
