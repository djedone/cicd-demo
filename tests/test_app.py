import pytest
from app.main import create_app
from app.database import db, init_db
import json

@pytest.fixture
def app():
    """Create a Flask app configured for testing"""
    test_app = create_app(testing=True)
    
    with test_app.app_context():
        db.create_all()
        init_db()
        yield test_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

def test_health(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["status"] == "UP"

def test_create_deployment(client):
    """Test creating a deployment"""
    deployment_data = {
        "version": "1.0.0",
        "environment": "staging"
    }
    response = client.post(
        "/api/deployments",
        data=json.dumps(deployment_data),
        content_type="application/json"
    )
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data
    assert data["version"] == "1.0.0"
    assert data["environment"] == "staging"

def test_get_deployments(client):
    """Test getting deployments"""
    # First, create a deployment
    test_create_deployment(client)
    
    # Then get all deployments
    response = client.get("/api/deployments")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert isinstance(data, dict)
    assert "deployments" in data
    assert len(data["deployments"]) > 0
    assert "version" in data["deployments"][0]
    assert "environment" in data["deployments"][0]