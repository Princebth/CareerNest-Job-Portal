from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

def test_jobs_endpoint_requires_no_login():
    # This test needs a working configured MySQL database because the app lifespan creates tables.
    with TestClient(app) as client:
        response = client.get("/api/jobs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
