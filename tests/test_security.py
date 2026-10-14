import os
from fastapi.testclient import TestClient
from app.core.config import settings

def test_credentials_not_returned_in_api_responses(client: TestClient):
    """Test 16: Confirmation that credentials are not returned in any API responses."""
    endpoints = [
        ("GET", "/api/health"),
        ("GET", "/api/symptoms"),
        ("POST", "/api/predict", {"symptoms": ["itching", "skin_rash"]}),
        ("POST", "/api/predict", {"symptoms": ["unknown_xyz_symptom"]}),
    ]

    sensitive_tokens = [
        settings.SECRET_KEY,
        settings.GEMINI_API_KEY,
        "AIzaSy",
        "secret_key"
    ]

    for item in endpoints:
        method = item[0]
        url = item[1]
        payload = item[2] if len(item) > 2 else None

        if method == "GET":
            res = client.get(url)
        else:
            res = client.post(url, json=payload)

        res_text = res.text
        for token in sensitive_tokens:
            if token and len(token) > 5:
                assert token not in res_text, f"Sensitive token found in response for {url}"

def test_model_registry_missing_file_handling():
    """Test 14: Missing model or dataset file handling."""
    from app.ml.model_loader import ModelRegistry
    from unittest.mock import patch
    from pathlib import Path

    reg = ModelRegistry()
    nonexistent = Path("/nonexistent/path/to/svc.pkl")
    with patch.object(settings, "MODEL_PATH", nonexistent), \
         patch.object(settings, "CHECKPOINT_MODEL_PATH", nonexistent):
        try:
            reg.load_all()
        except FileNotFoundError:
            pass  # Expected behavior
        assert reg.is_loaded is False or reg.load_error is not None
