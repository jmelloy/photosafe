"""Tests for maintenance CLI commands"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli.maintenance_commands import (
    compare_versions,
    delete_orphaned_files,
    get_s3_objects_from_csv,
    maintenance,
    print_report,
)
from app.models import Version


class TestGetS3ObjectsFromCsv:
    """Test get_s3_objects_from_csv function"""

    def test_parse_csv_with_bucket(self):
        """Test parsing CSV with bucket information"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["Bucket", "Key", "Size", "LastModifiedDate", "ETag"])
            writer.writerow(
                [
                    "test-bucket",
                    "photos/img1.jpg",
                    "1024",
                    "2023-01-01T00:00:00Z",
                    '"abc123"',
                ]
            )
            writer.writerow(
                [
                    "test-bucket",
                    "photos/img2.jpg",
                    "2048",
                    "2023-01-02T00:00:00Z",
                    '"def456"',
                ]
            )
            csv_path = f.name

        try:
            result = get_s3_objects_from_csv(csv_path)

            assert len(result) == 2
            assert "photos/img1.jpg" in result
            assert result["photos/img1.jpg"]["size"] == 1024
            assert result["photos/img1.jpg"]["bucket"] == "test-bucket"
            assert result["photos/img2.jpg"]["size"] == 2048
            assert result["photos/img2.jpg"]["bucket"] == "test-bucket"
        finally:
            Path(csv_path).unlink()

    def test_parse_csv_without_bucket(self):
        """Test parsing CSV without bucket column"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["Key", "Size", "LastModifiedDate", "ETag"])
            writer.writerow(
                ["photos/img1.jpg", "1024", "2023-01-01T00:00:00Z", '"abc123"']
            )
            csv_path = f.name

        try:
            result = get_s3_objects_from_csv(csv_path)

            assert len(result) == 1
            assert "photos/img1.jpg" in result
            assert result["photos/img1.jpg"]["size"] == 1024
            assert result["photos/img1.jpg"]["bucket"] == ""
        finally:
            Path(csv_path).unlink()


class TestCompareVersions:
    """Test compare_versions function"""

    def test_orphaned_files_with_size(self):
        """Test that orphaned files include size and bucket info"""
        # Create mock versions
        versions = [
            MagicMock(
                id=1,
                photo_uuid="uuid1",
                version="original",
                s3_path="photos/img1.jpg",
                size=1024,
            ),
        ]

        # S3 objects with extra orphaned files
        s3_objects = {
            "photos/img1.jpg": {"size": 1024, "bucket": "test-bucket"},
            "photos/orphan1.jpg": {"size": 512345, "bucket": "test-bucket"},
            "photos/orphan2.jpg": {"size": 3145728, "bucket": "test-bucket"},
        }

        result = compare_versions(versions, s3_objects)

        # Check orphaned files
        assert len(result["orphaned_in_s3"]) == 2

        orphaned = result["orphaned_in_s3"]
        orphaned_paths = [item["s3_path"] for item in orphaned]

        assert "photos/orphan1.jpg" in orphaned_paths
        assert "photos/orphan2.jpg" in orphaned_paths

        # Find orphan1 and orphan2
        orphan1 = next(
            item for item in orphaned if item["s3_path"] == "photos/orphan1.jpg"
        )
        orphan2 = next(
            item for item in orphaned if item["s3_path"] == "photos/orphan2.jpg"
        )

        assert orphan1["size"] == 512345
        assert orphan1["bucket"] == "test-bucket"
        assert orphan2["size"] == 3145728
        assert orphan2["bucket"] == "test-bucket"

    def test_no_orphaned_files(self):
        """Test when all S3 files are in database"""
        versions = [
            MagicMock(
                id=1,
                photo_uuid="uuid1",
                version="original",
                s3_path="photos/img1.jpg",
                size=1024,
            ),
            MagicMock(
                id=2,
                photo_uuid="uuid2",
                version="original",
                s3_path="photos/img2.jpg",
                size=2048,
            ),
        ]

        s3_objects = {
            "photos/img1.jpg": {"size": 1024, "bucket": "test-bucket"},
            "photos/img2.jpg": {"size": 2048, "bucket": "test-bucket"},
        }

        result = compare_versions(versions, s3_objects)

        assert len(result["orphaned_in_s3"]) == 0


class TestDeleteOrphanedFiles:
    """Test delete_orphaned_files function"""

    @patch("cli.maintenance_commands.boto3.client")
    @patch("cli.maintenance_commands.click.confirm")
    def test_delete_orphaned_files_confirmed(self, mock_confirm, mock_boto3_client):
        """Test deleting orphaned files when user confirms"""
        mock_confirm.return_value = True
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        orphaned_files = [
            {"s3_path": "photos/orphan1.jpg", "size": 512345, "bucket": "test-bucket"},
            {"s3_path": "photos/orphan2.jpg", "size": 3145728, "bucket": "test-bucket"},
        ]

        result = delete_orphaned_files(orphaned_files)

        assert result == 2
        assert mock_s3.delete_object.call_count == 2
        mock_s3.delete_object.assert_any_call(
            Bucket="test-bucket", Key="photos/orphan1.jpg"
        )
        mock_s3.delete_object.assert_any_call(
            Bucket="test-bucket", Key="photos/orphan2.jpg"
        )

    @patch("cli.maintenance_commands.click.confirm")
    def test_delete_orphaned_files_cancelled(self, mock_confirm):
        """Test cancelling deletion of orphaned files"""
        mock_confirm.return_value = False

        orphaned_files = [
            {"s3_path": "photos/orphan1.jpg", "size": 512345, "bucket": "test-bucket"},
        ]

        result = delete_orphaned_files(orphaned_files)

        assert result == 0

    @patch("cli.maintenance_commands.boto3.client")
    @patch("cli.maintenance_commands.click.confirm")
    def test_delete_orphaned_files_no_bucket(self, mock_confirm, mock_boto3_client):
        """Test handling files without bucket info"""
        mock_confirm.return_value = True
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        orphaned_files = [
            {"s3_path": "photos/orphan1.jpg", "size": 512345, "bucket": ""},
        ]

        result = delete_orphaned_files(orphaned_files)

        assert result == 0
        mock_s3.delete_object.assert_not_called()


class TestPrintReport:
    """Test print_report function"""

    def test_print_report_with_orphaned_files(self, capsys):
        """Test printing report with orphaned files"""
        issues = {
            "missing_in_s3": [],
            "size_mismatch": [],
            "missing_photos": [],
            "orphaned_in_s3": [
                {
                    "s3_path": "photos/orphan1.jpg",
                    "size": 512345,
                    "bucket": "test-bucket",
                },
                {
                    "s3_path": "photos/orphan2.jpg",
                    "size": 3145728,
                    "bucket": "test-bucket",
                },
            ],
        }

        print_report(issues, show_orphaned=True)

        captured = capsys.readouterr()

        # Check that size is displayed
        assert "MB" in captured.out
        assert "KB" in captured.out
        assert "photos/orphan1.jpg" in captured.out
        assert "photos/orphan2.jpg" in captured.out

    def test_print_report_without_show_orphaned(self, capsys):
        """Test printing report without showing orphaned details"""
        issues = {
            "missing_in_s3": [],
            "size_mismatch": [],
            "missing_photos": [],
            "orphaned_in_s3": [
                {
                    "s3_path": "photos/orphan1.jpg",
                    "size": 512345,
                    "bucket": "test-bucket",
                },
            ],
        }

        print_report(issues, show_orphaned=False)

        captured = capsys.readouterr()

        # Check that count and total size are shown but not details
        assert "1 files" in captured.out
        assert "MB" in captured.out
        assert "use --show-orphaned to see details" in captured.out
