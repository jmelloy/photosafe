"""Tests for sync CLI commands"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from cli.sync_commands import sync


@pytest.fixture
def runner():
    """Click CLI runner"""
    return CliRunner()


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
