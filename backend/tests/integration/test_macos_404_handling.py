"""Tests for macOS sync 404 handling and version creation"""

import json
from unittest.mock import MagicMock, patch
from dateutil import parser

import pytest
from click.testing import CliRunner

from cli.sync_commands import sync


@pytest.fixture
def macos_sample_data(fixtures_dir):
    """Load macos sample data from fixture"""
    fixture_path = fixtures_dir / "macos_sample.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


class TestMacOS404Handling:
    """Test macOS sync 404 handling and photo creation with versions"""

    def test_macos_sync_404_creates_photo_with_original(
        self, runner, macos_sample_data
    ):
        """Test that 404 response creates photo when it has an original path and is not in trash"""
        mock_osxphotos = MagicMock()
        with patch.dict("sys.modules", {"osxphotos": mock_osxphotos}):
            # Create mock PhotosDB
            mock_photos_db = MagicMock()
            mock_osxphotos.PhotosDB.return_value = mock_photos_db
            mock_photos_db.library_path = (
                "/Users/test/Pictures/Photos Library.photoslibrary"
            )

            # Use a photo with original path
            photo_data = macos_sample_data[1].copy()  # Second photo has original path
            photo_data["path"] = "/originals/test/photo.jpg"

            mock_photo = MagicMock()
            mock_photo.uuid = photo_data["uuid"]
            mock_photo.original_filename = photo_data["original_filename"]
            mock_photo.date = parser.parse(photo_data["date"])
            mock_photo.date_modified = None
            mock_photo.path = "/Users/test/Pictures/Photos Library.photoslibrary/originals/test/photo.jpg"
            mock_photo.path_edited = None
            mock_photo.path_derivatives = None
            mock_photo._info = {
                "cloudAssetGUID": photo_data["uuid"],
                "masterFingerprint": photo_data.get("masterFingerprint"),
            }
            mock_photo.asdict.return_value = photo_data
            mock_photo.search_info = MagicMock()
            mock_photo.search_info.asdict.return_value = {}
            mock_photo.intrash = False

            mock_photos_db.photos.return_value = [mock_photo]

            # Mock boto3
            with patch("cli.sync_commands.boto3") as mock_boto3:
                mock_s3 = MagicMock()
                mock_boto3.client.return_value = mock_s3

                # Mock os.path.exists to return True for file uploads
                with patch("cli.sync_commands.os.path.exists", return_value=True):
                    # Mock PhotoSafeAuth
                    with patch("cli.sync_tools.PhotoSafeAuth") as mock_auth:
                        mock_auth_instance = MagicMock()
                        mock_auth.return_value = mock_auth_instance

                        # Mock blocks API
                        mock_auth_instance.get.return_value.json.return_value = {}
                        mock_auth_instance.get.return_value.status_code = 200
                        mock_auth_instance.get.return_value.raise_for_status = (
                            MagicMock()
                        )

                        # Mock the patch request to return 404
                        mock_auth_instance.patch.return_value.status_code = 404
                        mock_auth_instance.patch.return_value.raise_for_status = (
                            MagicMock()
                        )

                        # Mock the post request (create photo)
                        mock_auth_instance.post.return_value.status_code = 201
                        mock_auth_instance.post.return_value.raise_for_status = (
                            MagicMock()
                        )

                        # Run the sync command with skip-blocks-check to ensure it processes the photo
                        result = runner.invoke(
                            sync,
                            [
                                "macos",
                                "--username",
                                "test",
                                "--password",
                                "test",
                                "--base-url",
                                "http://localhost:8000",
                                "--bucket",
                                "test-bucket",
                                "--skip-blocks-check",
                            ],
                        )

                        assert result.exit_code == 0
                        # Should have created the photo
                        assert "Creating photo" in result.output
                        # Verify POST was called to create photo
                        mock_auth_instance.post.assert_called_once()

                        # Verify S3 upload was called
                        mock_s3.upload_file.assert_called()

                    # Check the data passed to POST
                    call_args = mock_auth_instance.post.call_args
                    posted_data = json.loads(call_args[1]["data"])
                    assert "versions" in posted_data
                    assert len(posted_data["versions"]) > 0
                    assert posted_data["versions"][0]["version"] == "original"

    def test_macos_sync_deletes_trashed_photos(self, runner, macos_sample_data):
        """Test that trashed photos with no files are soft deleted"""
        mock_osxphotos = MagicMock()
        with patch.dict("sys.modules", {"osxphotos": mock_osxphotos}):
            # Create mock PhotosDB
            mock_photos_db = MagicMock()
            mock_osxphotos.PhotosDB.return_value = mock_photos_db
            mock_photos_db.library_path = (
                "/Users/test/Pictures/Photos Library.photoslibrary"
            )

            # Create a photo in trash with no files
            photo_data = macos_sample_data[0].copy()
            photo_data["intrash"] = True

            mock_photo = MagicMock()
            mock_photo.uuid = photo_data["uuid"]
            mock_photo.original_filename = photo_data["original_filename"]
            mock_photo.date = parser.parse(photo_data["date"])
            mock_photo.date_modified = None
            mock_photo.path = None  # No path
            mock_photo.path_edited = None
            mock_photo.path_live_photo = None
            mock_photo.intrash = True
            mock_photo._info = {
                "cloudAssetGUID": photo_data["uuid"],
                "masterFingerprint": photo_data.get("masterFingerprint"),
            }
            mock_photo.asdict.return_value = photo_data

            mock_photos_db.photos.return_value = [mock_photo]

            # Mock boto3
            with patch("cli.sync_commands.boto3"):
                # Mock PhotoSafeAuth
                with patch("cli.sync_tools.PhotoSafeAuth") as mock_auth:
                    mock_auth_instance = MagicMock()
                    mock_auth.return_value = mock_auth_instance

                    # Mock blocks API
                    mock_auth_instance.get.return_value.json.return_value = {}
                    mock_auth_instance.get.return_value.status_code = 200
                    mock_auth_instance.get.return_value.raise_for_status = MagicMock()

                    # Mock the delete request
                    mock_auth_instance.delete.return_value.status_code = 200

                    # Mock os.path.exists to return False
                    with patch("cli.sync_commands.os.path.exists", return_value=False):
                        # Run the sync command with skip-blocks-check to ensure it processes the photo
                        result = runner.invoke(
                            sync,
                            [
                                "macos",
                                "--username",
                                "test",
                                "--password",
                                "test",
                                "--base-url",
                                "http://localhost:8000",
                                "--bucket",
                                "test-bucket",
                                "--skip-blocks-check",
                            ],
                        )

                        assert result.exit_code == 0
                        # Should have deleted the photo
                        assert "Deleted photo" in result.output
                        # Verify DELETE was called
                        mock_auth_instance.delete.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
