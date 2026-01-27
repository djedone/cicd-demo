import app

def test_home():
    client = app.app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"CI/CD Cloud Demo" in response.data

def test_health():
    client = app.app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "UP"
