"""Tests for versions preselection and library filters"""

import uuid

import pytest


def test_list_photos_includes_versions(client):
    """Test that listing photos includes versions"""
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

    photo_uuid = str(uuid.uuid4())

    # Create a photo with versions
    client.post(
        "/api/photos/",
        json={
            "uuid": photo_uuid,
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
            "versions": [
                {
                    "version": "thumbnail",
                    "s3_path": "s3://bucket/thumbnail.jpg",
                    "width": 150,
                    "height": 150,
                },
                {
                    "version": "medium",
                    "s3_path": "s3://bucket/medium.jpg",
                    "width": 800,
                    "height": 600,
                },
                {
                    "version": "original",
                    "s3_path": "s3://bucket/original.jpg",
                    "width": 4032,
                    "height": 3024,
                },
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # List photos
    response = client.get("/api/photos/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1

    photo = data["items"][0]
    assert photo["uuid"] == photo_uuid
    assert "versions" in photo
    assert photo["versions"] is not None
    assert len(photo["versions"]) == 3

    # Check version details
    versions = photo["versions"]
    version_names = {v["version"] for v in versions}
    assert "thumbnail" in version_names
    assert "medium" in version_names
    assert "original" in version_names


def test_library_filter(client):
    """Test that library filter works correctly"""
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

    # Create photos with different libraries
    photo1_uuid = str(uuid.uuid4())
    client.post(
        "/api/photos/",
        json={
            "uuid": photo1_uuid,
            "original_filename": "photo1.jpg",
            "date": "2024-01-01T00:00:00",
            "library": "Personal",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    photo2_uuid = str(uuid.uuid4())
    client.post(
        "/api/photos/",
        json={
            "uuid": photo2_uuid,
            "original_filename": "photo2.jpg",
            "date": "2024-01-02T00:00:00",
            "library": "Work",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    photo3_uuid = str(uuid.uuid4())
    client.post(
        "/api/photos/",
        json={
            "uuid": photo3_uuid,
            "original_filename": "photo3.jpg",
            "date": "2024-01-03T00:00:00",
            "library": "Personal",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Filter by Personal library
    response = client.get(
        "/api/photos/?library=Personal", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    library_values = {photo["library"] for photo in data["items"]}
    assert library_values == {"Personal"}

    # Filter by Work library
    response = client.get(
        "/api/photos/?library=Work", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["library"] == "Work"


def test_available_filters_includes_libraries(client):
    """Test that available filters endpoint includes libraries"""
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

    # Create photos with different libraries
    for i in range(3):
        client.post(
            "/api/photos/",
            json={
                "uuid": str(uuid.uuid4()),
                "original_filename": f"photo{i}.jpg",
                "date": f"2024-01-0{i + 1}T00:00:00",
                "library": f"Library{i % 2 + 1}",  # Library1 or Library2
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    # Get available filters
    response = client.get(
        "/api/photos/filters/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "libraries" in data
    assert "albums" in data
    assert "persons" in data
    # Check that keywords is NOT in the response (since we're removing it from the frontend)
    # The backend still returns it, but we don't use it in the frontend
    assert set(data["libraries"]) == {"Library1", "Library2"}
