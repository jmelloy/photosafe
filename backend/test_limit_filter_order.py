"""Test to demonstrate the limit/filter order issue"""

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


def test_filter_applied_before_limit():
    """
    Test that filtering is applied BEFORE pagination limit.
    
    Scenario:
    - Create 100 photos
    - 10 photos have keyword "special" 
    - Request first page with page_size=5 and keyword filter
    - Should get 5 photos (out of 10 matching), not 0 photos
    
    Bug: If limit is applied first, it would take first 5 photos (none with "special"),
         then filter would find 0 matches.
    Correct: Filter first (10 photos with "special"), then take first 5.
    """
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

    # Create 100 photos - only the last 10 have keyword "special"
    for i in range(100):
        photo_data = {
            "uuid": str(uuid4()),
            "original_filename": f"photo{i:03d}.jpg",
            "date": f"2024-01-{(i % 30) + 1:02d}T12:00:00",
            "keywords": ["special"] if i >= 90 else ["normal"],
        }
        client.post("/api/photos/", json=photo_data, headers=headers)

    # Request first page with filter - page_size=5, filter by "special"
    response = client.get("/api/photos/?keyword=special&page=1&page_size=5", headers=headers)
    
    assert response.status_code == 200
    result = response.json()
    
    # Should find 5 photos (first page of 10 matching photos)
    print(f"Total matching photos: {result['total']}")
    print(f"Photos returned: {len(result['items'])}")
    print(f"Has more: {result['has_more']}")
    
    assert result["total"] == 10, f"Should have 10 total matching photos, got {result['total']}"
    assert len(result["items"]) == 5, f"Should return 5 photos on first page, got {len(result['items'])}"
    assert result["has_more"] == True, "Should have more pages"
    
    # All returned photos should have "special" keyword
    for photo in result["items"]:
        assert "special" in photo["keywords"], f"Photo {photo['original_filename']} should have 'special' keyword"


def test_filter_with_search_applied_before_limit():
    """
    Test that search filtering is applied BEFORE pagination limit.
    """
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

    # Create 50 photos - only 5 match the search term
    for i in range(50):
        photo_data = {
            "uuid": str(uuid4()),
            "original_filename": f"special_photo.jpg" if i >= 45 else f"normal{i}.jpg",
            "date": f"2024-01-{(i % 30) + 1:02d}T12:00:00",
        }
        client.post("/api/photos/", json=photo_data, headers=headers)

    # Search for "special" with page_size=3
    response = client.get("/api/photos/?search=special&page=1&page_size=3", headers=headers)
    
    assert response.status_code == 200
    result = response.json()
    
    print(f"Total matching photos: {result['total']}")
    print(f"Photos returned: {len(result['items'])}")
    
    assert result["total"] == 5, f"Should have 5 total matching photos, got {result['total']}"
    assert len(result["items"]) == 3, f"Should return 3 photos on first page, got {len(result['items'])}"
    assert result["has_more"] == True, "Should have more pages"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
