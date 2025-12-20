"""Tests for album API endpoints"""

import uuid

import pytest


def create_test_user_and_login(client):
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


def test_create_album(client):
    """Test creating a new album"""
    create_test_user_and_login(client)
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


def test_create_album_duplicate_uuid(client):
    """Test creating an album with a duplicate UUID fails"""
    create_test_user_and_login(client)
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


def test_create_album_with_photos(client):
    """Test creating an album with associated photos"""
    token = create_test_user_and_login(client)

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


def test_list_albums_empty(client):
    """Test listing albums when none exist"""
    create_test_user_and_login(client)

    response = client.get("/api/albums/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_albums(client):
    """Test listing multiple albums"""
    create_test_user_and_login(client)

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


def test_list_albums_pagination(client):
    """Test album list pagination"""
    create_test_user_and_login(client)

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


def test_get_album(client):
    """Test retrieving a specific album by UUID"""
    create_test_user_and_login(client)
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


def test_get_album_not_found(client):
    """Test retrieving a non-existent album returns 404"""
    create_test_user_and_login(client)
    nonexistent_uuid = str(uuid.uuid4())

    response = client.get(f"/api/albums/{nonexistent_uuid}/")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_or_create_album_create(client):
    """Test PUT endpoint creates a new album when it doesn't exist"""
    create_test_user_and_login(client)
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


def test_update_or_create_album_update(client):
    """Test PUT endpoint updates an existing album"""
    create_test_user_and_login(client)
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


def test_update_or_create_album_with_photos(client):
    """Test PUT endpoint updates album photos"""
    token = create_test_user_and_login(client)

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


def test_patch_album(client):
    """Test partially updating an album"""
    create_test_user_and_login(client)
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


def test_patch_album_not_found(client):
    """Test patching a non-existent album returns 404"""
    create_test_user_and_login(client)
    nonexistent_uuid = str(uuid.uuid4())

    response = client.patch(
        f"/api/albums/{nonexistent_uuid}/",
        json={"title": "New Title"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_patch_album_photos(client):
    """Test updating album photos via PATCH"""
    token = create_test_user_and_login(client)

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


def test_patch_album_clear_photos(client):
    """Test clearing album photos via PATCH"""
    token = create_test_user_and_login(client)

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


def test_delete_album(client):
    """Test deleting an album"""
    create_test_user_and_login(client)
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


def test_delete_album_not_found(client):
    """Test deleting a non-existent album returns 404"""
    create_test_user_and_login(client)
    nonexistent_uuid = str(uuid.uuid4())

    response = client.delete(f"/api/albums/{nonexistent_uuid}/")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_album_with_photos(client):
    """Test deleting an album with associated photos"""
    token = create_test_user_and_login(client)

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


def test_album_with_dates(client):
    """Test creating and retrieving album with start and end dates"""
    create_test_user_and_login(client)
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


def test_album_with_nonexistent_photos(client):
    """Test creating album with references to non-existent photos"""
    create_test_user_and_login(client)

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
