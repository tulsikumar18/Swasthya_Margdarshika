from fastapi.testclient import TestClient

def test_natural_language_symptom_extraction(client: TestClient):
    """Test extracting symptoms from conversational sentence."""
    text = "i am feeling like stomach , ache, then headache , then vomiting , etc, etc"
    response = client.post("/api/symptoms/extract", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    extracted_keys = data["extracted_keys"]
    assert "stomach_pain" in extracted_keys
    assert "headache" in extracted_keys
    assert "vomiting" in extracted_keys
    assert len(data["extracted_symptoms"]) >= 3
    assert "We identified" in data["confirmation_message"]

def test_comma_separated_symptoms_predict_gerd(client: TestClient):
    """Test row 25 GERD symptoms: stomach_pain, acidity, ulcers_on_tongue, vomiting."""
    payload = {
        "symptoms": ["stomach_pain, acidity, ulcers_on_tongue, vomiting"]
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["mode"] == "ml_prediction"
    assert data["predicted_disease"] == "GERD"
    assert len(data["medications"]) > 0
    assert len(data["precautions"]) > 0

def test_login_and_logout_flow(client: TestClient):
    """Test GET /login, POST /login with demo credentials, session cookie, and logout."""
    # 1. View login page
    res = client.get("/login")
    assert res.status_code == 200
    assert "Sign In" in res.text

    # 2. Login with demo user
    login_res = client.post(
        "/login",
        data={"email": "demo@example.com", "password": "password123", "next_url": "/profile"},
        follow_redirects=True
    )
    assert login_res.status_code == 200
    assert "Demo User" in login_res.text or "Profile" in login_res.text

    # 3. View profile while logged in
    prof_res = client.get("/profile")
    assert prof_res.status_code == 200
    assert "demo@example.com" in prof_res.text

    # 4. Logout
    logout_res = client.get("/logout", follow_redirects=True)
    assert logout_res.status_code == 200
    assert "Welcome Back" in logout_res.text

def test_registration_flow(client: TestClient):
    """Test user registration redirects to the homepage after success."""
    reg_res = client.post(
        "/register",
        data={
            "firstName": "Alice",
            "lastName": "Smith",
            "email": "alice@example.com",
            "password": "securepassword",
            "confirmPassword": "securepassword",
            "next_url": "/"
        },
        follow_redirects=True
    )
    assert reg_res.status_code == 200
    # After registration the user is redirected to the homepage;
    # the navbar no longer renders the user's name, so we assert on
    # stable page content instead.
    assert "Symptom Checker" in reg_res.text or "Swasthya Margadarshika" in reg_res.text
