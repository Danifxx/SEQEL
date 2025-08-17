from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_pin_authentication():
    response = client.get("/admin/settings")
    assert response.status_code == 401  # Should fail without PIN

    response = client.get("/admin/settings", headers={"X-Pin": "wrong_pin"})
    assert response.status_code == 401  # Should fail with wrong PIN