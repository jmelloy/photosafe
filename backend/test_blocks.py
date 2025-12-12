"""Tests for /photos/blocks endpoint"""

import os
from datetime import datetime
from uuid import uuid4

import pytest
from app.auth import get_password_hash
from app.database import get_db
from app.main import app
from app.models import Photo, User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
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
    yield
    db = TestingSessionLocal()
    db.query(Photo).delete()
    db.query(User).delete()
    db.commit()
    db.close()


def test_photo_blocks_endpoint():
    """Test the /photos/blocks endpoint"""
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

    # Create photos with different dates and labels
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "test1.jpg",
        "date": "2024-01-15T12:00:00",
        "labels": None,  # No labels
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "test2.jpg",
        "date": "2024-01-15T14:00:00",
        "labels": None,  # Also NULL labels (not empty array for SQLite compatibility)
    }
    photo3_data = {
        "uuid": str(uuid4()),
        "original_filename": "test3.jpg",
        "date": "2024-02-10T10:00:00",
        "labels": None,
    }
    photo4_data = {
        "uuid": str(uuid4()),
        "original_filename": "test4.jpg",
        "date": "2024-01-15T16:00:00",
        "labels": ["Outdoor", "Nature"],  # Has labels - should be excluded
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)
    client.post("/api/photos/", json=photo3_data, headers=headers)
    client.post("/api/photos/", json=photo4_data, headers=headers)

    # Get blocks
    response = client.get("/api/photos/blocks", headers=headers)

    assert response.status_code == 200
    blocks = response.json()

    # Verify structure (JSON keys are strings)
    assert "2024" in blocks
    assert "1" in blocks["2024"]
    assert "2" in blocks["2024"]
    assert "15" in blocks["2024"]["1"]
    assert "10" in blocks["2024"]["2"]

    # Verify counts (should only include photos without labels)
    assert blocks["2024"]["1"]["15"]["count"] == 2  # photo1 and photo2, NOT photo4
    assert blocks["2024"]["2"]["10"]["count"] == 1  # photo3

    # Verify max_date exists
    assert "max_date" in blocks["2024"]["1"]["15"]
    assert "max_date" in blocks["2024"]["2"]["10"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
