"""Tests for photo filtering functionality"""

import os
from datetime import datetime
from uuid import uuid4

import pytest
from app.database import get_db
from app.main import app
from app.models import Photo, User
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


SQLModel.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up database between tests"""
    yield
    db = TestingSessionLocal()
    db.query(Photo).delete()
    db.query(User).delete()
    db.commit()
    db.close()


def test_filter_photos_by_original_filename():
    """Test filtering photos by original_filename (legacy parameter)"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@test.com",
            "password": "testpass123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create photos with different filenames
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "test1.jpg",
        "date": "2024-01-01T00:00:00",
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "test2.jpg",
        "date": "2024-01-02T00:00:00",
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)

    # Filter by search (searches in original_filename)
    response = client.get("/api/photos/?search=test1", headers=headers)

    assert response.status_code == 200
    result = response.json()
    assert "items" in result
    assert len(result["items"]) == 1
    assert result["items"][0]["original_filename"] == "test1.jpg"


def test_filter_photos_by_date():
    """Test filtering photos by date range"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser2",
            "email": "test2@test.com",
            "password": "testpass123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser2", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create photos with different dates
    date1 = "2024-01-01T12:00:00"
    date2 = "2024-01-02T12:00:00"
    date3 = "2024-01-03T12:00:00"

    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo1.jpg",
        "date": date1,
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo2.jpg",
        "date": date2,
    }
    photo3_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo3.jpg",
        "date": date3,
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)
    client.post("/api/photos/", json=photo3_data, headers=headers)

    # Filter by date range
    response = client.get(
        f"/api/photos/?start_date={date1}&end_date={date2}", headers=headers
    )

    assert response.status_code == 200
    result = response.json()
    assert "items" in result
    assert len(result["items"]) == 2
    filenames = [p["original_filename"] for p in result["items"]]
    assert "photo1.jpg" in filenames
    assert "photo2.jpg" in filenames


def test_album_patch_endpoint():
    """Test PATCH endpoint for albums"""
    from app.models import Album

    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser3",
            "email": "test3@test.com",
            "password": "testpass123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser3", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create an album
    album_uuid = str(uuid4())
    album_data = {
        "uuid": album_uuid,
        "title": "Original Title",
        "creation_date": "2024-01-01T00:00:00",
    }

    response = client.post("/api/albums/", json=album_data, headers=headers)
    assert response.status_code == 201

    # Patch the album (partial update)
    patch_data = {"title": "Updated Title"}

    response = client.patch(
        f"/api/albums/{album_uuid}/", json=patch_data, headers=headers
    )
    assert response.status_code == 200

    updated_album = response.json()
    assert updated_album["title"] == "Updated Title"
    assert updated_album["uuid"] == album_uuid
    # creation_date should remain unchanged
    assert updated_album["creation_date"] == "2024-01-01T00:00:00"


def test_filter_photos_by_album():
    """Test filtering photos by album"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser4",
            "email": "test4@test.com",
            "password": "testpass123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser4", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create photos with different albums
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo1.jpg",
        "date": "2024-01-01T00:00:00",
        "albums": ["Vacation", "Beach"],
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo2.jpg",
        "date": "2024-01-02T00:00:00",
        "albums": ["Family"],
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)

    # Filter by album
    response = client.get("/api/photos/?album=Vacation", headers=headers)

    assert response.status_code == 200
    result = response.json()
    assert "items" in result
    assert len(result["items"]) == 1
    assert result["items"][0]["original_filename"] == "photo1.jpg"


def test_filter_photos_by_keyword():
    """Test filtering photos by keyword"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser5",
            "email": "test5@test.com",
            "password": "testpass123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser5", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create photos with different keywords
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo1.jpg",
        "date": "2024-01-01T00:00:00",
        "keywords": ["sunset", "nature"],
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo2.jpg",
        "date": "2024-01-02T00:00:00",
        "keywords": ["portrait"],
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)

    # Filter by keyword
    response = client.get("/api/photos/?keyword=sunset", headers=headers)

    assert response.status_code == 200
    result = response.json()
    assert "items" in result
    assert len(result["items"]) == 1
    assert result["items"][0]["original_filename"] == "photo1.jpg"


def test_filter_photos_by_person():
    """Test filtering photos by person"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser6",
            "email": "test6@test.com",
            "password": "testpass123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser6", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create photos with different persons
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo1.jpg",
        "date": "2024-01-01T00:00:00",
        "persons": ["Alice", "Bob"],
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo2.jpg",
        "date": "2024-01-02T00:00:00",
        "persons": ["Charlie"],
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)

    # Filter by person
    response = client.get("/api/photos/?person=Alice", headers=headers)

    assert response.status_code == 200
    result = response.json()
    assert "items" in result
    assert len(result["items"]) == 1
    assert result["items"][0]["original_filename"] == "photo1.jpg"


def test_get_available_filters():
    """Test getting available filter values"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser7",
            "email": "test7@test.com",
            "password": "testpass123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser7", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create photos with various metadata
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo1.jpg",
        "date": "2024-01-01T00:00:00",
        "albums": ["Vacation", "Beach"],
        "keywords": ["sunset", "nature"],
        "persons": ["Alice", "Bob"],
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo2.jpg",
        "date": "2024-01-02T00:00:00",
        "albums": ["Family"],
        "keywords": ["portrait"],
        "persons": ["Charlie"],
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)

    # Get available filters
    response = client.get("/api/photos/filters/", headers=headers)

    assert response.status_code == 200
    filters = response.json()
    assert "albums" in filters
    assert "keywords" in filters
    assert "persons" in filters

    assert set(filters["albums"]) == {"Beach", "Family", "Vacation"}
    assert set(filters["keywords"]) == {"nature", "portrait", "sunset"}
    assert set(filters["persons"]) == {"Alice", "Bob", "Charlie"}


def test_filter_photos_by_photo_type():
    """Test filtering photos by photo type (favorite, isphoto, etc.)"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser8",
            "email": "test8@test.com",
            "password": "testpass123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser8", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create photos with different types
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo1.jpg",
        "date": "2024-01-01T00:00:00",
        "favorite": True,
        "isphoto": True,
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "video1.mov",
        "date": "2024-01-02T00:00:00",
        "ismovie": True,
    }
    photo3_data = {
        "uuid": str(uuid4()),
        "original_filename": "screenshot1.png",
        "date": "2024-01-03T00:00:00",
        "screenshot": True,
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)
    client.post("/api/photos/", json=photo3_data, headers=headers)

    # Filter by favorite
    response = client.get("/api/photos/?favorite=true", headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert len(result["items"]) == 1
    assert result["items"][0]["original_filename"] == "photo1.jpg"

    # Filter by ismovie
    response = client.get("/api/photos/?ismovie=true", headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert len(result["items"]) == 1
    assert result["items"][0]["original_filename"] == "video1.mov"

    # Filter by screenshot
    response = client.get("/api/photos/?screenshot=true", headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert len(result["items"]) == 1
    assert result["items"][0]["original_filename"] == "screenshot1.png"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
