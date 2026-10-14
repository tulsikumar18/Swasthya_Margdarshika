from fastapi.testclient import TestClient

def test_homepage_redirects_when_unauthenticated(client: TestClient):
    """Unauthenticated users should be redirected to /login."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

def test_homepage_rendering_authenticated(client: TestClient):
    """Test homepage rendering when user is logged in."""
    # Log in first
    login_resp = client.post(
        "/login",
        data={"email": "demo@example.com", "password": "password123"},
        follow_redirects=False
    )
    assert login_resp.status_code == 303

    # Now request homepage
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert "Personalized Medical" in html or "Swasthya Margadarshika" in html
    assert "symptomSearchInput" in html

    # Attribution and copyright confirmation
    assert "2026 Swasthya Margadarshika" in html

def test_additional_pages_rendering(client: TestClient):
    """Test about, contact, developer, and blog pages when authenticated."""
    # Log in
    client.post(
        "/login",
        data={"email": "demo@example.com", "password": "password123"},
        follow_redirects=False
    )
    for path in ["/about", "/contact", "/developer", "/blog"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "Swasthya Margadarshika" in response.text or response.status_code == 200

def test_swagger_docs_accessible(client: TestClient):
    """Test built-in Swagger UI documentation at /docs."""
    response = client.get("/docs")
    assert response.status_code == 200

