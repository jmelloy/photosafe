"""Tests for Personal Access Token functionality"""

from datetime import datetime, timedelta, timezone


def test_create_personal_access_token(client, test_user):
    """Test creating a Personal Access Token via API"""
    # Login to get auth token
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"},
    )
    jwt_token = login_response.json()["access_token"]

    # Create PAT
    response = client.post(
        "/api/auth/tokens",
        json={"name": "Test Token"},
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Token"
    assert "token" in data
    assert "id" in data
    assert data["user_id"] == test_user.id
    assert data["expires_at"] is None  # No expiration set

    # Token should be a string
    token = data["token"]
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_personal_access_token_with_expiration(client, test_user):
    """Test creating a PAT with expiration"""
    # Login
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"},
    )
    jwt_token = login_response.json()["access_token"]

    # Create PAT with 30 day expiration
    response = client.post(
        "/api/auth/tokens",
        json={"name": "Expiring Token", "expires_in_days": 30},
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["expires_at"] is not None

    # Check expiration is approximately 30 days from now
    # Parse ISO timestamp and ensure it's timezone-aware
    expires_at_str = data["expires_at"].replace("Z", "").replace("+00:00", "")
    expires_at = datetime.fromisoformat(expires_at_str).replace(tzinfo=timezone.utc)
    expected_expiry = datetime.now(timezone.utc) + timedelta(days=30)
    time_diff = abs((expires_at - expected_expiry).total_seconds())
    assert time_diff < 60  # Within 1 minute


def test_authenticate_with_personal_access_token(client, test_user):
    """Test using a PAT to authenticate API requests"""
    # Login to create PAT
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"},
    )
    jwt_token = login_response.json()["access_token"]

    # Create PAT
    pat_response = client.post(
        "/api/auth/tokens",
        json={"name": "API Token"},
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    pat_token = pat_response.json()["token"]

    # Use PAT to authenticate
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {pat_token}"},
    )

    assert me_response.status_code == 200
    data = me_response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_pat_works_for_protected_endpoints(client, test_user):
    """Test that PAT works for accessing photos and other protected resources"""
    # Login to create PAT
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"},
    )
    jwt_token = login_response.json()["access_token"]

    # Create PAT
    pat_response = client.post(
        "/api/auth/tokens",
        json={"name": "Photo Access Token"},
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    pat_token = pat_response.json()["token"]

    # Create a photo using JWT
    photo_response = client.post(
        "/api/photos/",
        json={
            "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    assert photo_response.status_code == 201

    # List photos using PAT
    photos_response = client.get(
        "/api/photos/",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert photos_response.status_code == 200
    photos = photos_response.json()["items"]
    assert len(photos) == 1
    assert photos[0]["uuid"] == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def test_list_personal_access_tokens(client, test_user):
    """Test listing all PATs for a user"""
    # Login
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"},
    )
    jwt_token = login_response.json()["access_token"]

    # Create multiple PATs
    client.post(
        "/api/auth/tokens",
        json={"name": "Token 1"},
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    client.post(
        "/api/auth/tokens",
        json={"name": "Token 2"},
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

    # List tokens
    response = client.get(
        "/api/auth/tokens",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

    assert response.status_code == 200
    tokens = response.json()
    assert len(tokens) == 2
    assert tokens[0]["name"] == "Token 1"
    assert tokens[1]["name"] == "Token 2"

    # Token values should not be in the list response
    assert "token" not in tokens[0]
    assert "token" not in tokens[1]


def test_revoke_personal_access_token(client, test_user):
    """Test revoking a PAT"""
    # Login
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"},
    )
    jwt_token = login_response.json()["access_token"]

    # Create PAT
    pat_response = client.post(
        "/api/auth/tokens",
        json={"name": "Revoke Me"},
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    token_id = pat_response.json()["id"]
    pat_token = pat_response.json()["token"]

    # Verify PAT works
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert me_response.status_code == 200

    # Revoke PAT
    revoke_response = client.delete(
        f"/api/auth/tokens/{token_id}",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    assert revoke_response.status_code == 204

    # Verify PAT no longer works
    me_response2 = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert me_response2.status_code == 401


def test_cannot_revoke_other_users_token(client):
    """Test that users can only revoke their own tokens"""
    # Create two users
    client.post(
        "/api/auth/register",
        json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123",
        },
    )
    client.post(
        "/api/auth/register",
        json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123",
        },
    )

    # User1 creates a token
    login1 = client.post(
        "/api/auth/login",
        data={"username": "user1", "password": "password123"},
    )
    token1 = login1.json()["access_token"]

    pat_response = client.post(
        "/api/auth/tokens",
        json={"name": "User1 Token"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    token_id = pat_response.json()["id"]

    # User2 tries to revoke user1's token
    login2 = client.post(
        "/api/auth/login",
        data={"username": "user2", "password": "password123"},
    )
    token2 = login2.json()["access_token"]

    revoke_response = client.delete(
        f"/api/auth/tokens/{token_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert revoke_response.status_code == 404


def test_invalid_pat_returns_401(client):
    """Test that an invalid PAT returns 401"""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"},
    )
    assert response.status_code == 401


def test_pat_unauthenticated_creation(client):
    """Test that creating a PAT requires authentication"""
    response = client.post(
        "/api/auth/tokens",
        json={"name": "Test Token"},
    )
    assert response.status_code == 401


def test_cli_create_token(runner, test_user):
    """Test creating a PAT via CLI"""
    from cli.main import cli

    result = runner.invoke(
        cli,
        ["user", "create-token", "testuser", "--name", "CLI Token"],
    )

    assert result.exit_code == 0
    assert "Personal Access Token created successfully" in result.output
    assert "Token:" in result.output
    assert "WARNING" in result.output


def test_cli_list_tokens(runner, test_user, db_session):
    """Test listing PATs via CLI"""
    from cli.main import cli
    from app.auth import create_personal_access_token

    # Create some tokens
    create_personal_access_token(db_session, test_user, "Token 1", None)
    create_personal_access_token(db_session, test_user, "Token 2", 30)

    result = runner.invoke(cli, ["user", "list-tokens", "testuser"])

    assert result.exit_code == 0
    assert "Token 1" in result.output
    assert "Token 2" in result.output


def test_cli_revoke_token(runner, test_user, db_session):
    """Test revoking a PAT via CLI"""
    from cli.main import cli
    from app.auth import create_personal_access_token

    # Create token
    pat, _ = create_personal_access_token(db_session, test_user, "Revoke Me", None)

    result = runner.invoke(
        cli,
        ["user", "revoke-token", "testuser", str(pat.id)],
        input="y\n",
    )

    assert result.exit_code == 0
    assert "revoked successfully" in result.output
