"""Tests for authentication and user photo management"""

import uuid

import pytest



def test_register_user(client):
    """Test user registration"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data
    assert data["is_active"] is True


def test_register_duplicate_username(client):
    """Test registration with duplicate username"""
    # Register first user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # Try to register with same username
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "different@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


def test_login(client):
    """Test user login"""
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # Login
    response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token(client):
    """Test refreshing access token using refresh token"""
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # Login to get tokens
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "testpassword123"}
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    refresh_token = login_data["refresh_token"]

    # Use refresh token to get new access token
    refresh_response = client.post(
        "/api/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    assert refresh_data["token_type"] == "bearer"

    # Verify the new access token works
    new_access_token = refresh_data["access_token"]
    me_response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "testuser"


def test_refresh_token_invalid(client):
    """Test refresh with invalid token"""
    response = client.post("/api/auth/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401
    assert "Invalid refresh token" in response.json()["detail"]


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # Try to login with wrong password
    response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_get_current_user(client):
    """Test getting current user information"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User",
        },
    )

    login_response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "testpassword123"}
    )
    token = login_response.json()["access_token"]

    # Get current user
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


def test_create_photo_authenticated(client):
    """Test creating a photo while authenticated"""
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

    # Create photo
    response = client.post(
        "/api/photos/",
        json={
            "uuid": "1e692e8c-4b9a-4e6a-ae0e-8a0bf0e8ad44",
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["uuid"] == "1e692e8c-4b9a-4e6a-ae0e-8a0bf0e8ad44"
    assert data["original_filename"] == "test.jpg"


def test_create_photo_unauthenticated(client):
    """Test that creating a photo without authentication fails"""
    response = client.post(
        "/api/photos/",
        json={
            "uuid": "1e692e8c-4b9a-4e6a-ae0e-8a0bf0e8ad44",
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
        },
    )
    assert response.status_code == 401


def test_list_photos_only_owned(client):
    """Test that users only see their own photos"""
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

    # Login as user1 and create a photo
    login1 = client.post(
        "/api/auth/login", data={"username": "user1", "password": "password123"}
    )
    token1 = login1.json()["access_token"]

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

    # Login as user2 and create a photo
    login2 = client.post(
        "/api/auth/login", data={"username": "user2", "password": "password123"}
    )
    token2 = login2.json()["access_token"]

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

    # User1 should only see their photo
    response1 = client.get(
        "/api/photos/", headers={"Authorization": f"Bearer {token1}"}
    )
    assert response1.status_code == 200
    photos1 = response1.json()["items"]
    assert len(photos1) == 1
    assert photos1[0]["uuid"] == user1_photo_uuid

    # User2 should only see their photo
    response2 = client.get(
        "/api/photos/", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response2.status_code == 200
    photos2 = response2.json()["items"]
    assert len(photos2) == 1
    assert photos2[0]["uuid"] == user2_photo_uuid


def test_update_photo_ownership(client):
    """Test that users can only update their own photos"""
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

    # User1 creates a photo
    login1 = client.post(
        "/api/auth/login", data={"username": "user1", "password": "password123"}
    )
    token1 = login1.json()["access_token"]

    client.post(
        "/api/photos/",
        json={
            "uuid": "b2ae6737-e14c-4798-82b8-da99a34410ea",
            "original_filename": "user1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User2 tries to update user1's photo
    login2 = client.post(
        "/api/auth/login", data={"username": "user2", "password": "password123"}
    )
    token2 = login2.json()["access_token"]

    response = client.patch(
        "/api/photos/b2ae6737-e14c-4798-82b8-da99a34410ea/",
        json={"title": "Hacked!"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 403


def test_delete_photo_ownership(client):
    """Test that users can only delete their own photos"""
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

    # User1 creates a photo
    login1 = client.post(
        "/api/auth/login", data={"username": "user1", "password": "password123"}
    )
    token1 = login1.json()["access_token"]

    client.post(
        "/api/photos/",
        json={
            "uuid": "b2ae6737-e14c-4798-82b8-da99a34410ea",
            "original_filename": "user1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User2 tries to delete user1's photo
    login2 = client.post(
        "/api/auth/login", data={"username": "user2", "password": "password123"}
    )
    token2 = login2.json()["access_token"]

    response = client.delete(
        "/api/photos/b2ae6737-e14c-4798-82b8-da99a34410ea/",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 403


def test_batch_create_photos(client):
    """Test batch creation of photos"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "batchuser",
            "email": "batch@example.com",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "batchuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]

    # Create batch of photos
    batch_data = {
        "photos": [
            {
                "uuid": "ca63a0c0-a5d7-4ea1-ae3d-15e0095913d9",
                "original_filename": "photo1.jpg",
                "date": "2024-01-01T00:00:00",
            },
            {
                "uuid": "82b2a65a-cf6c-49da-9bab-840eccc355d0",
                "original_filename": "photo2.jpg",
                "date": "2024-01-02T00:00:00",
            },
            {
                "uuid": "bed6c326-c3b0-4127-8753-610462ef521e",
                "original_filename": "photo3.jpg",
                "date": "2024-01-03T00:00:00",
            },
        ]
    }

    response = client.post(
        "/api/photos/batch/",
        json=batch_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 3
    assert result["created"] == 3
    assert result["updated"] == 0
    assert result["errors"] == 0
    assert len(result["results"]) == 3

    # Verify all photos were created successfully
    for photo_result in result["results"]:
        assert photo_result["success"] is True
        assert photo_result["action"] == "created"

    # Verify photos exist in database
    photos_response = client.get(
        "/api/photos/", headers={"Authorization": f"Bearer {token}"}
    )
    photos = photos_response.json()["items"]
    assert len(photos) == 3


def test_batch_update_photos(client):
    """Test batch update of existing photos"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "updateuser",
            "email": "update@example.com",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "updateuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]

    # Create initial photos
    photo_uuids = []
    for i in range(1, 4):
        photo_uuid = str(uuid.uuid4())
        photo_uuids.append(photo_uuid)
        client.post(
            "/api/photos/",
            json={
                "uuid": photo_uuid,
                "original_filename": f"photo{i}.jpg",
                "date": f"2024-01-0{i}T00:00:00",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    # Update via batch
    batch_data = {
        "photos": [
            {
                "uuid": photo_uuids[0],
                "original_filename": "photo1.jpg",
                "date": "2024-01-01T00:00:00",
                "title": "Updated Photo 1",
                "favorite": True,
            },
            {
                "uuid": photo_uuids[1],
                "original_filename": "photo2.jpg",
                "date": "2024-01-02T00:00:00",
                "title": "Updated Photo 2",
            },
        ]
    }

    response = client.post(
        "/api/photos/batch/",
        json=batch_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 2
    assert result["created"] == 0
    assert result["updated"] == 2
    assert result["errors"] == 0

    # Verify updates were applied
    photo1 = client.get(
        f"/api/photos/{photo_uuids[0]}/", headers={"Authorization": f"Bearer {token}"}
    )
    assert photo1.json()["title"] == "Updated Photo 1"
    assert photo1.json()["favorite"] is True


def test_batch_mixed_create_and_update(client):
    """Test batch with both new and existing photos"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "mixeduser",
            "email": "mixed@example.com",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "mixeduser", "password": "password123"}
    )
    token = login_response.json()["access_token"]

    # Create one photo first
    client.post(
        "/api/photos/",
        json={
            "uuid": "1b0b7da3-d5e2-4dcf-bbd5-7e66dd012b8b",
            "original_filename": "existing.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Batch with mix of new and existing
    batch_data = {
        "photos": [
            {
                "uuid": "1b0b7da3-d5e2-4dcf-bbd5-7e66dd012b8b",
                "original_filename": "existing.jpg",
                "date": "2024-01-01T00:00:00",
                "title": "Updated",
            },
            {
                "uuid": "4ba4f82c-60ce-48e0-a676-303b8d1b4a1f",
                "original_filename": "new1.jpg",
                "date": "2024-01-02T00:00:00",
            },
            {
                "uuid": "08ab2d7f-0a61-4746-b774-b19b04f96cd7",
                "original_filename": "new2.jpg",
                "date": "2024-01-03T00:00:00",
            },
        ]
    }

    response = client.post(
        "/api/photos/batch/",
        json=batch_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 3
    assert result["created"] == 2
    assert result["updated"] == 1
    assert result["errors"] == 0


def test_batch_unauthenticated(client):
    """Test batch endpoint requires authentication"""
    new_uuid = uuid.uuid4()
    batch_data = {
        "photos": [
            {
                "uuid": str(new_uuid),
                "original_filename": "test.jpg",
                "date": "2024-01-01T00:00:00",
            }
        ]
    }

    response = client.post("/api/photos/batch/", json=batch_data)
    assert response.status_code == 401


def test_get_photo(client):
    """Test retrieving a specific photo by UUID"""
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

    new_uuid = uuid.uuid4()

    # Create a photo
    create_response = client.post(
        "/api/photos/",
        json={
            "uuid": str(new_uuid),
            "original_filename": "test.jpg",
            "date": "2024-01-01T00:00:00",
            "title": "Test Photo",
            "description": "This is a test photo",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201

    # Get the photo
    response = client.get(
        f"/api/photos/{new_uuid}/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == str(new_uuid)
    assert data["original_filename"] == "test.jpg"
    assert data["title"] == "Test Photo"


def test_get_photo_not_found(client):
    """Test getting a non-existent photo returns 404"""
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

    nonexistent_uuid = str(uuid.uuid4())
    response = client.get(
        f"/api/photos/{nonexistent_uuid}/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_get_photo_unauthorized(client):
    """Test getting another user's photo is forbidden"""
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

    # User1 creates a photo
    client.post(
        "/api/photos/",
        json={
            "uuid": "b2ae6737-e14c-4798-82b8-da99a34410ea",
            "original_filename": "user1.jpg",
            "date": "2024-01-01T00:00:00",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User2 tries to get user1's photo
    response = client.get(
        "/api/photos/b2ae6737-e14c-4798-82b8-da99a34410ea/",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 403


# def test_upload_photo():
#     """Test uploading a photo file"""
#     # Register and login
#     client.post(
#         "/api/auth/register",
#         json={
#             "username": "testuser",
#             "email": "test@example.com",
#             "password": "testpassword123",
#         },
#     )
#     login_response = client.post(
#         "/api/auth/login", data={"username": "testuser", "password": "testpassword123"}
#     )
#     token = login_response.json()["access_token"]

#     # Create a fake image file
#     file_content = b"fake image content"
#     files = {"file": ("test.jpg", file_content, "image/jpeg")}

#     response = client.post(
#         "/api/photos/upload",
#         files=files,
#         headers={"Authorization": f"Bearer {token}"},
#     )
#     assert response.status_code == 200
#     data = response.json()
#     assert "uuid" in data
#     assert data["original_filename"] == "test.jpg"
#     assert data["content_type"] == "image/jpeg"


def test_upload_photo_invalid_type(client):
    """Test uploading a non-image file fails"""
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

    # Create a non-image file
    file_content = b"not an image"
    files = {"file": ("test.txt", file_content, "text/plain")}

    response = client.post(
        "/api/photos/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "must be an image" in response.json()["detail"]


def test_upload_photo_unauthenticated(client):
    """Test uploading without authentication fails"""
    file_content = b"fake image content"
    files = {"file": ("test.jpg", file_content, "image/jpeg")}

    response = client.post("/api/photos/upload", files=files)
    assert response.status_code == 401
