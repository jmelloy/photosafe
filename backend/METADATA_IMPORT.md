# Photo Metadata Import Guide

This guide explains how PhotoSafe imports photos with metadata, including EXIF data extraction and arbitrary metadata from sidecar files.

## Overview

PhotoSafe supports importing photos with metadata from multiple sources:

1. **EXIF data** - Automatically extracted from image files
2. **JSON sidecar files** - Photo-specific metadata in JSON format  
3. **meta.json** - Arbitrary metadata shared across photos in a directory

## EXIF Data Extraction

EXIF data is automatically extracted from all supported image formats during import using Pillow. The following EXIF fields are extracted and stored:

### Camera Information
- `camera_make` - Camera manufacturer (e.g., "Canon", "Nikon")
- `camera_model` - Camera model (e.g., "EOS 5D Mark IV")
- `lens_model` - Lens model (if available)

### Exposure Settings
- `shutter_speed` - Shutter speed in seconds (e.g., 0.001 = 1/1000s)
- `aperture` - Aperture value (e.g., 2.8)
- `iso` - ISO sensitivity (e.g., 400)
- `focal_length` - Focal length in mm (e.g., 50.0)
- `exposure_bias` - Exposure compensation value

### Other Settings
- `flash_fired` - Boolean indicating if flash was used
- `white_balance` - White balance mode
- `metering_mode` - Metering mode used

All extracted EXIF data is stored in the `exif` JSON field of the Photo model. The raw EXIF data is also preserved in the `_raw` sub-field.

## JSON Sidecar Files

You can provide photo-specific metadata in JSON sidecar files. PhotoSafe looks for sidecar files in the following order:

1. `<photo>.<ext>.json` (e.g., `photo.jpg.json`)
2. `<photo>.json` (e.g., `photo.json`)

### Supported Fields

Sidecar files can contain any of the following PhotoSafe fields:

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Sunset at the Beach",
  "description": "Beautiful sunset photo",
  "keywords": ["sunset", "beach", "nature"],
  "labels": ["Outdoor", "Landscape"],
  "persons": ["John Doe", "Jane Smith"],
  "favorite": true,
  "hidden": false,
  "latitude": 37.7749,
  "longitude": -122.4194,
  "exif_info": {
    "camera_make": "Canon",
    "camera_model": "EOS R5"
  }
}
```

## meta.json - Arbitrary Metadata

For arbitrary metadata that applies to all photos in a directory, create a `meta.json` file in the same directory as your photos.

### Arbitrary Metadata

If `meta.json` contains fields that are **not** standard PhotoSafe fields, they will be stored in the `fields` JSON column:

```json
{
  "photographer": "John Doe",
  "location_name": "Golden Gate Park",
  "event": "Summer 2024",
  "camera_settings": {
    "custom_mode": "portrait",
    "lighting": "natural"
  },
  "copyright": "© 2024 John Doe"
}
```

This will be stored in the database as:
```json
{
  "fields": {
    "photographer": "John Doe",
    "location_name": "Golden Gate Park",
    "event": "Summer 2024",
    "camera_settings": {
      "custom_mode": "portrait",
      "lighting": "natural"
    },
    "copyright": "© 2024 John Doe"
  }
}
```

### Known PhotoSafe Fields

If `meta.json` contains known PhotoSafe fields (like `title`, `description`, `keywords`), they will be applied directly to the photo:

```json
{
  "title": "Default Title for All Photos",
  "keywords": ["vacation", "2024"],
  "custom_field": "custom value"
}
```

## Import Priority

When multiple metadata sources provide the same field, PhotoSafe uses this priority (highest to lowest):

1. **JSON sidecar file** (photo-specific)
2. **meta.json** (directory-wide)
3. **EXIF data** (extracted from image)

For example, if both the sidecar and EXIF data contain camera information, the sidecar data takes precedence.

## Import Command

Use the `photosafe import` command to import photos with metadata:

```bash
# Basic import
photosafe import \
  --username myuser \
  --library-name "My Photos" \
  --folder /path/to/photos

# Import with S3 upload
photosafe import \
  --username myuser \
  --library-name "My Photos" \
  --folder /path/to/photos \
  --upload-to-s3 \
  --s3-bucket my-bucket \
  --s3-prefix photos/2024

# Dry run (test without importing)
photosafe import \
  --username myuser \
  --library-name "Test Import" \
  --folder /path/to/photos \
  --dry-run
```

## Example Directory Structure

```
photos/
├── meta.json                    # Arbitrary metadata for all photos
├── photo1.jpg                   # Image file
├── photo1.jpg.json              # Photo-specific sidecar
├── photo2.jpg                   # Image file with EXIF
└── photo3.heic                  # HEIC image with EXIF
```

## Version Compatibility

The PhotoSafe FastAPI backend maintains compatibility with the Django backend for photo version handling:

- Both implementations use an `update_or_create` pattern for versions
- Versions are uniquely identified by `(photo_uuid, version)` combination
- When uploading S3 versions, existing versions are updated, new ones are created

This ensures seamless interoperability between the FastAPI and Django implementations.

## Database Storage

All metadata is stored in the `photos` table:

- **Standard fields**: Stored in dedicated columns (e.g., `title`, `description`, `keywords`)
- **EXIF data**: Stored as JSON in the `exif` column
- **Arbitrary metadata**: Stored as JSON in the `fields` column
- **JSON fields**: Automatically serialized for SQLite, native JSONB for PostgreSQL

## Best Practices

1. **Use EXIF when possible**: EXIF data is automatically extracted and always accurate
2. **Sidecar for corrections**: Use sidecar files to override incorrect EXIF data
3. **meta.json for bulk metadata**: Use meta.json for metadata that applies to many photos
4. **Preserve structure**: Keep arbitrary metadata well-structured for easier querying
5. **Don't duplicate EXIF**: Only override EXIF fields if the extracted data is incorrect

## Querying Arbitrary Metadata

You can query photos by arbitrary metadata using PostgreSQL's JSON operators:

```sql
-- Find photos by custom field
SELECT * FROM photos 
WHERE fields->>'photographer' = 'John Doe';

-- Find photos by nested field
SELECT * FROM photos 
WHERE fields->'camera_settings'->>'custom_mode' = 'portrait';
```

For SQLite, the `fields` column stores JSON as text, so you'll need to use JSON functions:

```sql
SELECT * FROM photos 
WHERE json_extract(fields, '$.photographer') = 'John Doe';
```
