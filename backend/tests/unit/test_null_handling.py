"""Tests for null handling in sync commands"""

import json
from cli.sync_tools import DateTimeEncoder
from cli.sync_commands import clean_photo_data


def test_none_values_filtered_from_persons():
    """Test that None values are removed from persons list"""
    # Simulate data with None in persons
    photo_data = {
        "uuid": "test-uuid",
        "persons": ["John", None, "Jane", None],
        "place": None,
        "face_info": [{"name": "John"}, None, {"name": "Jane"}],
    }

    # Apply the cleaning logic
    photo_data = clean_photo_data(photo_data)

    # Verify None values are removed
    assert photo_data["persons"] == ["John", "Jane"]
    assert photo_data["place"] == {}
    assert photo_data["face_info"] == [{"name": "John"}, {"name": "Jane"}]


def test_none_persons_becomes_empty_list():
    """Test that None persons becomes empty list"""
    photo_data = {
        "uuid": "test-uuid",
        "persons": None,
        "place": None,
        "face_info": None,
    }

    # Apply the cleaning logic
    photo_data = clean_photo_data(photo_data)

    assert photo_data["persons"] == []
    assert photo_data["place"] == {}
    assert photo_data["face_info"] == []


def test_json_serialization_without_null_strings():
    """Test that None values don't become 'null' strings in JSON"""
    photo_data = {
        "uuid": "test-uuid",
        "persons": ["John", "Jane"],
        "place": {},
        "face_info": [],
        "latitude": None,  # This can remain None as it's a numeric field
    }

    # Serialize to JSON
    json_str = json.dumps(photo_data, cls=DateTimeEncoder)

    # Verify that we don't have the string "null" in arrays
    assert '"persons": ["John", "Jane"]' in json_str
    assert '"place": {}' in json_str
    assert '"face_info": []' in json_str
    # latitude: null is OK for numeric fields
    assert '"latitude": null' in json_str

    # Verify we don't have "null" as a string in the persons array
    assert '"persons": [null]' not in json_str
    assert '"persons": ["null"]' not in json_str


def test_empty_lists_preserved():
    """Test that empty lists are preserved, not converted to None"""
    photo_data = {
        "uuid": "test-uuid",
        "persons": [],
        "place": {},
        "face_info": [],
    }

    # Apply the cleaning logic (should not change anything)
    photo_data = clean_photo_data(photo_data)

    assert photo_data["persons"] == []
    assert photo_data["place"] == {}
    assert photo_data["face_info"] == []
