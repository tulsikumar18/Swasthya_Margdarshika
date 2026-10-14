import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import requests

def test_unsupported_symptoms_fallback_when_no_api_key(client: TestClient):
    """Test 7 & 9: Unsupported symptoms when no Gemini API key is configured."""
    with patch("app.core.config.settings.GEMINI_API_KEY", ""):
        payload = {
            "symptoms": ["unknown_alien_symptom", "strange_aura_buzzing"],
            "allow_ai_fallback": True
        }
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["mode"] == "fallback"
        assert len(data["unrecognized_symptoms"]) == 2
        assert "not present in our system's 132-symptom machine learning database" in data["description"]
        assert len(data["precautions"]) > 0
        assert "disclaimer" in data

def test_ai_fallback_when_configured_with_valid_response(client: TestClient):
    """Test 8: AI fallback when configured (mocked Gemini API response)."""
    mock_gemini_json = {
        "condition_or_topic": "Potential Upper Respiratory Discomfort",
        "description": "These symptoms are often seen in acute environmental or viral throat irritation.",
        "precautions": ["Stay well hydrated", "Avoid cold air and smoke", "Rest your voice"],
        "non_prescription_care": ["Warm salt water gargle", "Honey and warm herbal tea"],
        "lifestyle_and_diet": ["Nutrient dense soups", "Warm liquids"],
        "suggested_activities": ["Adequate bed rest"],
        "clarifying_questions": ["How long have you had this throat irritation?", "Do you have an accompanying fever?"]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{"text": json.dumps(mock_gemini_json)}]
            }
        }]
    }

    with patch("app.core.config.settings.GEMINI_API_KEY", "mock_valid_key_for_testing"), \
         patch("requests.post", return_value=mock_response):
        payload = {
            "symptoms": ["unsupported_scratchy_throat_feeling"],
            "allow_ai_fallback": True
        }
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["mode"] == "ai_assisted"
        assert "Upper Respiratory" in data["predicted_disease"]
        assert "Honey and warm herbal tea" in data["medications"]
        assert len(data["precautions"]) >= 3
        assert data["confidence"] is None

def test_ai_provider_timeout_handling(client: TestClient):
    """Test 10: AI provider timeout error handling."""
    with patch("app.core.config.settings.GEMINI_API_KEY", "mock_key"), \
         patch("requests.post", side_effect=requests.exceptions.Timeout("Connection timed out")):
        payload = {
            "symptoms": ["unsupported_head_tingling"],
            "allow_ai_fallback": True
        }
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Graceful fallback to rule-based informational response
        assert data["success"] is True
        assert data["mode"] == "fallback"
        assert "not present in our system" in data["description"]

def test_ai_provider_invalid_json_response(client: TestClient):
    """Test 11: Invalid AI responses (malformed JSON returned by provider)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{"text": "THIS IS NOT VALID JSON {malformed"}]
            }
        }]
    }

    with patch("app.core.config.settings.GEMINI_API_KEY", "mock_key"), \
         patch("requests.post", return_value=mock_response):
        payload = {
            "symptoms": ["unsupported_knee_click"],
            "allow_ai_fallback": True
        }
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Graceful fallback
        assert data["success"] is True
        assert data["mode"] == "fallback"
        assert len(data["unrecognized_symptoms"]) == 1
