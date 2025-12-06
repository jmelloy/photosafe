# PhotoSafe CLI

Command-line interface for PhotoSafe photo library management.

## Installation

Install the CLI in development mode:

```bash
cd backend
pip install -e .
```

Or install the required dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

The PhotoSafe CLI provides several commands for managing users, libraries, and importing photos.

### User Management

#### Create a User

```bash
# Interactive mode (will prompt for password)
photosafe user create --username john --email john@example.com --name "John Doe"

# Create a superuser
photosafe user create --username admin --email admin@example.com --superuser
```

#### List Users

```bash
photosafe user list
```

#### Show User Information

```bash
photosafe user info john
```

### Library Management

Libraries allow users to organize photos into separate collections.

#### Create a Library

```bash
photosafe library create --username john --name "Vacation Photos" --path /photos/vacation --description "Summer vacation 2024"
```

#### List Libraries

```bash
# List all libraries
photosafe library list

# List libraries for a specific user
photosafe library list --username john
```

#### Show Library Information

```bash
photosafe library info 1
```

#### Update a Library

```bash
photosafe library update 1 --name "New Name" --path /new/path
```

### Photo Import

Import photos from a folder with automatic EXIF extraction and optional metadata sidecars.

#### Automatic EXIF Extraction

All images are automatically scanned for EXIF data during import. Camera settings, exposure information, and GPS coordinates are extracted and stored in the `exif` field.

#### Import with JSON Sidecar

The importer reads JSON sidecar files that follow the Apple Photos export format (compatible with dump scripts):

```bash
photosafe import \
  --username john \
  --library-id 1 \
  --folder /path/to/photos \
  --sidecar-format json
```

#### Import with meta.json for Arbitrary Metadata

Place a `meta.json` file in your photo directory to add arbitrary metadata to all photos:

```bash
# Directory structure:
# /photos/
#   ├── meta.json          # Arbitrary metadata for all photos
#   ├── photo1.jpg
#   ├── photo1.jpg.json    # Photo-specific metadata
#   └── photo2.jpg

photosafe import \
  --username john \
  --library-id 1 \
  --folder /path/to/photos
```

The `meta.json` file can contain any arbitrary metadata:

```json
{
  "photographer": "John Doe",
  "location_name": "Central Park",
  "event": "Summer Festival 2024",
  "copyright": "© 2024 John Doe"
}
```

This metadata will be stored in the `fields` JSON column and can be queried later.

#### Import with Library Creation

Create a library automatically if it doesn't exist:

```bash
photosafe import \
  --username john \
  --library-name "New Library" \
  --folder /path/to/photos \
  --sidecar-format json
```

#### Import with S3 Upload

Upload photos to S3 during import:

```bash
photosafe import \
  --username john \
  --library-id 1 \
  --folder /path/to/photos \
  --upload-to-s3 \
  --s3-bucket my-photo-bucket \
  --s3-prefix photos/john
```

#### Dry Run

Test the import without making any changes:

```bash
photosafe import \
  --username john \
  --library-id 1 \
  --folder /path/to/photos \
  --dry-run
```

## Sidecar File Format

The import command supports JSON sidecar files with the following format:

```json
{
  "uuid": "UNIQUE-PHOTO-UUID",
  "fingerprint": "photo-fingerprint",
  "original_filename": "IMG_1234.jpg",
  "filename": "IMG_1234.jpg",
  "date": "2024-01-01T12:00:00-08:00",
  "title": "Photo Title",
  "description": "Photo description",
  "keywords": ["keyword1", "keyword2"],
  "labels": ["Label 1", "Label 2"],
  "persons": ["Person 1", "Person 2"],
  "favorite": true,
  "hidden": false,
  "isphoto": true,
  "ismovie": false,
  "width": 3264,
  "height": 2448,
  "latitude": 37.7749,
  "longitude": -122.4194,
  "exif_info": {
    "camera_make": "Apple",
    "camera_model": "iPhone 12"
  },
  "place": {},
  "score": {},
  "search_info": {}
}
```

This format is compatible with the output of the PhotoSafe dump scripts and Apple Photos export tools.

### Metadata Priority

When multiple metadata sources provide the same field:

1. **JSON sidecar** (photo-specific) - highest priority
2. **meta.json** (directory-wide) - medium priority  
3. **EXIF data** (extracted from image) - lowest priority

For example, if both a sidecar file and EXIF data contain camera information, the sidecar data is used.

See [METADATA_IMPORT.md](METADATA_IMPORT.md) for detailed documentation on metadata handling.

## Examples

### Complete Workflow

1. Create a user:
```bash
photosafe user create --username john --email john@example.com
```

2. Create a library:
```bash
photosafe library create --username john --name "My Photos" --path /home/john/photos
```

3. Import photos:
```bash
photosafe import --username john --library-id 1 --folder /home/john/photos --sidecar-format json
```

4. Verify:
```bash
photosafe user info john
photosafe library info 1
```

### Import from Apple Photos Export

If you've exported photos from Apple Photos with sidecar metadata:

```bash
# Export should contain .jpg/.heic files and .json sidecar files
photosafe import \
  --username john \
  --library-name "Apple Photos Import" \
  --folder /path/to/apple-export \
  --sidecar-format json
```

### Batch Import with S3

For large photo collections, upload to S3 for better storage:

```bash
photosafe import \
  --username john \
  --library-id 1 \
  --folder /path/to/photos \
  --upload-to-s3 \
  --s3-bucket my-bucket \
  --s3-prefix photos/collection-2024
```

## Database Migrations

Before using the CLI, ensure the database is up to date:

```bash
cd backend
alembic upgrade head
```

## Environment Variables

The CLI uses the same database configuration as the main application. Configure via environment variables or `.env` file:

```bash
DATABASE_URL=sqlite:///./photosafe.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/photosafe
```

## Development

Run tests:

```bash
cd backend
python -m pytest test_cli.py -v
```

## Features

- ✅ User creation and management
- ✅ Multiple libraries per user
- ✅ Photo import from folders
- ✅ **Automatic EXIF extraction** from images
- ✅ JSON sidecar metadata support
- ✅ **meta.json for arbitrary metadata**
- ✅ **Arbitrary metadata storage in fields column**
- ✅ S3 upload integration
- ✅ Dry-run mode for safe testing
- 🔄 XMP sidecar support (basic structure, needs enhancement)
- 🔄 Apple library direct import (planned)
