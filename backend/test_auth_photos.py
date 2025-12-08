"""Tests for authentication and user photo management"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import tempfile

from app.main import app
from app.database import Base, get_db
from app.models import User, Photo


# NOTE: These tests require a PostgreSQL test database
# Test database setup - PostgreSQL connection required
# For local testing, set up a test database: createdb photosafe_test
# Set environment variable: export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/photosafe_test"
# The default below is for Docker Compose development environment only
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://photosafe:photosafe@localhost:5432/photosafe_test",
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables once
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up database between tests"""
    yield
    # Clear all data between tests
    db = TestingSessionLocal()
    try:
        db.query(Photo).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


def test_register_user():
    """Test user registration"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data
    assert data["is_active"] is True


def test_register_duplicate_username():
    """Test registration with duplicate username"""
    # Register first user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # Try to register with same username
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "different@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


def test_login():
    """Test user login"""
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # Login
    response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # Try to login with wrong password
    response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_get_current_user():
    """Test getting current user information"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User",
        },
    )

    login_response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "testpassword123"}
    )
    token = login_response.json()["access_token"]

    # Get current user
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


def test_create_photo_authenticated():
    """Test creating a photo while authenticated"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    login_response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "testpassword123"}
    )
    token = login_response.json()["access_token"]

    # Create photo
    response = client.post(
        "/api/photos/",
        json={
            "uuid": "test-uuid-123",
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["uuid"] == "test-uuid-123"
    assert data["original_filename"] == "test.jpg"


def test_create_photo_unauthenticated():
    """Test that creating a photo without authentication fails"""
    response = client.post(
        "/api/photos/",
        json={
            "uuid": "test-uuid-123",
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
        },
    )
    assert response.status_code == 401


def test_list_photos_only_owned():
    """Test that users only see their own photos"""
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

    # Login as user1 and create a photo
    login1 = client.post(
        "/api/auth/login", data={"username": "user1", "password": "password123"}
    )
    token1 = login1.json()["access_token"]

    client.post(
        "/api/photos/",
        json={
            "uuid": "user1-photo",
            "original_filename": "user1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    # Login as user2 and create a photo
    login2 = client.post(
        "/api/auth/login", data={"username": "user2", "password": "password123"}
    )
    token2 = login2.json()["access_token"]

    client.post(
        "/api/photos/",
        json={
            "uuid": "user2-photo",
            "original_filename": "user2.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token2}"},
    )

    # User1 should only see their photo
    response1 = client.get(
        "/api/photos/", headers={"Authorization": f"Bearer {token1}"}
    )
    assert response1.status_code == 200
    photos1 = response1.json()
    assert len(photos1) == 1
    assert photos1[0]["uuid"] == "user1-photo"

    # User2 should only see their photo
    response2 = client.get(
        "/api/photos/", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response2.status_code == 200
    photos2 = response2.json()
    assert len(photos2) == 1
    assert photos2[0]["uuid"] == "user2-photo"


def test_update_photo_ownership():
    """Test that users can only update their own photos"""
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

    # User1 creates a photo
    login1 = client.post(
        "/api/auth/login", data={"username": "user1", "password": "password123"}
    )
    token1 = login1.json()["access_token"]

    client.post(
        "/api/photos/",
        json={
            "uuid": "user1-photo",
            "original_filename": "user1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User2 tries to update user1's photo
    login2 = client.post(
        "/api/auth/login", data={"username": "user2", "password": "password123"}
    )
    token2 = login2.json()["access_token"]

    response = client.patch(
        "/api/photos/user1-photo/",
        json={"title": "Hacked!"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 403


def test_delete_photo_ownership():
    """Test that users can only delete their own photos"""
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

    # User1 creates a photo
    login1 = client.post(
        "/api/auth/login", data={"username": "user1", "password": "password123"}
    )
    token1 = login1.json()["access_token"]

    client.post(
        "/api/photos/",
        json={
            "uuid": "user1-photo",
            "original_filename": "user1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User2 tries to delete user1's photo
    login2 = client.post(
        "/api/auth/login", data={"username": "user2", "password": "password123"}
    )
    token2 = login2.json()["access_token"]

    response = client.delete(
        "/api/photos/user1-photo/", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 403
