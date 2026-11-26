from fastapi.testclient import TestClient
from app.main import app

def test_provider_endpoint_requires_auth():
    response=TestClient(app).get('/v1/providers')
    assert response.status_code in (401,503)
