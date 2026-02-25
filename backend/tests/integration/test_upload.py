"""Tests for the photo upload endpoint with S3-first fallback behavior."""

import os
from unittest.mock import MagicMock, patch

from app.models import Photo, Version


def _register_and_login(client):
    """Helper to register a user and return an auth token."""
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    resp = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"},
    )
    return resp.json()["access_token"]


def test_upload_falls_back_to_local_when_no_s3_bucket(client, db_session):
    """When S3_BUCKET is not set, files are stored locally."""
    token = _register_and_login(client)

    file_content = b"fake image content"
    files = {"file": ("test.jpg", file_content, "image/jpeg")}

    with patch.dict(os.environ, {}, clear=False):
        # Ensure S3_BUCKET is not set
        os.environ.pop("S3_BUCKET", None)
        response = client.post(
            "/api/photos/upload",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "test.jpg"
    assert data["content_type"] == "image/jpeg"
    assert data["file_size"] == len(file_content)
    # Should have local file_path, no s3 paths
    assert data["file_path"] is not None
    assert data["s3_key_path"] is None

    # Version record should be created
    assert data["versions"] is not None
    assert len(data["versions"]) == 1
    assert data["versions"][0]["version"] == "original"
    assert data["versions"][0]["filename"] == "test.jpg"
    assert data["versions"][0]["size"] == len(file_content)


def test_upload_to_s3_success(client, db_session):
    """When S3_BUCKET is set and S3 upload succeeds, file goes to S3."""
    token = _register_and_login(client)

    file_content = b"fake image content"
    files = {"file": ("photo.jpg", file_content, "image/jpeg")}

    mock_s3 = MagicMock()

    with patch.dict(os.environ, {"S3_BUCKET": "test-bucket", "S3_PREFIX": "uploads"}):
        with patch("app.routers.photos.boto3", create=True) as mock_boto3:
            mock_boto3.client.return_value = mock_s3
            # Patch the import inside the endpoint
            import importlib
            import app.routers.photos as photos_module

            original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

            def patched_import(name, *args, **kwargs):
                if name == "boto3":
                    return mock_boto3
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=patched_import):
                response = client.post(
                    "/api/photos/upload",
                    files=files,
                    headers={"Authorization": f"Bearer {token}"},
                )

    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "photo.jpg"
    assert data["s3_key_path"] is not None
    assert "uploads/" in data["s3_key_path"]
    assert "/original/" in data["s3_key_path"]
    assert data["s3_original_path"] == data["s3_key_path"]
    assert data["file_path"] is None

    # Version should point to S3
    assert len(data["versions"]) == 1
    assert data["versions"][0]["s3_path"] == data["s3_key_path"]

    # Verify S3 put_object was called
    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args[1]
    assert call_kwargs["Bucket"] == "test-bucket"
    assert call_kwargs["Body"] == file_content
    assert call_kwargs["ContentType"] == "image/jpeg"


def test_upload_falls_back_to_local_on_s3_failure(client, db_session):
    """When S3 upload fails, the file is stored locally."""
    token = _register_and_login(client)

    file_content = b"fake image content"
    files = {"file": ("test.jpg", file_content, "image/jpeg")}

    mock_s3 = MagicMock()
    mock_s3.put_object.side_effect = Exception("S3 connection error")

    with patch.dict(os.environ, {"S3_BUCKET": "test-bucket"}):
        def patched_import(name, *args, **kwargs):
            if name == "boto3":
                m = MagicMock()
                m.client.return_value = mock_s3
                return m
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=patched_import):
            response = client.post(
                "/api/photos/upload",
                files=files,
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    data = response.json()
    # Should fall back to local
    assert data["file_path"] is not None
    assert data["s3_key_path"] is None

    # Version should still be created with local path
    assert len(data["versions"]) == 1
    assert data["versions"][0]["version"] == "original"


def test_upload_with_version_parameter(client, db_session):
    """The version form field is used in the Version record and S3 path."""
    token = _register_and_login(client)

    file_content = b"fake thumb content"
    files = {"file": ("thumb.jpg", file_content, "image/jpeg")}

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("S3_BUCKET", None)
        response = client.post(
            "/api/photos/upload",
            files=files,
            data={"version": "thumb"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["versions"]) == 1
    assert data["versions"][0]["version"] == "thumb"


def test_upload_video_accepted(client, db_session):
    """Video files should be accepted (not just images)."""
    token = _register_and_login(client)

    file_content = b"fake video content"
    files = {"file": ("clip.mp4", file_content, "video/mp4")}

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("S3_BUCKET", None)
        response = client.post(
            "/api/photos/upload",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["content_type"] == "video/mp4"


def test_upload_rejects_non_media_file(client):
    """Non-image/video files should be rejected."""
    token = _register_and_login(client)

    file_content = b"not media"
    files = {"file": ("test.txt", file_content, "text/plain")}

    response = client.post(
        "/api/photos/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "must be an image or video" in response.json()["detail"]


def test_upload_unauthenticated(client):
    """Upload without auth should fail."""
    file_content = b"fake image content"
    files = {"file": ("test.jpg", file_content, "image/jpeg")}

    response = client.post("/api/photos/upload", files=files)
    assert response.status_code == 401
