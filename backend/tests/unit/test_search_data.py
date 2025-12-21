"""Test search functionality with search_data table"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from app.models import Photo, SearchData, User
from app.utils import populate_search_data_for_photo
from sqlmodel import select


def test_populate_search_data_for_photo(db_session, test_user):
    """Test that search_data is populated correctly for a photo"""
    # Create a photo with various metadata
    photo = Photo(
        uuid=uuid4(),
        original_filename="test.jpg",
        date=datetime.now(timezone.utc),
        title="Sunset Beach",
        description="Beautiful sunset at the beach",
        keywords=["vacation", "summer"],
        labels=["beach", "sunset"],
        persons=["John", "Jane"],
        albums=["Summer 2023"],
        library="Main Library",
        place={
            "name": "Santa Monica Beach",
            "name_locality": "Santa Monica",
            "name_administrative_area": "California",
            "name_country": "United States",
        },
        owner_id=test_user.id,
    )
    db_session.add(photo)
    db_session.flush()

    # Populate search_data
    populate_search_data_for_photo(photo, db_session)
    db_session.commit()

    # Query search_data entries
    search_entries = db_session.exec(
        select(SearchData).where(SearchData.photo_uuid == photo.uuid)
    ).all()

    # Check that entries were created
    assert len(search_entries) > 0

    # Convert to dict for easier checking
    search_dict = {}
    for entry in search_entries:
        if entry.key not in search_dict:
            search_dict[entry.key] = []
        search_dict[entry.key].append(entry.value)

    # Verify expected entries
    assert "keyword" in search_dict
    assert "vacation" in search_dict["keyword"]
    assert "summer" in search_dict["keyword"]

    assert "label" in search_dict
    assert "beach" in search_dict["label"]
    assert "sunset" in search_dict["label"]

    assert "person" in search_dict
    assert "John" in search_dict["person"]
    assert "Jane" in search_dict["person"]

    assert "album" in search_dict
    assert "Summer 2023" in search_dict["album"]

    assert "library" in search_dict
    assert "Main Library" in search_dict["library"]

    assert "title" in search_dict
    assert "Sunset Beach" in search_dict["title"]

    assert "description" in search_dict
    assert "Beautiful sunset at the beach" in search_dict["description"]

    assert "place" in search_dict
    assert "Santa Monica Beach" in search_dict["place"]
    assert "Santa Monica" in search_dict["place"]
    assert "California" in search_dict["place"]
    assert "United States" in search_dict["place"]


def test_search_data_unique_constraint(db_session, test_user):
    """Test that duplicate search_data entries are prevented by unique constraint"""
    # Create a photo
    photo = Photo(
        uuid=uuid4(),
        original_filename="test.jpg",
        date=datetime.now(timezone.utc),
        labels=["test"],
        owner_id=test_user.id,
    )
    db_session.add(photo)
    db_session.flush()

    # Add search_data entry
    search_entry = SearchData(
        photo_uuid=photo.uuid,
        key="label",
        value="test",
    )
    db_session.add(search_entry)
    db_session.commit()

    # Try to add duplicate - should be prevented by unique constraint
    duplicate_entry = SearchData(
        photo_uuid=photo.uuid,
        key="label",
        value="test",
    )
    db_session.add(duplicate_entry)

    # Should raise an integrity error
    with pytest.raises(Exception):  # IntegrityError from SQLAlchemy
        db_session.commit()


def test_update_photo_updates_search_data(db_session, test_user):
    """Test that updating a photo updates its search_data"""
    # Create a photo
    photo = Photo(
        uuid=uuid4(),
        original_filename="test.jpg",
        date=datetime.now(timezone.utc),
        labels=["initial"],
        owner_id=test_user.id,
    )
    db_session.add(photo)
    db_session.flush()

    # Populate initial search_data
    populate_search_data_for_photo(photo, db_session)
    db_session.commit()

    # Check initial entries
    entries = db_session.exec(
        select(SearchData)
        .where(SearchData.photo_uuid == photo.uuid)
        .where(SearchData.key == "label")
    ).all()
    assert len(entries) == 1
    assert entries[0].value == "initial"

    # Update photo labels
    photo.labels = ["updated", "new"]
    populate_search_data_for_photo(photo, db_session)
    db_session.commit()

    # Check updated entries (should replace old ones)
    entries = db_session.exec(
        select(SearchData)
        .where(SearchData.photo_uuid == photo.uuid)
        .where(SearchData.key == "label")
    ).all()
    assert len(entries) == 2
    values = [e.value for e in entries]
    assert "updated" in values
    assert "new" in values
    assert "initial" not in values
