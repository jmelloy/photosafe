"""Tests for pagination and filtering functionality"""

import os
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from app.database import get_db
from app.main import app
from app.models import Library, Photo, User, Version, Album, album_photos
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

# Test database setup - PostgreSQL connection required
# For local testing, set TEST_DATABASE_URL environment variable:
# export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/photosafe_test"
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


def test_pagination_with_100_photos():
    """Test that pagination works correctly with 100 photos"""
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

    # Create 100 photos with different dates
    base_date = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(100):
        photo_data = {
            "uuid": str(uuid4()),
            "original_filename": f"photo{i:03d}.jpg",
            "date": (base_date + timedelta(days=i)).isoformat(),
        }
        response = client.post("/api/photos/", json=photo_data, headers=headers)
        assert response.status_code == 201, f"Failed to create photo {i}: {response.text}"

    # Test page 1 - should return 50 photos with has_more=True
    response = client.get("/api/photos/?page=1&page_size=50", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 50
    assert data["total"] == 100
    assert data["page"] == 1
    assert data["page_size"] == 50
    assert data["has_more"] is True
    
    # Most recent photos first (ordered by date desc)
    assert data["items"][0]["original_filename"] == "photo099.jpg"
    assert data["items"][49]["original_filename"] == "photo050.jpg"

    # Test page 2 - should return 50 photos with has_more=False
    response = client.get("/api/photos/?page=2&page_size=50", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 50
    assert data["total"] == 100
    assert data["page"] == 2
    assert data["page_size"] == 50
    assert data["has_more"] is False
    
    # Remaining photos
    assert data["items"][0]["original_filename"] == "photo049.jpg"
    assert data["items"][49]["original_filename"] == "photo000.jpg"

    # Test page 3 - should return empty array with has_more=False
    response = client.get("/api/photos/?page=3&page_size=50", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0
    assert data["total"] == 100
    assert data["page"] == 3
    assert data["page_size"] == 50
    assert data["has_more"] is False


def test_filters_endpoint_returns_all_values():
    """Test that /api/photos/filters/ returns values from ALL photos, not just paginated subset"""
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

    # Create 100 photos with different albums, keywords, and persons
    # Spread them across to ensure they span multiple pages
    base_date = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(100):
        photo_data = {
            "uuid": str(uuid4()),
            "original_filename": f"photo{i:03d}.jpg",
            "date": (base_date + timedelta(days=i)).isoformat(),
            "albums": [f"Album{i % 10}"],  # 10 different albums
            "keywords": [f"Keyword{i % 20}"],  # 20 different keywords
            "persons": [f"Person{i % 15}"],  # 15 different persons
        }
        response = client.post("/api/photos/", json=photo_data, headers=headers)
        assert response.status_code == 201, f"Failed to create photo {i}: {response.text}"

    # Get available filters - should return ALL unique values
    response = client.get("/api/photos/filters/", headers=headers)
    assert response.status_code == 200
    filters = response.json()
    
    # Should have all 10 albums, 20 keywords, and 15 persons
    assert len(filters["albums"]) == 10
    assert len(filters["keywords"]) == 20
    assert len(filters["persons"]) == 15
    
    # Verify some specific values
    assert "Album0" in filters["albums"]
    assert "Album9" in filters["albums"]
    assert "Keyword0" in filters["keywords"]
    assert "Keyword19" in filters["keywords"]
    assert "Person0" in filters["persons"]
    assert "Person14" in filters["persons"]


def test_filtering_with_pagination():
    """Test that filtering works correctly across paginated results"""
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

    # Create 100 photos - 60 in "Vacation" album, 40 in "Family" album
    base_date = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(100):
        album = "Vacation" if i < 60 else "Family"
        photo_data = {
            "uuid": str(uuid4()),
            "original_filename": f"photo{i:03d}.jpg",
            "date": (base_date + timedelta(days=i)).isoformat(),
            "albums": [album],
        }
        response = client.post("/api/photos/", json=photo_data, headers=headers)
        assert response.status_code == 201

    # Filter by "Vacation" album - should return 60 photos total
    # Page 1: 50 photos
    response = client.get("/api/photos/?page=1&page_size=50&album=Vacation", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 50
    assert data["total"] == 60
    assert data["has_more"] is True
    
    # All should be from Vacation album
    for photo in data["items"]:
        assert "Vacation" in photo["albums"]

    # Page 2: 10 photos
    response = client.get("/api/photos/?page=2&page_size=50&album=Vacation", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 60
    assert data["has_more"] is False
    
    # All should be from Vacation album
    for photo in data["items"]:
        assert "Vacation" in photo["albums"]

    # Filter by "Family" album - should return 40 photos (all on one page)
    response = client.get("/api/photos/?page=1&page_size=50&album=Family", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 40
    assert data["total"] == 40
    assert data["has_more"] is False
    
    # All should be from Family album
    for photo in data["items"]:
        assert "Family" in photo["albums"]


def test_filters_endpoint_with_no_photos():
    """Test that /api/photos/filters/ returns empty lists when there are no photos"""
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

    # Get available filters - should return empty lists
    response = client.get("/api/photos/filters/", headers=headers)
    assert response.status_code == 200
    filters = response.json()
    
    assert filters["albums"] == []
    assert filters["keywords"] == []
    assert filters["persons"] == []
