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
    value TEXT NOT NULL,
    source VARCHAR NOT NULL,
    INDEX idx_photo_uuid (photo_uuid),
    INDEX idx_key (key),
    INDEX idx_source (source)
);
```

### Key Features

1. **Extensible Metadata**: Metadata can be added incrementally without replacing existing entries
2. **Source Tracking**: Each metadata entry tracks its source (e.g., "macos", "exif", "legacy")
3. **Key-Source Uniqueness**: Updates to metadata with the same key and source will update the value instead of creating duplicates
4. **Different Sources**: Metadata with the same key but different sources are kept separate

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
      "value": "Canon PowerShot",
      "source": "macos"
    },
    {
      "key": "year",
      "value": "2024",
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
- Existing entries with the same key+source are updated
- Entries with different sources are kept separate

### macOS Sync Changes

The macOS sync script now sends metadata with `source="macos"` instead of just using `search_info`. This allows for proper source tracking while maintaining backward compatibility.

Example in `sync_commands.py`:

```python
# Convert search_info to metadata with source="macos"
metadata_entries = []
for key, value in search_info_dict.items():
    metadata_entries.append({
        "key": key,
        "value": str(value),  # or JSON for lists/dicts
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
