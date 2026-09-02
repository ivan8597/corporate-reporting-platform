from fastapi.testclient import TestClient

from api.app import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_anomalies_endpoint_before_pipeline():
    response = client.get("/anomalies")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"not_ready", "ready"}
    assert "count" in body
    assert "anomalies" in body
