from fastapi.testclient import TestClient

def test_valid_recognized_symptoms_prediction(client: TestClient):
    """Test 4 & 12: Valid recognized symptoms and correct prediction response structure."""
    payload = {
        "symptoms": ["itching", "skin_rash", "nodal_skin_eruptions", "dischromic _patches"],
        "allow_ai_fallback": True
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["mode"] == "ml_prediction"
    assert data["predicted_disease"] == "Fungal infection"
    assert data["confidence"] is None  # SVC model probability=False -> explicit None
    assert isinstance(data["description"], str)
    assert len(data["description"]) > 10

    # Test 13: Existing recommendation data compatibility
    assert isinstance(data["medications"], list)
    assert len(data["medications"]) > 0
    assert len(data["medications"]) <= 5  # Top 5 preserved

    assert isinstance(data["precautions"], list)
    assert len(data["precautions"]) >= 1

    assert isinstance(data["diet_recommendations"], list)
    assert len(data["diet_recommendations"]) >= 1

    assert isinstance(data["workout_recommendations"], list)
    assert len(data["workout_recommendations"]) >= 1

    assert "disclaimer" in data
    assert "NOT a substitute for professional medical advice" in data["disclaimer"]

def test_empty_symptom_submission(client: TestClient):
    """Test 5: Empty symptom submissions."""
    # Empty list in payload
    response = client.post("/api/predict", json={"symptoms": []})
    assert response.status_code == 422

    # Whitespace only symptoms
    response = client.post("/api/predict", json={"symptoms": ["   ", ""]})
    assert response.status_code == 422

def test_duplicate_symptoms_handling(client: TestClient):
    """Test 6: Duplicate symptoms handling."""
    payload = {
        "symptoms": ["itching", "itching", "skin_rash", "itching", "nodal_skin_eruptions", "dischromic _patches"],
        "allow_ai_fallback": True
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["predicted_disease"] == "Fungal infection"
    # Deduplicated recognized symptoms
    assert data["recognized_symptoms"].count("itching") == 1
    assert data["recognized_symptoms"].count("skin_rash") == 1

def test_symptom_alias_and_formatting_normalization(client: TestClient):
    """Test symptom normalization (spaces vs underscores, aliases)."""
    payload = {
        "symptoms": ["joint pain", "knee pain", "neck pain", "back pain"],
        "allow_ai_fallback": True
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "joint_pain" in data["recognized_symptoms"]
    assert "knee_pain" in data["recognized_symptoms"]
