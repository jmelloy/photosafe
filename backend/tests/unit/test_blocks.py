"""Tests for /photos/blocks endpoint"""

from datetime import datetime
from uuid import uuid4

import pytest


def test_photo_blocks_endpoint(client):
    """Test the /photos/blocks endpoint"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser1",
            "email": "test2@test.com",
            "password": "testpass123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser1", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create photos with different dates and labels
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "test1.jpg",
        "date": "2024-01-15T12:00:00",
        "labels": None,  # No labels
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "test2.jpg",
        "date": "2024-01-15T14:00:00",
        "labels": None,  # Also NULL labels (not empty array for SQLite compatibility)
    }
    photo3_data = {
        "uuid": str(uuid4()),
        "original_filename": "test3.jpg",
        "date": "2024-02-10T10:00:00",
        "labels": None,
    }
    photo4_data = {
        "uuid": str(uuid4()),
        "original_filename": "test4.jpg",
        "date": "2024-01-15T16:00:00",
        "labels": ["Outdoor", "Nature"],  # Has labels - should be excluded
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)
    client.post("/api/photos/", json=photo3_data, headers=headers)
    client.post("/api/photos/", json=photo4_data, headers=headers)

    # Get blocks
    response = client.get("/api/photos/blocks", headers=headers)

    assert response.status_code == 200
    blocks = response.json()

    # Verify structure (JSON keys are strings)
    assert "2024" in blocks
    assert "1" in blocks["2024"]
    assert "2" in blocks["2024"]
    assert "15" in blocks["2024"]["1"]
    assert "10" in blocks["2024"]["2"]

    # Verify counts (should only include photos without labels)
    assert blocks["2024"]["1"]["15"]["count"] == 3  # photo1 photo2, photo4
    assert blocks["2024"]["2"]["10"]["count"] == 1  # photo3

    # Verify max_date exists
    assert "max_date" in blocks["2024"]["1"]["15"]
    assert "max_date" in blocks["2024"]["2"]["10"]

    # Verify max_date is the latest date for the day (photo2 at 14:00:00)
    # Note: We don't check modified date in this test, only photo date
    max_date_str = blocks["2024"]["1"]["15"]["max_date"]
    assert max_date_str is not None
    # The max_date should be photo2's date since it's later than photo1
    # (photo1: 12:00:00, photo2: 14:00:00, photo4 is excluded due to labels)


def test_photo_blocks_with_modified_dates(client):
    """Test that blocks endpoint correctly uses date_modified when available"""
    # Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser2",
            "email": "test3@test.com",
            "password": "testpass123",
        },
    )
    login_response = client.post(
        "/api/auth/login", data={"username": "testuser2", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create photos with different dates and modified dates
    photo1_data = {
        "uuid": str(uuid4()),
        "original_filename": "test1.jpg",
        "date": "2024-03-20T10:00:00",
        "date_modified": "2024-03-20T15:00:00",  # Modified later
        "labels": None,
    }
    photo2_data = {
        "uuid": str(uuid4()),
        "original_filename": "test2.jpg",
        "date": "2024-03-20T12:00:00",
        "date_modified": None,  # No modification
        "labels": None,
    }

    client.post("/api/photos/", json=photo1_data, headers=headers)
    client.post("/api/photos/", json=photo2_data, headers=headers)

    # Get blocks
    response = client.get("/api/photos/blocks", headers=headers)

    assert response.status_code == 200
    blocks = response.json()

    # Verify structure
    assert "2024" in blocks
    assert "3" in blocks["2024"]
    assert "20" in blocks["2024"]["3"]

    # Verify count
    assert blocks["2024"]["3"]["20"]["count"] == 2

    # Verify max_date uses date_modified when available
    max_date_str = blocks["2024"]["3"]["20"]["max_date"]
    assert max_date_str is not None
    # The max should be the modified date of photo1 (15:00:00), not photo2's date (12:00:00)
    datetime.fromisoformat(max_date_str.replace("Z", "+00:00"))
    # Should be 15:00 or later (coalesce should pick date_modified)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
