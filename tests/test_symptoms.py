from fastapi.testclient import TestClient

def test_list_all_symptoms(client: TestClient):
    """Test GET /api/symptoms returns all 132 symptoms."""
    response = client.get("/api/symptoms")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 132
    assert len(data["symptoms"]) == 132
    first_item = data["symptoms"][0]
    assert "key" in first_item
    assert "label" in first_item
    assert "index" in first_item

def test_search_symptoms(client: TestClient):
    """Test GET /api/symptoms/search filtering."""
    response = client.get("/api/symptoms/search?q=fever")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 2  # high_fever, mild_fever
    keys = [r["key"] for r in results]
    assert "high_fever" in keys or "mild_fever" in keys
