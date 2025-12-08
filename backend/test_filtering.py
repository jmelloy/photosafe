"""Tests for photo filtering functionality"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
from uuid import uuid4

from app.main import app
from app.database import Base, get_db
from app.models import User, Photo
from app.auth import get_password_hash


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


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
    """Test filtering photos by original_filename"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={"username": "testuser", "email": "test@test.com", "password": "testpass123"}
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create photos with different filenames
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "test1.jpg",
        "date": "2024-01-01T00:00:00"
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "test2.jpg",
        "date": "2024-01-02T00:00:00"
    }
    
    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)
    
    # Filter by original_filename
    response = client.get(
        "/api/photos/?original_filename=test1.jpg",
        headers=headers
    )
    
    assert response.status_code == 200
    photos = response.json()
    assert len(photos) == 1
    assert photos[0]["original_filename"] == "test1.jpg"


def test_filter_photos_by_date():
    """Test filtering photos by date"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={"username": "testuser2", "email": "test2@test.com", "password": "testpass123"}
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser2", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create photos with different dates
    date1 = "2024-01-01T12:00:00"
    date2 = "2024-01-02T12:00:00"
    
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo1.jpg",
        "date": date1
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "photo2.jpg",
        "date": date2
    }
    
    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)
    
    # Filter by date
    response = client.get(
        f"/api/photos/?date={date1}",
        headers=headers
    )
    
    assert response.status_code == 200
    photos = response.json()
    assert len(photos) == 1
    assert photos[0]["date"] == date1


def test_album_patch_endpoint():
    """Test PATCH endpoint for albums"""
    from app.models import Album
    
    # Register and login
    client.post(
        "/api/auth/register",
        json={"username": "testuser3", "email": "test3@test.com", "password": "testpass123"}
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser3", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create an album
    album_uuid = str(uuid4())
    album_data = {
        "uuid": album_uuid,
        "title": "Original Title",
        "creation_date": "2024-01-01T00:00:00"
    }
    
    response = client.post("/api/albums/", json=album_data, headers=headers)
    assert response.status_code == 201
    
    # Patch the album (partial update)
    patch_data = {
        "title": "Updated Title"
    }
    
    response = client.patch(f"/api/albums/{album_uuid}/", json=patch_data, headers=headers)
    assert response.status_code == 200
    
    updated_album = response.json()
    assert updated_album["title"] == "Updated Title"
    assert updated_album["uuid"] == album_uuid
    # creation_date should remain unchanged
    assert updated_album["creation_date"] == "2024-01-01T00:00:00"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
