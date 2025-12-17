"""Tests for authentication and user photo management"""

import os
from datetime import datetime

import pytest
from app.database import get_db
from app.main import app
from app.models import Library, Photo, User, Version, Album, album_photos
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

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
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=Session
)

# Create all tables once
SQLModel.metadata.create_all(bind=engine)


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
    # Clear all data before test
    db = TestingSessionLocal()
    try:
        db.execute(album_photos.delete())
        db.query(Version).delete()
        db.query(Photo).delete()
        db.query(Album).delete()
        db.query(Library).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()

    yield

    # Clear all data after test
    db = TestingSessionLocal()
    try:
        db.execute(album_photos.delete())
        db.query(Version).delete()
        db.query(Photo).delete()
        db.query(Album).delete()
        db.query(Library).delete()
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
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token():
    """Test refreshing access token using refresh token"""
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # Login to get tokens
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "testpassword123"}
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    refresh_token = login_data["refresh_token"]

    # Use refresh token to get new access token
    refresh_response = client.post(
        "/api/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    assert refresh_data["token_type"] == "bearer"

    # Verify the new access token works
    new_access_token = refresh_data["access_token"]
    me_response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "testuser"


def test_refresh_token_invalid():
    """Test refresh with invalid token"""
    response = client.post("/api/auth/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401
    assert "Invalid refresh token" in response.json()["detail"]


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
    photos1 = response1.json()["items"]
    assert len(photos1) == 1
    assert photos1[0]["uuid"] == "user1-photo"

    # User2 should only see their photo
    response2 = client.get(
        "/api/photos/", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response2.status_code == 200
    photos2 = response2.json()["items"]
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


def test_batch_create_photos():
    """Test batch creation of photos"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "batchuser",
            "email": "batch@example.com",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "batchuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]

    # Create batch of photos
    batch_data = {
        "photos": [
            {
                "uuid": "batch-photo-1",
                "original_filename": "photo1.jpg",
                "date": "2024-01-01T00:00:00",
            },
            {
                "uuid": "batch-photo-2",
                "original_filename": "photo2.jpg",
                "date": "2024-01-02T00:00:00",
            },
            {
                "uuid": "batch-photo-3",
                "original_filename": "photo3.jpg",
                "date": "2024-01-03T00:00:00",
            },
        ]
    }

    response = client.post(
        "/api/photos/batch/",
        json=batch_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 3
    assert result["created"] == 3
    assert result["updated"] == 0
    assert result["errors"] == 0
    assert len(result["results"]) == 3

    # Verify all photos were created successfully
    for photo_result in result["results"]:
        assert photo_result["success"] is True
        assert photo_result["action"] == "created"

    # Verify photos exist in database
    photos_response = client.get(
        "/api/photos/", headers={"Authorization": f"Bearer {token}"}
    )
    photos = photos_response.json()["items"]
    assert len(photos) == 3


def test_batch_update_photos():
    """Test batch update of existing photos"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "updateuser",
            "email": "update@example.com",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "updateuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]

    # Create initial photos
    for i in range(1, 4):
        client.post(
            "/api/photos/",
            json={
                "uuid": f"update-photo-{i}",
                "original_filename": f"photo{i}.jpg",
                "date": f"2024-01-0{i}T00:00:00",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    # Update via batch
    batch_data = {
        "photos": [
            {
                "uuid": "update-photo-1",
                "original_filename": "photo1.jpg",
                "date": "2024-01-01T00:00:00",
                "title": "Updated Photo 1",
                "favorite": True,
            },
            {
                "uuid": "update-photo-2",
                "original_filename": "photo2.jpg",
                "date": "2024-01-02T00:00:00",
                "title": "Updated Photo 2",
            },
        ]
    }

    response = client.post(
        "/api/photos/batch/",
        json=batch_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 2
    assert result["created"] == 0
    assert result["updated"] == 2
    assert result["errors"] == 0

    # Verify updates were applied
    photo1 = client.get(
        "/api/photos/update-photo-1/", headers={"Authorization": f"Bearer {token}"}
    )
    assert photo1.json()["title"] == "Updated Photo 1"
    assert photo1.json()["favorite"] is True


def test_batch_mixed_create_and_update():
    """Test batch with both new and existing photos"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "mixeduser",
            "email": "mixed@example.com",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "mixeduser", "password": "password123"}
    )
    token = login_response.json()["access_token"]

    # Create one photo first
    client.post(
        "/api/photos/",
        json={
            "uuid": "existing-photo",
            "original_filename": "existing.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Batch with mix of new and existing
    batch_data = {
        "photos": [
            {
                "uuid": "existing-photo",
                "original_filename": "existing.jpg",
                "date": "2024-01-01T00:00:00",
                "title": "Updated",
            },
            {
                "uuid": "new-photo-1",
                "original_filename": "new1.jpg",
                "date": "2024-01-02T00:00:00",
            },
            {
                "uuid": "new-photo-2",
                "original_filename": "new2.jpg",
                "date": "2024-01-03T00:00:00",
            },
        ]
    }

    response = client.post(
        "/api/photos/batch/",
        json=batch_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 3
    assert result["created"] == 2
    assert result["updated"] == 1
    assert result["errors"] == 0


def test_batch_unauthenticated():
    """Test batch endpoint requires authentication"""
    batch_data = {
        "photos": [
            {
                "uuid": "test-photo",
                "original_filename": "test.jpg",
                "date": "2024-01-01T00:00:00",
            }
        ]
    }

    response = client.post("/api/photos/batch/", json=batch_data)
    assert response.status_code == 401


def test_get_photo():
    """Test retrieving a specific photo by UUID"""
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

    # Create a photo
    create_response = client.post(
        "/api/photos/",
        json={
            "uuid": "test-photo-uuid",
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
            "title": "Test Photo",
            "description": "This is a test photo",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201

    # Get the photo
    response = client.get(
        "/api/photos/test-photo-uuid/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == "test-photo-uuid"
    assert data["original_filename"] == "test.jpg"
    assert data["title"] == "Test Photo"


def test_get_photo_not_found():
    """Test getting a non-existent photo returns 404"""
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

    response = client.get(
        "/api/photos/nonexistent-uuid/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_get_photo_unauthorized():
    """Test getting another user's photo is forbidden"""
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

    # Login as user1
    login1 = client.post(
        "/api/auth/login", data={"username": "user1", "password": "password123"}
    )
    token1 = login1.json()["access_token"]

    # Login as user2
    login2 = client.post(
        "/api/auth/login", data={"username": "user2", "password": "password123"}
    )
    token2 = login2.json()["access_token"]

    # User1 creates a photo
    client.post(
        "/api/photos/",
        json={
            "uuid": "user1-photo",
            "original_filename": "user1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User2 tries to get user1's photo
    response = client.get(
        "/api/photos/user1-photo/",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 403


def test_upload_photo():
    """Test uploading a photo file"""
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

    # Create a fake image file
    file_content = b"fake image content"
    files = {"file": ("test.jpg", file_content, "image/jpeg")}

    response = client.post(
        "/api/photos/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "uuid" in data
    assert data["original_filename"] == "test.jpg"
    assert data["content_type"] == "image/jpeg"


def test_upload_photo_invalid_type():
    """Test uploading a non-image file fails"""
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

    # Create a non-image file
    file_content = b"not an image"
    files = {"file": ("test.txt", file_content, "text/plain")}

    response = client.post(
        "/api/photos/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "must be an image" in response.json()["detail"]


def test_upload_photo_unauthenticated():
    """Test uploading without authentication fails"""
    file_content = b"fake image content"
    files = {"file": ("test.jpg", file_content, "image/jpeg")}

    response = client.post("/api/photos/upload", files=files)
    assert response.status_code == 401
