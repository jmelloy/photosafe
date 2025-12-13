"""Inspect the actual SQL generated for filtering"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel
from app.models import Photo, User
from app.database import get_db
from app.main import app
from fastapi.testclient import TestClient
from uuid import uuid4

# Test database setup
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://photosafe:photosafe@localhost:5432/photosafe_test",
)
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)  # echo=True to see SQL
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


def test_inspect_filter_sql():
    """Inspect the actual SQL query generated"""
    # Clean database
    db = TestingSessionLocal()
    try:
        from app.models import album_photos, Version, Album, Library
        db.execute(album_photos.delete())
        db.query(Version).delete()
        db.query(Photo).delete()
        db.query(Album).delete()
        db.query(Library).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    
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

    # Create 20 photos
    for i in range(20):
        photo_data = {
            "uuid": str(uuid4()),
            "original_filename": f"photo{i:03d}.jpg",
            "date": f"2024-01-01T12:00:00",
            "keywords": ["special"] if i >= 15 else ["normal"],
        }
        client.post("/api/photos/", json=photo_data, headers=headers)

    print("\n\n========== MAKING FILTERED REQUEST ==========")
    # This should print the SQL query with filters applied BEFORE limit
    response = client.get("/api/photos/?keyword=special&page=1&page_size=3", headers=headers)
    print("========== END OF REQUEST ==========\n\n")
    
    result = response.json()
    print(f"Total matching photos: {result['total']}")
    print(f"Photos returned: {len(result['items'])}")
    assert result["total"] == 5, f"Expected 5, got {result['total']}"
    assert len(result["items"]) == 3, f"Expected 3, got {len(result['items'])}"


if __name__ == "__main__":
    test_inspect_filter_sql()
