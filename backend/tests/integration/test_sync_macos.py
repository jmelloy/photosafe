"""Tests for macOS photo synchronization using fixtures"""

import json
from datetime import datetime, timezone
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


class TestMacOSSyncWithFixtures:
    """Test macOS sync functionality using fixtures"""

    def test_macos_sync_with_fixture_data(self, runner, macos_sample_data):
        """Test syncing photos from macOS using fixture data"""
        # Mock osxphotos module import
        mock_osxphotos = MagicMock()
        with patch.dict("sys.modules", {"osxphotos": mock_osxphotos}):
            # Create mock PhotosDB
            mock_photos_db = MagicMock()
            mock_osxphotos.PhotosDB.return_value = mock_photos_db
            mock_photos_db.library_path = (
                "/Users/test/Pictures/Photos Library.photoslibrary"
            )

            # Create mock photos from fixture data
            mock_photos = []
            for photo_data in macos_sample_data[:3]:  # Use first 3 photos
                mock_photo = MagicMock()
                mock_photo.uuid = photo_data["uuid"]
                mock_photo.original_filename = photo_data["original_filename"]
                mock_photo.date = parser.parse(photo_data["date"])
                mock_photo.date_modified = (
                    parser.parse(photo_data["date_modified"])
                    if photo_data.get("date_modified")
                    else None
                )
                mock_photo._info = {
                    "cloudAssetGUID": photo_data["uuid"],
                    "masterFingerprint": photo_data.get("masterFingerprint"),
                }
                mock_photo.asdict.return_value = photo_data.copy()
                mock_photos.append(mock_photo)

            mock_photos_db.photos.return_value = mock_photos

            # Mock boto3
            with patch("cli.sync_commands.boto3") as mock_boto3:
                mock_s3 = MagicMock()
                mock_boto3.client.return_value = mock_s3

                # Mock PhotoSafeAuth
                with patch("cli.sync_tools.PhotoSafeAuth") as mock_auth:
                    mock_auth_instance = MagicMock()
                    mock_auth.return_value = mock_auth_instance

                    # Mock the blocks API response - empty blocks to trigger processing
                    mock_auth_instance.get.return_value.json.return_value = {}
                    mock_auth_instance.get.return_value.status_code = 200
                    mock_auth_instance.get.return_value.raise_for_status = MagicMock()

                    # Mock the patch request (photo sync)
                    mock_auth_instance.patch.return_value.status_code = 200
                    mock_auth_instance.patch.return_value.raise_for_status = MagicMock()

                    # Run the sync command
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
                        ],
                    )

                    assert result.exit_code == 0
                    assert (
                        "photos processed" in result.output
                        or "to process" in result.output
                    )

    def test_macos_sync_discrepancy_detection(self, runner, macos_sample_data):
        """Test that discrepancies are correctly detected between local and server"""
        mock_osxphotos = MagicMock()
        with patch.dict("sys.modules", {"osxphotos": mock_osxphotos}):
            # Create mock PhotosDB
            mock_photos_db = MagicMock()
            mock_osxphotos.PhotosDB.return_value = mock_photos_db
            mock_photos_db.library_path = (
                "/Users/test/Pictures/Photos Library.photoslibrary"
            )

            # Create two mock photos with the SAME date to test discrepancy detection
            photo_data = macos_sample_data[0]
            same_date = parser.parse(photo_data["date"])

            mock_photos = []
            for i in range(2):  # Create 2 photos with same date
                mock_photo = MagicMock()
                mock_photo.uuid = photo_data["uuid"] + str(i)
                mock_photo.original_filename = f"test{i}.jpg"
                mock_photo.date = same_date
                mock_photo.date_modified = None
                mock_photo._info = {
                    "cloudAssetGUID": photo_data["uuid"] + str(i),
                    "masterFingerprint": photo_data.get("masterFingerprint", "test"),
                }
                # Create a unique dict for each photo
                photo_dict = photo_data.copy()
                photo_dict["uuid"] = photo_data["uuid"] + str(i)
                photo_dict["original_filename"] = f"test{i}.jpg"
                mock_photo.asdict.return_value = photo_dict
                mock_photos.append(mock_photo)

            mock_photos_db.photos.return_value = mock_photos

            # Mock boto3
            with patch("cli.sync_commands.boto3") as mock_boto3:
                mock_s3 = MagicMock()
                mock_boto3.client.return_value = mock_s3

                # Mock PhotoSafeAuth
                with patch("cli.sync_tools.PhotoSafeAuth") as mock_auth:
                    mock_auth_instance = MagicMock()
                    mock_auth.return_value = mock_auth_instance

                    # Create a mismatched blocks response
                    # Set count to 1 when we actually have 2 photos
                    photo_date = same_date.astimezone(timezone.utc)
                    server_blocks = {
                        str(photo_date.year): {
                            str(photo_date.month): {
                                str(photo_date.day): {
                                    "count": 1,  # Mismatch! We have 2 but server says 1
                                    "max_date": photo_date.isoformat(),
                                }
                            }
                        }
                    }

                    mock_auth_instance.get.return_value.json.return_value = (
                        server_blocks
                    )
                    mock_auth_instance.get.return_value.status_code = 200
                    mock_auth_instance.get.return_value.raise_for_status = MagicMock()

                    # Mock the patch request
                    mock_auth_instance.patch.return_value.status_code = 200
                    mock_auth_instance.patch.return_value.raise_for_status = MagicMock()

                    # Run the sync command
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
                        ],
                    )

                    assert result.exit_code == 0
                    # Should detect discrepancy
                    assert "Discrepancy" in result.output

    def test_macos_sync_date_comparison(self, runner, macos_sample_data):
        """Test that date changes are detected in sync"""
        mock_osxphotos = MagicMock()
        with patch.dict("sys.modules", {"osxphotos": mock_osxphotos}):
            # Create mock PhotosDB
            mock_photos_db = MagicMock()
            mock_osxphotos.PhotosDB.return_value = mock_photos_db
            mock_photos_db.library_path = (
                "/Users/test/Pictures/Photos Library.photoslibrary"
            )

            # Use a photo from fixtures
            photo_data = macos_sample_data[0]
            mock_photo = MagicMock()
            mock_photo.uuid = photo_data["uuid"]
            mock_photo.original_filename = photo_data["original_filename"]
            photo_date = parser.parse(photo_data["date"])
            mock_photo.date = photo_date
            mock_photo.date_modified = (
                parser.parse(photo_data["date_modified"])
                if photo_data.get("date_modified")
                else photo_date
            )
            mock_photo._info = {
                "cloudAssetGUID": photo_data["uuid"],
                "masterFingerprint": photo_data.get("masterFingerprint"),
            }
            mock_photo.asdict.return_value = photo_data.copy()

            mock_photos_db.photos.return_value = [mock_photo]

            # Mock boto3
            with patch("cli.sync_commands.boto3") as mock_boto3:
                mock_s3 = MagicMock()
                mock_boto3.client.return_value = mock_s3

                # Mock PhotoSafeAuth
                with patch("cli.sync_tools.PhotoSafeAuth") as mock_auth:
                    mock_auth_instance = MagicMock()
                    mock_auth.return_value = mock_auth_instance

                    # Create blocks response with older date
                    dt = photo_date.astimezone(timezone.utc)
                    older_date = datetime(
                        dt.year, dt.month, dt.day, 0, 0, 0, tzinfo=timezone.utc
                    )

                    server_blocks = {
                        str(dt.year): {
                            str(dt.month): {
                                str(dt.day): {
                                    "count": 1,  # Same count
                                    "max_date": older_date.isoformat(),  # But older date
                                }
                            }
                        }
                    }

                    mock_auth_instance.get.return_value.json.return_value = (
                        server_blocks
                    )
                    mock_auth_instance.get.return_value.status_code = 200
                    mock_auth_instance.get.return_value.raise_for_status = MagicMock()

                    # Mock the patch request
                    mock_auth_instance.patch.return_value.status_code = 200
                    mock_auth_instance.patch.return_value.raise_for_status = MagicMock()

                    # Run the sync command
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
                        ],
                    )

                    assert result.exit_code == 0
                    # Should detect discrepancy due to date difference
                    # Date checking is now implemented in the blocks check
                    assert (
                        "Discrepancy" in result.output or "to process" in result.output
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
