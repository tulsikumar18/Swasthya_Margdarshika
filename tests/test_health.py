from fastapi.testclient import TestClient

def test_health_check_endpoint(client: TestClient):
    """Test 2: Health-check endpoint GET /api/health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["app_name"] == "Personalized Medical Recommendation System"
    assert data["model_loaded"] is True
    assert data["supported_symptoms_count"] == 132
    assert data["supported_diseases_count"] == 41

    # Security verification: Ensure no credentials or secret keys are exposed
    json_str = str(data).lower()
    assert "secret" not in json_str or "secret_key" not in data
    assert "aizasy" not in json_str
