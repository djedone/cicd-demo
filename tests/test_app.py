# tests/test_app.py
import pytest
from app.main import create_app
from app.database import db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "UP"}

def test_get_deployments_empty(client):
    response = client.get("/api/deployments")
    assert response.status_code == 200
    assert response.get_json() == []

def test_create_deployment(client):
    deployment_data = {
        "version": "1.0.0",
        "status": "success",
        "user": "test_user",
        "commit_hash": "abc123",
        "environment": "staging"
    }
    response = client.post("/api/deployments", json=deployment_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data["version"] == "1.0.0"
    assert data["status"] == "success"
    assert data["user"] == "test_user"
    
    # Provjeri da li se deployment pojavljuje u listi
    response = client.get("/api/deployments")
    assert response.status_code == 200
    deployments = response.get_json()
    assert len(deployments) == 1
    assert deployments[0]["version"] == "1.0.0"