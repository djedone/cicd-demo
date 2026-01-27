# tests/test_integration.py
import pytest
import os
from app.main import create_app
from app.database import db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    # Koristi environment varijablu ili sqlite za test
    test_db_url = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
    app.config['SQLALCHEMY_DATABASE_URI'] = test_db_url
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_custom_metrics_empty(client):
    response = client.get("/api/metrics/custom")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_deployments"] == 0
    assert data["success_rate"] == 0

def test_custom_metrics_with_data(client):
    # Kreiraj nekoliko deploymenta
    deployments = [
        {"version": "1.0.0", "status": "success", "user": "user1"},
        {"version": "1.0.1", "status": "success", "user": "user2"},
        {"version": "1.0.2", "status": "failed", "user": "user3"},
    ]
    
    for deployment in deployments:
        client.post("/api/deployments", json=deployment)
    
    response = client.get("/api/metrics/custom")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_deployments"] == 3
    assert data["successful_deployments"] == 2
    assert data["failed_deployments"] == 1
    assert data["success_rate"] == 2/3