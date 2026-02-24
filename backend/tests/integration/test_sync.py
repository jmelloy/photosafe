"""Tests for photo synchronization functionality"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from dateutil import parser

import pytest

from cli.sync_commands import sync


@pytest.fixture
def macos_sample_data(fixtures_dir):
    """Load macos sample data from fixture"""
    fixture_path = fixtures_dir / "macos_sample.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


class TestSyncCommands:
    """Test sync CLI commands"""

    def test_sync_help(self, runner):
        """Test sync group help"""
        result = runner.invoke(sync, ["--help"])
        assert result.exit_code == 0
        assert "Sync photos from various sources" in result.output

    def test_macos_help(self, runner):
        """Test macos command help"""
        result = runner.invoke(sync, ["macos", "--help"])
        assert result.exit_code == 0
        assert "Sync photos from macOS Photos library" in result.output
        assert "--output-json" in result.output

    def test_icloud_help(self, runner):
        """Test icloud command help"""
        result = runner.invoke(sync, ["icloud", "--help"])
        assert result.exit_code == 0
        assert "Sync photos from iCloud" in result.output
        assert "--library" in result.output

    def test_list_libraries_help(self, runner):
        """Test list-libraries command help"""
        result = runner.invoke(sync, ["list-libraries", "--help"])
        assert result.exit_code == 0
        assert "List available iCloud photo libraries" in result.output
        assert "--icloud-username" in result.output
        assert "--icloud-password" in result.output

    def test_dump_icloud_help(self, runner):
        """Test dump-icloud command help"""
        result = runner.invoke(sync, ["dump-icloud", "--help"])
        assert result.exit_code == 0
        assert "Dump sample photos from iCloud" in result.output

    @patch("cli.sync_tools.authenticate_icloud")
    def test_list_libraries(self, mock_authenticate, runner):
        """Test list-libraries command"""
        # Mock iCloud API with libraries
        mock_api = MagicMock()
        mock_library1 = MagicMock()
        mock_library2 = MagicMock()
        mock_api.photos.libraries = {
            "Primary": mock_library1,
            "Shared": mock_library2,
        }
        mock_authenticate.return_value = mock_api

        result = runner.invoke(
            sync,
            [
                "list-libraries",
                "--icloud-username",
                "test@example.com",
                "--icloud-password",
                "testpass",
            ],
        )

        assert result.exit_code == 0
        assert "Available iCloud Photo Libraries" in result.output
        assert "Primary" in result.output
        assert "Shared" in result.output

    @patch("cli.sync_tools.authenticate_icloud")
    def test_list_libraries_empty(self, mock_authenticate, runner):
        """Test list-libraries command with no libraries"""
        # Mock iCloud API with no libraries
        mock_api = MagicMock()
        mock_api.photos.libraries = {}
        mock_authenticate.return_value = mock_api

        result = runner.invoke(
            sync,
            [
                "list-libraries",
                "--icloud-username",
                "test@example.com",
                "--icloud-password",
                "testpass",
            ],
        )

        assert result.exit_code == 0
        assert "No libraries found" in result.output

    def test_icloud_library_option_exists(self, runner):
        """Test that icloud command has --library option"""
        result = runner.invoke(sync, ["icloud", "--help"])
        assert result.exit_code == 0
        assert "--library" in result.output
        assert "Filter by library name" in result.output


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
