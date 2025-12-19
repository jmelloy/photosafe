"""Tests for library upsert functionality in photo PATCH endpoint"""

import pytest
import uuid
import os
from sqlmodel import select

from app.models import Library, Photo, User


def test_patch_photo_creates_library_if_not_exists(client, db_session):
    """Test that patching a photo with a library name creates the library if it doesn't exist"""
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

    new_uuid = str(uuid.uuid4())

    # Create a photo without library
    response = client.post(
        "/api/photos/",
        json={
            "uuid": new_uuid,
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    # Verify no libraries exist yet
    libraries = db_session.exec(select(Library)).all()
    assert len(libraries) == 0

    # Patch the photo with a library name
    patch_response = client.patch(
        f"/api/photos/{new_uuid}/",
        json={"library": "My Photos"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch_response.status_code == 200

    # Verify library was created
    libraries = db_session.exec(select(Library)).all()
    assert len(libraries) == 1
    assert libraries[0].name == "My Photos"

    # Verify photo has library_id set
    photo = db_session.exec(select(Photo).where(Photo.uuid == new_uuid)).first()
    assert photo is not None
    assert photo.library_id == libraries[0].id
    assert photo.library == "My Photos"


def test_patch_photo_reuses_existing_library(client, db_session):
    """Test that patching a photo with an existing library name reuses the library"""
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

    # Create first photo with library
    photo_uuid_1 = str(uuid.uuid4())
    client.post(
        "/api/photos/",
        json={
            "uuid": photo_uuid_1,
            "original_filename": "test1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    client.patch(
        f"/api/photos/{photo_uuid_1}/",
        json={"library": "My Photos"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Create second photo
    photo_uuid_2 = str(uuid.uuid4())
    client.post(
        "/api/photos/",
        json={
            "uuid": photo_uuid_2,
            "original_filename": "test2.jpg",
            "date": "2024-01-02T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Patch second photo with same library name
    client.patch(
        f"/api/photos/{photo_uuid_2}/",
        json={"library": "My Photos"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Verify only one library was created
    libraries = db_session.exec(select(Library)).all()
    assert len(libraries) == 1
    assert libraries[0].name == "My Photos"

    # Verify both photos reference the same library
    photo1 = db_session.exec(select(Photo).where(Photo.uuid == photo_uuid_1)).first()
    photo2 = db_session.exec(select(Photo).where(Photo.uuid == photo_uuid_2)).first()
    assert photo1.library_id == libraries[0].id
    assert photo2.library_id == libraries[0].id


def test_patch_photo_library_user_isolation(client, db_session):
    """Test that libraries are isolated per user"""
    # Create two users
    client.post(
        "/api/auth/register",
        json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123",
        },
    )
    client.post(
        "/api/auth/register",
        json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123",
        },
    )

    # Login as user1
    login1 = client.post(
        "/api/auth/login", data={"username": "user1", "password": "password123"}
    )
    token1 = login1.json()["access_token"]

    # Login as user2
    login2 = client.post(
        "/api/auth/login", data={"username": "user2", "password": "password123"}
    )
    token2 = login2.json()["access_token"]

    # User1 creates a photo with library
    user1_photo_uuid = str(uuid.uuid4())
    client.post(
        "/api/photos/",
        json={
            "uuid": user1_photo_uuid,
            "original_filename": "user1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    client.patch(
        f"/api/photos/{user1_photo_uuid}/",
        json={"library": "Shared Name"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User2 creates a photo with same library name
    user2_photo_uuid = str(uuid.uuid4())
    client.post(
        "/api/photos/",
        json={
            "uuid": user2_photo_uuid,
            "original_filename": "user2.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token2}"},
    )
    client.patch(
        f"/api/photos/{user2_photo_uuid}/",
        json={"library": "Shared Name"},
        headers={"Authorization": f"Bearer {token2}"},
    )

    # Verify two separate libraries were created (one per user)
    libraries = db_session.exec(select(Library)).all()
    assert len(libraries) == 2

    # Get user IDs
    user1 = db_session.exec(select(User).where(User.username == "user1")).first()
    user2 = db_session.exec(select(User).where(User.username == "user2")).first()

    # Verify each user has their own library
    user1_libs = db_session.exec(select(Library).where(Library.owner_id == user1.id)).all()
    user2_libs = db_session.exec(select(Library).where(Library.owner_id == user2.id)).all()
    assert len(user1_libs) == 1
    assert len(user2_libs) == 1
    assert user1_libs[0].name == "Shared Name"
    assert user2_libs[0].name == "Shared Name"
    assert user1_libs[0].id != user2_libs[0].id


def test_patch_photo_without_library_no_change(client, db_session):
    """Test that patching a photo without library field doesn't affect library"""
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
    new_uuid = str(uuid.uuid4())
    # Create a photo
    client.post(
        "/api/photos/",
        json={
            "uuid": new_uuid,
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Patch with other fields but no library
    client.patch(
        f"/api/photos/{new_uuid}/",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Verify no libraries were created
    libraries = db_session.exec(select(Library)).all()
    assert len(libraries) == 0

    # Verify photo title was updated
    photo = db_session.exec(select(Photo).where(Photo.uuid == new_uuid)).first()
    assert photo.title == "Updated Title"
    assert photo.library_id is None
