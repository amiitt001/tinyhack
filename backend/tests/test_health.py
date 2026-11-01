def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready(client):
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_integrations_reports_safe_configuration_status(client):
    response = client.get("/api/v1/integrations")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert isinstance(body["gemini"]["configured"], bool)
    assert body["gemini"]["model"]
    assert "api_key" not in str(body).lower()
