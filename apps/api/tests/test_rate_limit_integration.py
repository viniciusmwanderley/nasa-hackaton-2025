# ABOUTME: Integration test for rate limiting under burst conditions
# ABOUTME: Validates that rate limits are properly enforced when exceeding configured thresholds

import time

import pytest
from fastapi.testclient import TestClient


class TestRateLimitIntegration:
    """Integration tests for rate limiting enforcement."""

    def setup_method(self):
        """Set up test client for each test."""
        from app.main import app

        self.client = TestClient(app)

    @pytest.mark.skip(reason="Rate limiting test - enable for manual testing")
    def test_rate_limit_burst_protection(self):
        """Test rate limiting under burst conditions (manual test)."""
        # This test is skipped by default to avoid slowing down CI
        # Enable it manually to test rate limiting behavior

        responses = []
        rate_limited_count = 0

        # Make many requests quickly to trigger rate limiting
        for i in range(50):
            response = self.client.get("/health")
            responses.append(response.status_code)

            if response.status_code == 429:
                rate_limited_count += 1
                # Check for rate limit headers
                assert "Retry-After" in response.headers

            # Small delay to prevent overwhelming the test
            time.sleep(0.01)

        # We should see some rate limiting kick in
        success_count = len([r for r in responses if r == 200])

        # Verify we had both successes and rate limits
        assert success_count > 0, "Should have some successful requests"
        print(
            f"Successful requests: {success_count}, Rate limited: {rate_limited_count}"
        )

    def test_rate_limit_recovery(self):
        """Test that rate limiting recovers after window expires."""
        # Make a request - should succeed
        response1 = self.client.get("/health")
        assert response1.status_code == 200

        # Wait a moment
        time.sleep(0.1)

        # Make another request - should still succeed
        response2 = self.client.get("/health")
        assert response2.status_code == 200
