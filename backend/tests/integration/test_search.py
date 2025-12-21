"""Integration tests for search API endpoints"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from app.models import Photo


def test_get_search_filters(client, auth_headers, test_user, db_session):
    """Test GET /api/search/filters endpoint"""
    # Create some photos with various metadata
    photos = [
        Photo(
            uuid=uuid4(),
            original_filename="photo1.jpg",
            date=datetime.now(timezone.utc),
            labels=["sunset", "beach"],
            keywords=["vacation"],
            persons=["John"],
            albums=["Summer 2023"],
            library="Main",
            place={"name": "Santa Monica"},
            owner_id=test_user.id,
        ),
        Photo(
            uuid=uuid4(),
            original_filename="photo2.jpg",
            date=datetime.now(timezone.utc),
            labels=["sunset"],
            keywords=["travel"],
            persons=["Jane"],
            albums=["Travel"],
            library="Main",
            owner_id=test_user.id,
        ),
    ]
    
    for photo in photos:
        db_session.add(photo)
    db_session.commit()

    # Populate search_data via the photos endpoint
    # (The populate_search_data_for_photo is called automatically in photo create/update)
    from app.utils import populate_search_data_for_photo
    for photo in photos:
        populate_search_data_for_photo(photo, db_session)
    db_session.commit()

    # Get search filters
    response = client.get("/api/search/filters", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "places" in data
    assert "labels" in data
    assert "keywords" in data
    assert "persons" in data
    assert "albums" in data
    assert "libraries" in data

    # Check that our data is present
    assert "Santa Monica" in data["places"]
    assert "sunset" in data["labels"]
    assert "beach" in data["labels"]
    assert "vacation" in data["keywords"]
    assert "travel" in data["keywords"]
    assert "John" in data["persons"]
    assert "Jane" in data["persons"]
    assert "Summer 2023" in data["albums"]
    assert "Travel" in data["albums"]
    assert "Main" in data["libraries"]


def test_search_photos_by_label(client, auth_headers, test_user, db_session):
    """Test searching photos by label"""
    # Create photos
    photo1 = Photo(
        uuid=uuid4(),
        original_filename="sunset.jpg",
        date=datetime.now(timezone.utc),
        labels=["sunset", "beach"],
        owner_id=test_user.id,
    )
    photo2 = Photo(
        uuid=uuid4(),
        original_filename="mountain.jpg",
        date=datetime.now(timezone.utc),
        labels=["mountain"],
        owner_id=test_user.id,
    )
    
    db_session.add(photo1)
    db_session.add(photo2)
    db_session.commit()

    # Populate search_data
    from app.utils import populate_search_data_for_photo
    populate_search_data_for_photo(photo1, db_session)
    populate_search_data_for_photo(photo2, db_session)
    db_session.commit()

    # Search for sunset
    response = client.get(
        "/api/search/",
        params={"labels": "sunset"},
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["uuid"] == str(photo1.uuid)


def test_search_photos_multiple_filters(client, auth_headers, test_user, db_session):
    """Test searching photos with multiple filters"""
    # Create photos
    photo1 = Photo(
        uuid=uuid4(),
        original_filename="beach_vacation.jpg",
        date=datetime.now(timezone.utc),
        labels=["sunset"],
        keywords=["vacation"],
        owner_id=test_user.id,
    )
    photo2 = Photo(
        uuid=uuid4(),
        original_filename="mountain_vacation.jpg",
        date=datetime.now(timezone.utc),
        labels=["mountain"],
        keywords=["vacation"],
        owner_id=test_user.id,
    )
    photo3 = Photo(
        uuid=uuid4(),
        original_filename="beach_work.jpg",
        date=datetime.now(timezone.utc),
        labels=["sunset"],
        keywords=["work"],
        owner_id=test_user.id,
    )
    
    db_session.add(photo1)
    db_session.add(photo2)
    db_session.add(photo3)
    db_session.commit()

    # Populate search_data
    from app.utils import populate_search_data_for_photo
    for photo in [photo1, photo2, photo3]:
        populate_search_data_for_photo(photo, db_session)
    db_session.commit()

    # Search for sunset AND vacation (should match photo1 only)
    response = client.get(
        "/api/search/",
        params={"labels": "sunset", "keywords": "vacation"},
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["uuid"] == str(photo1.uuid)


def test_search_photos_multiple_values(client, auth_headers, test_user, db_session):
    """Test searching photos with multiple values in one filter (OR logic)"""
    # Create photos
    photo1 = Photo(
        uuid=uuid4(),
        original_filename="sunset.jpg",
        date=datetime.now(timezone.utc),
        labels=["sunset"],
        owner_id=test_user.id,
    )
    photo2 = Photo(
        uuid=uuid4(),
        original_filename="mountain.jpg",
        date=datetime.now(timezone.utc),
        labels=["mountain"],
        owner_id=test_user.id,
    )
    photo3 = Photo(
        uuid=uuid4(),
        original_filename="beach.jpg",
        date=datetime.now(timezone.utc),
        labels=["beach"],
        owner_id=test_user.id,
    )
    
    db_session.add(photo1)
    db_session.add(photo2)
    db_session.add(photo3)
    db_session.commit()

    # Populate search_data
    from app.utils import populate_search_data_for_photo
    for photo in [photo1, photo2, photo3]:
        populate_search_data_for_photo(photo, db_session)
    db_session.commit()

    # Search for sunset OR mountain (should match photo1 and photo2)
    response = client.get(
        "/api/search/",
        params={"labels": "sunset,mountain"},
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 2
    uuids = [item["uuid"] for item in data["items"]]
    assert str(photo1.uuid) in uuids
    assert str(photo2.uuid) in uuids


def test_search_photos_text_search(client, auth_headers, test_user, db_session):
    """Test text search in titles and descriptions"""
    # Create photos
    photo1 = Photo(
        uuid=uuid4(),
        original_filename="photo1.jpg",
        date=datetime.now(timezone.utc),
        title="Beautiful Sunset",
        owner_id=test_user.id,
    )
    photo2 = Photo(
        uuid=uuid4(),
        original_filename="photo2.jpg",
        date=datetime.now(timezone.utc),
        description="A mountain view at sunset",
        owner_id=test_user.id,
    )
    photo3 = Photo(
        uuid=uuid4(),
        original_filename="photo3.jpg",
        date=datetime.now(timezone.utc),
        title="Beach Day",
        owner_id=test_user.id,
    )
    
    db_session.add(photo1)
    db_session.add(photo2)
    db_session.add(photo3)
    db_session.commit()

    # Populate search_data
    from app.utils import populate_search_data_for_photo
    for photo in [photo1, photo2, photo3]:
        populate_search_data_for_photo(photo, db_session)
    db_session.commit()

    # Search for "sunset" in text (should match photo1 and photo2)
    response = client.get(
        "/api/search/",
        params={"search_text": "sunset"},
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 2
    uuids = [item["uuid"] for item in data["items"]]
    assert str(photo1.uuid) in uuids
    assert str(photo2.uuid) in uuids
