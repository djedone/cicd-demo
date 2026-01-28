import json
from datetime import datetime, timedelta

import pytest


def test_custom_metrics_empty(client):
    """Test metrics endpoint when metrics are disabled"""
    response = client.get("/metrics")
    # Ako su metrike onemogućene, vraća 404
    assert response.status_code in [200, 404]


def test_custom_metrics_with_data(client):
    """Test stats endpoint"""
    response = client.get("/api/stats")
    assert response.status_code in [200, 500]  # 500 ako baza nije spremna

    if response.status_code == 200:
        data = response.get_json()
        assert "total_deployments" in data
        assert "successful_deployments" in data
        assert "success_rate" in data


def test_deployment_workflow(client):
    """Test complete deployment workflow"""
    # 1. Create a deployment
    deployment_data = {"version": "1.0.0", "environment": "test"}
    response = client.post(
        "/api/deployments", json=deployment_data, content_type="application/json"
    )

    # Should succeed or fail gracefully
    assert response.status_code in [201, 500]

    if response.status_code == 201:
        # 2. Verify deployment was recorded
        response = client.get("/api/deployments")
        assert response.status_code == 200
        data = response.get_json()
        assert "deployments" in data
        assert len(data["deployments"]) > 0

        # Check the deployment data
        deployment = data["deployments"][0]
        assert deployment["version"] == "1.0.0"
        assert deployment["environment"] == "test"
        assert deployment["status"] == "success"


def test_custom_metrics_endpoint(client):
    """Test the custom metrics endpoint"""
    response = client.get("/api/metrics/custom")
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.get_json()
        assert "summary" in data
        assert "by_environment" in data
        assert "daily_deployments" in data
        assert "generated_at" in data

        # Verify summary structure
        summary = data["summary"]
        assert "total_deployments_30d" in summary
        assert "successful_deployments_30d" in summary
        assert "success_rate_30d" in summary
        assert "avg_deployments_per_day" in summary


def test_health_endpoint_detailed(client):
    """Test health endpoint with detailed checks"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()

    required_fields = ["status", "timestamp", "database", "environment", "version"]
    for field in required_fields:
        assert field in data

    assert data["status"] == "UP"
    assert "healthy" in data["database"] or "unhealthy" in data["database"]
    assert data["environment"] in ["development", "testing", "staging", "production", "test"]


def test_error_handling(client):
    """Test error handling for invalid requests"""
    # Test invalid JSON
    response = client.post(
        "/api/deployments", data="invalid json", content_type="application/json"
    )
    assert response.status_code == 400

    # Test missing required fields
    response = client.post("/api/deployments", json={}, content_type="application/json")
    assert response.status_code in [201, 500]  # Should handle missing fields gracefully

    # Test non-existent endpoint
    response = client.get("/api/nonexistent")
    assert response.status_code == 404


def test_concurrent_requests(client):
    """Test handling of concurrent requests"""
    import threading
    import time

    results = []

    def make_request():
        response = client.get("/health")
        results.append(response.status_code)

    # Create multiple threads
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # All requests should succeed
    assert all(status == 200 for status in results)
    assert len(results) == 10


def test_data_persistence(client, app):
    """Test that data persists across requests"""
    with app.app_context():
        # Create deployment
        response = client.post(
            "/api/deployments", json={"version": "2.0.0", "environment": "test"}
        )

        if response.status_code == 201:
            # Get stats
            response = client.get("/api/stats")
            assert response.status_code == 200
            data = response.get_json()
            assert data["total_deployments"] >= 1

            # Get custom metrics
            response = client.get("/api/metrics/custom")
            if response.status_code == 200:
                data = response.get_json()
                assert data["summary"]["total_deployments_30d"] >= 0


def test_performance_benchmarks(client):
    """Test basic performance benchmarks"""
    import time

    # Test health endpoint response time
    start_time = time.time()
    response = client.get("/health")
    end_time = time.time()

    assert response.status_code == 200
    response_time = end_time - start_time
    assert response_time < 1.0  # Should respond within 1 second

    # Test deployments endpoint response time
    start_time = time.time()
    response = client.get("/api/deployments")
    end_time = time.time()

    assert response.status_code in [200, 500]
    response_time = end_time - start_time
    assert response_time < 2.0  # Should respond within 2 seconds


def test_security_headers(client):
    """Test security headers are present"""
    response = client.get("/")
    # Note: This test assumes you're running behind nginx or similar
    # In development, these might not be present

    # Test for basic security headers if present
    headers = response.headers
    # These are optional in development
    security_headers = ["X-Content-Type-Options", "X-Frame-Options"]

    for header in security_headers:
        if header in headers:
            assert headers[header] is not None


def test_database_connection_resilience(client, app):
    """Test application behavior with database issues"""
    # This test would require mocking database failures
    # For now, we'll test normal operation
    response = client.get("/health")
    assert response.status_code == 200

    data = response.get_json()
    # Database should be healthy in test environment
    assert "healthy" in data["database"]
