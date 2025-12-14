"""Tests for library upsert functionality in photo PATCH endpoint"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

from app.main import app
from app.database import get_db
from app.models import User, Photo, Library, Version, Album, album_photos
from sqlmodel import Session, SQLModel


# Test database setup
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://photosafe:photosafe@localhost:5432/photosafe_test",
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=Session
)

# Create all tables
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
    db = TestingSessionLocal()
    try:
        # Clean up in correct order due to foreign keys
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


def test_patch_photo_creates_library_if_not_exists():
    """Test that patching a photo with a library name creates the library if it doesn't exist"""
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

    # Create a photo without library
    response = client.post(
        "/api/photos/",
        json={
            "uuid": "test-photo-123",
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    # Verify no libraries exist yet
    db = TestingSessionLocal()
    try:
        libraries = db.query(Library).all()
        assert len(libraries) == 0
    finally:
        db.close()

    # Patch the photo with a library name
    patch_response = client.patch(
        "/api/photos/test-photo-123/",
        json={"library": "My Photos"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch_response.status_code == 200

    # Verify library was created
    db = TestingSessionLocal()
    try:
        libraries = db.query(Library).all()
        assert len(libraries) == 1
        assert libraries[0].name == "My Photos"

        # Verify photo has library_id set
        photo = db.query(Photo).filter(Photo.uuid == "test-photo-123").first()
        assert photo is not None
        assert photo.library_id == libraries[0].id
        assert photo.library == "My Photos"
    finally:
        db.close()


def test_patch_photo_reuses_existing_library():
    """Test that patching a photo with an existing library name reuses the library"""
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

    # Create first photo with library
    client.post(
        "/api/photos/",
        json={
            "uuid": "photo-1",
            "original_filename": "test1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    client.patch(
        "/api/photos/photo-1/",
        json={"library": "My Photos"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Create second photo
    client.post(
        "/api/photos/",
        json={
            "uuid": "photo-2",
            "original_filename": "test2.jpg",
            "date": "2024-01-02T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Patch second photo with same library name
    client.patch(
        "/api/photos/photo-2/",
        json={"library": "My Photos"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Verify only one library was created
    db = TestingSessionLocal()
    try:
        libraries = db.query(Library).all()
        assert len(libraries) == 1
        assert libraries[0].name == "My Photos"

        # Verify both photos reference the same library
        photo1 = db.query(Photo).filter(Photo.uuid == "photo-1").first()
        photo2 = db.query(Photo).filter(Photo.uuid == "photo-2").first()
        assert photo1.library_id == libraries[0].id
        assert photo2.library_id == libraries[0].id
    finally:
        db.close()


def test_patch_photo_library_user_isolation():
    """Test that libraries are isolated per user"""
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

    # User1 creates a photo with library
    client.post(
        "/api/photos/",
        json={
            "uuid": "user1-photo",
            "original_filename": "user1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    client.patch(
        "/api/photos/user1-photo/",
        json={"library": "Shared Name"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User2 creates a photo with same library name
    client.post(
        "/api/photos/",
        json={
            "uuid": "user2-photo",
            "original_filename": "user2.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token2}"},
    )
    client.patch(
        "/api/photos/user2-photo/",
        json={"library": "Shared Name"},
        headers={"Authorization": f"Bearer {token2}"},
    )

    # Verify two separate libraries were created (one per user)
    db = TestingSessionLocal()
    try:
        libraries = db.query(Library).all()
        assert len(libraries) == 2

        # Get user IDs
        user1 = db.query(User).filter(User.username == "user1").first()
        user2 = db.query(User).filter(User.username == "user2").first()

        # Verify each user has their own library
        user1_libs = db.query(Library).filter(Library.owner_id == user1.id).all()
        user2_libs = db.query(Library).filter(Library.owner_id == user2.id).all()
        assert len(user1_libs) == 1
        assert len(user2_libs) == 1
        assert user1_libs[0].name == "Shared Name"
        assert user2_libs[0].name == "Shared Name"
        assert user1_libs[0].id != user2_libs[0].id
    finally:
        db.close()


def test_patch_photo_without_library_no_change():
    """Test that patching a photo without library field doesn't affect library"""
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
    client.post(
        "/api/photos/",
        json={
            "uuid": "test-photo",
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Patch with other fields but no library
    client.patch(
        "/api/photos/test-photo/",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Verify no libraries were created
    db = TestingSessionLocal()
    try:
        libraries = db.query(Library).all()
        assert len(libraries) == 0

        # Verify photo title was updated
        photo = db.query(Photo).filter(Photo.uuid == "test-photo").first()
        assert photo.title == "Updated Title"
        assert photo.library_id is None
    finally:
        db.close()
