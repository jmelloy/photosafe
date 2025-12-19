"""Tests for album API endpoints"""

import os
import uuid

import pytest
from app.database import get_db
from app.main import app
from app.models import Library, Photo, User, Version, Album, album_photos
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session

# Test database setup - PostgreSQL connection required
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
        db.exec(delete(Version))
        db.exec(delete(Photo))
        db.exec(delete(Album))
        db.exec(delete(Library))
        db.exec(delete(User))
        db.commit()
    finally:
        db.close()

    yield

    # Clear all data after test
    db = TestingSessionLocal()
    try:
        db.execute(album_photos.delete())
        db.exec(delete(Version))
        db.exec(delete(Photo))
        db.exec(delete(Album))
        db.exec(delete(Library))
        db.exec(delete(User))
        db.commit()
    finally:
        db.close()


def create_test_user_and_login():
    """Helper function to create a user and return auth token"""
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
    return login_response.json()["access_token"]


def create_test_photo(token, photo_uuid=None):
    """Helper function to create a test photo"""
    if photo_uuid is None:
        photo_uuid = str(uuid.uuid4())
    response = client.post(
        "/api/photos/",
        json={
            "uuid": photo_uuid,
            "original_filename": f"test-{photo_uuid}.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()


def test_create_album():
    """Test creating a new album"""
    create_test_user_and_login()
    album_uuid = str(uuid.uuid4())

    response = client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Test Album",
            "creation_date": "2024-01-01T00:00:00",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["uuid"] == album_uuid
    assert data["title"] == "Test Album"
    assert data["creation_date"] == "2024-01-01T00:00:00"


def test_create_album_duplicate_uuid():
    """Test creating an album with a duplicate UUID fails"""
    create_test_user_and_login()
    album_uuid = str(uuid.uuid4())

    # Create first album
    client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Test Album",
            "creation_date": "2024-01-01T00:00:00",
        },
    )

    # Try to create another with same UUID
    response = client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Different Album",
            "creation_date": "2024-01-02T00:00:00",
        },
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_album_with_photos():
    """Test creating an album with associated photos"""
    token = create_test_user_and_login()

    # Create test photos
    photo_uuid_1 = str(uuid.uuid4())
    photo_uuid_2 = str(uuid.uuid4())
    create_test_photo(token, photo_uuid_1)
    create_test_photo(token, photo_uuid_2)

    album_uuid = str(uuid.uuid4())
    response = client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Album with Photos",
            "creation_date": "2024-01-01T00:00:00",
            "photos": [photo_uuid_1, photo_uuid_2],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["uuid"] == album_uuid
    assert data["title"] == "Album with Photos"


