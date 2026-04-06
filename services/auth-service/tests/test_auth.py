def test_health_check(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "auth-service"


def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123",
            "name": "Test User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "password": "Password123",
            "name": "Test User",
        },
    )
    assert response.status_code == 422


def test_register_weak_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "weak",
            "name": "Test User",
        },
    )
    assert response.status_code == 400
    assert "at least 8 characters" in response.json()["detail"]


def test_register_duplicate_email(client):
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123",
            "name": "Test User",
        },
    )
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password456",
            "name": "Another User",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client):
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123",
            "name": "Test User",
        },
    )
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Password123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123",
            "name": "Test User",
        },
    )
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123",
        },
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Password123",
        },
    )
    assert response.status_code == 401


def test_get_me_authenticated(client):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123",
            "name": "Test User",
        },
    )
    token = register_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["has_password"] is True
    assert data["oauth_provider"] is None


def test_get_me_unauthenticated(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_refresh_token_success(client):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123",
            "name": "Test User",
        },
    )
    refresh_token = register_response.json()["refresh_token"]

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_invalid(client):
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert response.status_code == 401


def test_github_auth_url():
    from src.services.auth_service import get_github_auth_url
    from src.config import settings

    url = get_github_auth_url()
    assert "github.com/login/oauth/authorize" in url
    assert settings.GITHUB_CLIENT_ID in url
