# Photo Metadata Feature

## Overview

This document describes the photo metadata feature that replaces the monolithic `search_info` JSONB field with a flexible key-value-source table structure.

## Changes

### Database Schema

Added a new `photo_metadata` table with the following structure:

```sql
CREATE TABLE photo_metadata (
    id SERIAL PRIMARY KEY,
    photo_uuid UUID REFERENCES photos(uuid),
    key VARCHAR NOT NULL,
    value JSONB,
    source VARCHAR NOT NULL,
    UNIQUE (photo_uuid, key),
    INDEX idx_photo_uuid (photo_uuid),
    INDEX idx_value_gin USING GIN (value)
);
```

### Key Features

1. **Extensible Metadata**: Metadata can be added incrementally without replacing existing entries
2. **Source Tracking**: Each metadata entry tracks its source (e.g., "macos", "exif", "legacy")
3. **Key Uniqueness**: Each photo can have only one value per key. Updates to the same key will replace the value and source
4. **JSONB Values**: Values are stored as JSONB, allowing complex data structures (arrays, objects) with efficient querying via GIN index

### API Changes

#### Photo Create/Update

Photos can now include a `metadata` field:

```json
{
  "uuid": "...",
  "original_filename": "photo.jpg",
  "date": "2024-12-19T00:00:00Z",
  "metadata": [
    {
      "key": "camera",
      "value": {"value": "Canon PowerShot"},
      "source": "macos"
    },
    {
      "key": "year",
      "value": {"value": "2024"},
      "source": "macos"
    },
    {
      "key": "labels",
      "value": ["Wedding", "People", "Outdoor"],
      "source": "macos"
    }
  ]
}
```

#### Backward Compatibility

The `search_info` field is still supported for backward compatibility. When provided, it will be automatically converted to metadata entries with source="legacy".

#### PATCH Behavior

The PATCH endpoint now **extends** metadata rather than replacing it:
- New metadata entries are added
- Existing entries with the same key are updated (value and source are replaced)
- The unique constraint on (photo_uuid, key) ensures only one value per key per photo

### macOS Sync Changes

The macOS sync script now sends metadata with `source="macos"` instead of just using `search_info`. This allows for proper source tracking while maintaining backward compatibility.

Example in `sync_commands.py`:

```python
# Convert search_info to metadata with source="macos"
metadata_entries = []
for key, value in search_info_dict.items():
    # Store as JSONB - lists/dicts directly, scalars wrapped
    metadata_entries.append({
        "key": key,
        "value": value if isinstance(value, (list, dict)) else {"value": value},
        "source": "macos",
    })

p["metadata"] = metadata_entries
```

### Migration

The migration (`868ffb01c651_add_photo_metadata_table.py`) performs the following:

1. Creates the `photo_metadata` table with indexes
2. Migrates existing `search_info` data to the new table with source="legacy"
3. Keeps the `search_info` field in the photos table for backward compatibility

### Models

- **PhotoMetadata**: New model for storing key-value-source metadata
- **Photo**: Updated with `photo_metadata` relationship (named to avoid SQLAlchemy reserved name conflict)
- **PhotoMetadataRead/Create**: Schema models for API serialization

### Utility Functions

- `process_search_info_to_metadata(search_info, source)`: Converts a search_info dictionary to metadata entries
- `extend_photo_metadata(photo, metadata_entries, db)`: Extends photo metadata, updating existing entries with same key+source

## Usage Examples

### Creating a Photo with Metadata

```python
photo_data = PhotoCreate(
    uuid=uuid.uuid4(),
    original_filename="vacation.jpg",
    date=datetime.utcnow(),
    metadata=[
        PhotoMetadataCreate(key="camera", value="Canon EOS", source="exif"),
        PhotoMetadataCreate(key="location", value="Paris", source="macos"),
    ]
)
```

### Updating Photo Metadata

```python
# This will extend existing metadata
update_data = PhotoUpdate(
    metadata=[
        PhotoMetadataCreate(key="season", value="Summer", source="macos"),
    ]
)
```

### Querying Photos by Metadata

```python
# Find photos with specific metadata
photos_with_canon = (
    db.query(Photo)
    .join(PhotoMetadata)
    .filter(PhotoMetadata.key == "camera", PhotoMetadata.value.like("%Canon%"))
    .all()
)
```

## Testing

Unit tests are available in `tests/unit/test_photo_metadata.py` covering:
- Metadata conversion from search_info
- Extending metadata
- Updating existing metadata
- Different sources creating separate entries

Integration tests are available in `tests/integration/test_photo_metadata_api.py` covering:
- Creating photos with metadata
- Backward compatibility with search_info
- PATCH extending behavior
- Batch operations

## Future Enhancements

1. **Metadata Search API**: Add dedicated endpoint for searching photos by metadata
2. **Metadata Aggregation**: Add endpoint to list all unique metadata keys/values
3. **Metadata UI**: Frontend components for viewing and editing metadata
4. **Additional Sources**: Support for more metadata sources (exif, icloud, user-defined, etc.)
