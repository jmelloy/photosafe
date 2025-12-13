"""Test that the filters endpoint respects active filters"""

import os
from datetime import datetime
from uuid import uuid4

import pytest
from app.database import get_db
from app.main import app
from app.models import Photo, User, Version, Album, Library, album_photos
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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


def test_filters_endpoint_without_filters():
    """Test that filters endpoint returns all filter values when no filters applied"""
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

    # Create photos with different albums and keywords
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo1.jpg",
        "date": "2024-01-01T00:00:00",
        "albums": ["Vacation"],
        "keywords": ["beach", "summer"],
        "persons": ["Alice"],
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo2.jpg",
        "date": "2024-01-02T00:00:00",
        "albums": ["Work"],
        "keywords": ["meeting", "office"],
        "persons": ["Bob"],
    }
    photo3_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo3.jpg",
        "date": "2024-01-03T00:00:00",
        "albums": ["Family"],
        "keywords": ["home", "party"],
        "persons": ["Charlie"],
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)
    client.post("/api/photos/", json=photo3_data, headers=headers)

    # Get available filters without any filter parameters
    response = client.get("/api/photos/filters/", headers=headers)
    
    assert response.status_code == 200
    result = response.json()
    
    # Should see all albums, keywords, and persons
    assert set(result["albums"]) == {"Vacation", "Work", "Family"}
    assert set(result["keywords"]) == {"beach", "summer", "meeting", "office", "home", "party"}
    assert set(result["persons"]) == {"Alice", "Bob", "Charlie"}


def test_filters_endpoint_with_album_filter():
    """Test that filters endpoint returns only values from photos matching the album filter"""
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

    # Create photos with different albums and keywords
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo1.jpg",
        "date": "2024-01-01T00:00:00",
        "albums": ["Vacation", "Summer"],
        "keywords": ["beach", "sun"],
        "persons": ["Alice"],
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo2.jpg",
        "date": "2024-01-02T00:00:00",
        "albums": ["Vacation", "Beach"],
        "keywords": ["ocean", "sand"],
        "persons": ["Bob"],
    }
    photo3_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo3.jpg",
        "date": "2024-01-03T00:00:00",
        "albums": ["Work"],
        "keywords": ["meeting"],
        "persons": ["Charlie"],
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)
    client.post("/api/photos/", json=photo3_data, headers=headers)

    # Get available filters with album=Vacation filter
    response = client.get("/api/photos/filters/?album=Vacation", headers=headers)
    
    assert response.status_code == 200
    result = response.json()
    
    # Should only see albums/keywords/persons from photos in "Vacation" album
    # Photo3 should be excluded
    assert "Work" not in result["albums"]
    assert "meeting" not in result["keywords"]
    assert "Charlie" not in result["persons"]
    
    # Should see values from photo1 and photo2
    assert "Summer" in result["albums"]
    assert "Beach" in result["albums"]
    assert set(result["keywords"]) == {"beach", "sun", "ocean", "sand"}
    assert set(result["persons"]) == {"Alice", "Bob"}


def test_filters_endpoint_with_keyword_filter():
    """Test that filters endpoint returns only values from photos matching the keyword filter"""
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

    # Create photos with different keywords
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo1.jpg",
        "date": "2024-01-01T00:00:00",
        "albums": ["Nature"],
        "keywords": ["sunset", "landscape"],
        "persons": ["Alice"],
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo2.jpg",
        "date": "2024-01-02T00:00:00",
        "albums": ["Nature"],
        "keywords": ["sunset", "ocean"],
        "persons": ["Bob"],
    }
    photo3_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo3.jpg",
        "date": "2024-01-03T00:00:00",
        "albums": ["Urban"],
        "keywords": ["city", "architecture"],
        "persons": ["Charlie"],
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)
    client.post("/api/photos/", json=photo3_data, headers=headers)

    # Get available filters with keyword=sunset filter
    response = client.get("/api/photos/filters/?keyword=sunset", headers=headers)
    
    assert response.status_code == 200
    result = response.json()
    
    # Should only see values from photos with "sunset" keyword
    assert "Urban" not in result["albums"]
    assert "city" not in result["keywords"]
    assert "architecture" not in result["keywords"]
    assert "Charlie" not in result["persons"]
    
    # Should see values from photo1 and photo2
    assert set(result["albums"]) == {"Nature"}
    assert set(result["keywords"]) == {"sunset", "landscape", "ocean"}
    assert set(result["persons"]) == {"Alice", "Bob"}


def test_filters_endpoint_with_search_filter():
    """Test that filters endpoint returns only values from photos matching the search filter"""
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

    # Create photos with different filenames
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "sunset_beach.jpg",
        "date": "2024-01-01T00:00:00",
        "albums": ["Vacation"],
        "keywords": ["beach"],
        "persons": ["Alice"],
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "sunset_mountain.jpg",
        "date": "2024-01-02T00:00:00",
        "albums": ["Trip"],
        "keywords": ["mountain"],
        "persons": ["Bob"],
    }
    photo3_data = {
        "uuid": str(uuid4()),
        "original_filename": "city_night.jpg",
        "date": "2024-01-03T00:00:00",
        "albums": ["Urban"],
        "keywords": ["city"],
        "persons": ["Charlie"],
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)
    client.post("/api/photos/", json=photo3_data, headers=headers)

    # Get available filters with search=sunset filter
    response = client.get("/api/photos/filters/?search=sunset", headers=headers)
    
    assert response.status_code == 200
    result = response.json()
    
    # Should only see values from photos with "sunset" in filename
    assert "Urban" not in result["albums"]
    assert "city" not in result["keywords"]
    assert "Charlie" not in result["persons"]
    
    # Should see values from photo1 and photo2
    assert set(result["albums"]) == {"Vacation", "Trip"}
    assert set(result["keywords"]) == {"beach", "mountain"}
    assert set(result["persons"]) == {"Alice", "Bob"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