def test_list_albums_empty():
    """Test listing albums when none exist"""
    create_test_user_and_login()

    response = client.get("/api/albums/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_albums():
    """Test listing multiple albums"""
    create_test_user_and_login()

    # Create multiple albums
    for i in range(3):
        album_uuid = str(uuid.uuid4())
        client.post(
            "/api/albums/",
            json={
                "uuid": album_uuid,
                "title": f"Test Album {i}",
                "creation_date": "2024-01-01T00:00:00",
            },
        )

    response = client.get("/api/albums/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["title"] == "Test Album 0"
    assert data[1]["title"] == "Test Album 1"
    assert data[2]["title"] == "Test Album 2"


def test_list_albums_pagination():
    """Test album list pagination"""
    create_test_user_and_login()

    # Create 5 albums
    for i in range(5):
        album_uuid = str(uuid.uuid4())
        client.post(
            "/api/albums/",
            json={
                "uuid": album_uuid,
                "title": f"Test Album {i}",
                "creation_date": "2024-01-01T00:00:00",
            },
        )

    # Test pagination - skip 2, limit 2
    response = client.get("/api/albums/?skip=2&limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_album():
    """Test retrieving a specific album by UUID"""
    create_test_user_and_login()
    album_uuid = str(uuid.uuid4())

    # Create album
    client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Test Album",
            "creation_date": "2024-01-01T00:00:00",
            "start_date": "2024-01-01T10:00:00",
            "end_date": "2024-01-01T20:00:00",
        },
    )

    response = client.get(f"/api/albums/{album_uuid}/")

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == album_uuid
    assert data["title"] == "Test Album"
    assert data["start_date"] == "2024-01-01T10:00:00"
    assert data["end_date"] == "2024-01-01T20:00:00"


def test_get_album_not_found():
    """Test retrieving a non-existent album returns 404"""
    create_test_user_and_login()
    nonexistent_uuid = str(uuid.uuid4())

    response = client.get(f"/api/albums/{nonexistent_uuid}/")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_or_create_album_create():
    """Test PUT endpoint creates a new album when it doesn't exist"""
    create_test_user_and_login()
    album_uuid = str(uuid.uuid4())

    response = client.put(
        f"/api/albums/{album_uuid}/",
        json={
            "uuid": album_uuid,
            "title": "New Album via PUT",
            "creation_date": "2024-01-01T00:00:00",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == album_uuid
    assert data["title"] == "New Album via PUT"


def test_update_or_create_album_update():
    """Test PUT endpoint updates an existing album"""
    create_test_user_and_login()
    album_uuid = str(uuid.uuid4())

    # Create album
    client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Original Title",
            "creation_date": "2024-01-01T00:00:00",
        },
    )

    # Update via PUT
    response = client.put(
        f"/api/albums/{album_uuid}/",
        json={
            "uuid": album_uuid,
            "title": "Updated Title",
            "creation_date": "2024-01-02T00:00:00",
            "start_date": "2024-01-02T10:00:00",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == album_uuid
    assert data["title"] == "Updated Title"
    assert data["creation_date"] == "2024-01-02T00:00:00"
    assert data["start_date"] == "2024-01-02T10:00:00"


def test_update_or_create_album_with_photos():
    """Test PUT endpoint updates album photos"""
    token = create_test_user_and_login()

    # Create test photos
    photo_uuid_1 = str(uuid.uuid4())
    photo_uuid_2 = str(uuid.uuid4())
    photo_uuid_3 = str(uuid.uuid4())
    create_test_photo(token, photo_uuid_1)
    create_test_photo(token, photo_uuid_2)
    create_test_photo(token, photo_uuid_3)

    # Create album with initial photos
    album_uuid = str(uuid.uuid4())
    client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Test Album",
            "creation_date": "2024-01-01T00:00:00",
            "photos": [photo_uuid_1, photo_uuid_2],
        },
    )

    # Update with different photos
    response = client.put(
        f"/api/albums/{album_uuid}/",
        json={
            "uuid": album_uuid,
            "title": "Test Album",
            "creation_date": "2024-01-01T00:00:00",
            "photos": [photo_uuid_2, photo_uuid_3],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == album_uuid


def test_patch_album():
    """Test partially updating an album"""
    create_test_user_and_login()
    album_uuid = str(uuid.uuid4())

    # Create album
    client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Original Title",
            "creation_date": "2024-01-01T00:00:00",
        },
    )

    # Partial update - only title
    response = client.patch(
        f"/api/albums/{album_uuid}/",
        json={"title": "Updated Title Only"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == album_uuid
    assert data["title"] == "Updated Title Only"
    assert data["creation_date"] == "2024-01-01T00:00:00"


def test_patch_album_not_found():
    """Test patching a non-existent album returns 404"""
    create_test_user_and_login()
    nonexistent_uuid = str(uuid.uuid4())

    response = client.patch(
        f"/api/albums/{nonexistent_uuid}/",
        json={"title": "New Title"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_patch_album_photos():
    """Test updating album photos via PATCH"""
    token = create_test_user_and_login()

    # Create test photos
    photo_uuid_1 = str(uuid.uuid4())
    photo_uuid_2 = str(uuid.uuid4())
    photo_uuid_3 = str(uuid.uuid4())
    create_test_photo(token, photo_uuid_1)
    create_test_photo(token, photo_uuid_2)
    create_test_photo(token, photo_uuid_3)

    # Create album with initial photos
    album_uuid = str(uuid.uuid4())
    client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Test Album",
            "creation_date": "2024-01-01T00:00:00",
            "photos": [photo_uuid_1],
        },
    )

    # Update photos via PATCH
    response = client.patch(
        f"/api/albums/{album_uuid}/",
        json={"photos": [photo_uuid_2, photo_uuid_3]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == album_uuid


def test_patch_album_clear_photos():
    """Test clearing album photos via PATCH"""
    token = create_test_user_and_login()

    # Create test photo
    photo_uuid_1 = str(uuid.uuid4())
    create_test_photo(token, photo_uuid_1)

    # Create album with photos
    album_uuid = str(uuid.uuid4())
    client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Test Album",
            "creation_date": "2024-01-01T00:00:00",
            "photos": [photo_uuid_1],
        },
    )

    # Clear photos via PATCH
    response = client.patch(
        f"/api/albums/{album_uuid}/",
        json={"photos": []},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == album_uuid


def test_delete_album():
    """Test deleting an album"""
    create_test_user_and_login()
    album_uuid = str(uuid.uuid4())

    # Create album
    client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Test Album",
            "creation_date": "2024-01-01T00:00:00",
        },
    )

    # Delete album
    response = client.delete(f"/api/albums/{album_uuid}/")

    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    # Verify album is deleted
    get_response = client.get(f"/api/albums/{album_uuid}/")
    assert get_response.status_code == 404


def test_delete_album_not_found():
    """Test deleting a non-existent album returns 404"""
    create_test_user_and_login()
    nonexistent_uuid = str(uuid.uuid4())

    response = client.delete(f"/api/albums/{nonexistent_uuid}/")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_album_with_photos():
    """Test deleting an album with associated photos"""
    token = create_test_user_and_login()

    # Create test photos
    photo_uuid_1 = str(uuid.uuid4())
    photo_uuid_2 = str(uuid.uuid4())
    create_test_photo(token, photo_uuid_1)
    create_test_photo(token, photo_uuid_2)

    # Create album with photos
    album_uuid = str(uuid.uuid4())
    client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Test Album",
            "creation_date": "2024-01-01T00:00:00",
            "photos": [photo_uuid_1, photo_uuid_2],
        },
    )

    # Delete album
    response = client.delete(f"/api/albums/{album_uuid}/")

    assert response.status_code == 200

    # Verify photos still exist
    photo_response = client.get(
        f"/api/photos/{photo_uuid_1}/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert photo_response.status_code == 200


def test_album_with_dates():
    """Test creating and retrieving album with start and end dates"""
    create_test_user_and_login()
    album_uuid = str(uuid.uuid4())

    response = client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Vacation Album",
            "creation_date": "2024-01-01T00:00:00",
            "start_date": "2024-06-01T00:00:00",
            "end_date": "2024-06-15T23:59:59",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["start_date"] == "2024-06-01T00:00:00"
    assert data["end_date"] == "2024-06-15T23:59:59"

    # Verify dates are preserved on retrieval
    get_response = client.get(f"/api/albums/{album_uuid}/")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["start_date"] == "2024-06-01T00:00:00"
    assert get_data["end_date"] == "2024-06-15T23:59:59"


def test_album_with_nonexistent_photos():
    """Test creating album with references to non-existent photos"""
    create_test_user_and_login()

    # Create album with non-existent photo UUIDs
    album_uuid = str(uuid.uuid4())
    nonexistent_photo_1 = str(uuid.uuid4())
    nonexistent_photo_2 = str(uuid.uuid4())
    response = client.post(
        "/api/albums/",
        json={
            "uuid": album_uuid,
            "title": "Test Album",
            "creation_date": "2024-01-01T00:00:00",
            "photos": [nonexistent_photo_1, nonexistent_photo_2],
        },
    )

    # Should succeed but silently ignore non-existent photos
    assert response.status_code == 201
    data = response.json()
    assert data["uuid"] == album_uuid
