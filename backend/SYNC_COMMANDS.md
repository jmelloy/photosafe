# PhotoSafe Sync Commands

This document describes the sync commands that have been moved into the PhotoSafe CLI.

## Overview

The sync functionality for importing photos from various sources has been integrated into the PhotoSafe CLI as subcommands under `photosafe sync`. The original standalone scripts are preserved in the `legacy/` directory for reference.

## Available Sync Commands

### 1. macOS Photos Sync

Syncs photos from the macOS Photos library to PhotoSafe, including all photo metadata such as EXIF data, location information, faces, labels, and aesthetic scores.

**Photo Data Included:**
- Basic metadata (filename, date, dimensions, orientation)
- EXIF information (camera, lens, ISO, aperture, shutter speed, etc.)
- Location data (GPS coordinates, place names, address)
- People and face recognition data
- Labels and keywords
- Album associations
- **Score data** - Apple's aesthetic quality scores including:
  - Overall quality score
  - Curation score
  - Individual aesthetic metrics (composition, lighting, color, focus, etc.)
  - These scores are used by Apple Photos for intelligent curation and highlighting

```bash
photosafe sync macos \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --bucket S3_BUCKET_NAME \
  --base-url https://api.photosafe.example.com
```

To write JSON files for each photo (similar to iCloud dump):

```bash
photosafe sync macos \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --bucket S3_BUCKET_NAME \
  --base-url https://api.photosafe.example.com \
  --output-json
```

**Requirements:**
- macOS operating system
- `osxphotos` package (install with `pip install photosafe-cli[macos]`)

**Environment Variables:**
- `USERNAME` - API username
- `PASSWORD` - API password
- `BUCKET` - S3 bucket name (default: jmelloy-photo-backup)
- `BASE_URL` - PhotoSafe API base URL (default: http://localhost:8000)

**Options:**
- `--output-json` - Write JSON files for each photo to disk (organized by date)

### 2. iCloud Photos Sync

Syncs photos from iCloud Photos to PhotoSafe.

```bash
photosafe sync icloud \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --icloud-username YOUR_ICLOUD_EMAIL \
  --icloud-password YOUR_ICLOUD_PASSWORD \
  --bucket S3_BUCKET_NAME \
  --base-url https://api.photosafe.example.com \
  --stop-after 1000 \
  --offset 0
```

To filter by a specific library:

```bash
photosafe sync icloud \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --icloud-username YOUR_ICLOUD_EMAIL \
  --icloud-password YOUR_ICLOUD_PASSWORD \
  --bucket S3_BUCKET_NAME \
  --base-url https://api.photosafe.example.com \
  --library "My Library Name"
```

**Requirements:**
- `pyicloud` package (install with `pip install photosafe-cli[icloud]`)

**Environment Variables:**
- `USERNAME` - API username
- `PASSWORD` - API password
- `ICLOUD_USERNAME` - iCloud username/email
- `ICLOUD_PASSWORD` - iCloud password
- `BUCKET` - S3 bucket name (default: jmelloy-photo-backup)
- `BASE_URL` - PhotoSafe API base URL (default: https://api.photosafe.melloy.life)

**Options:**
- `--stop-after` - Stop after N existing photos (default: 1000)
- `--offset` - Offset for fetching photos (default: 0)
- `--batch-size` - Number of photos to process in each batch (default: 10)
- `--library` - Filter by library name (optional)

### 3. List iCloud Libraries

Lists available iCloud photo libraries.

```bash
photosafe sync list-libraries \
  --icloud-username YOUR_ICLOUD_EMAIL \
  --icloud-password YOUR_ICLOUD_PASSWORD
```

**Requirements:**
- `pyicloud` package (install with `pip install photosafe-cli[icloud]`)

**Environment Variables:**
- `ICLOUD_USERNAME` - iCloud username/email
- `ICLOUD_PASSWORD` - iCloud password

### 4. Leonardo AI Sync

Syncs AI-generated images from Leonardo.ai to PhotoSafe.

```bash
photosafe sync leonardo \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --leonardo-key YOUR_LEONARDO_API_KEY \
  --bucket S3_BUCKET_NAME \
  --base-url https://api.photosafe.example.com \
  --stop-after 5 \
  --log-level info
```

**Requirements:**
- Leonardo.ai API key
- `Pillow` package for image processing

**Environment Variables:**
- `USERNAME` - API username
- `PASSWORD` - API password
- `LEONARDO_KEY` - Leonardo.ai API key
- `BUCKET` - S3 bucket name (default: jmelloy-photo-backup)
- `BASE_URL` - PhotoSafe API base URL (default: https://api.photosafe.melloy.life)

**Options:**
- `--stop-after` - Stop after N existing photos (default: 5)
- `--log-level` - Set log level: debug, info, warning, error (default: info)

## Installation

### Base Installation

```bash
cd backend
pip install -e .
```

### With macOS Support

```bash
cd backend
pip install -e ".[macos]"
```

### With iCloud Support

```bash
cd backend
pip install -e ".[icloud]"
```

### With All Extras

```bash
cd backend
pip install -e ".[macos,icloud]"
```

## Migration from Legacy Scripts

The original sync scripts have been moved to the `legacy/` directory:

- `legacy/sync_photos/sync_photos.py` → `photosafe sync macos`
- `legacy/sync_photos_linux/photo_sync.py` → `photosafe sync icloud`
- `legacy/sync_photos_linux/leonardo.py` → `photosafe sync leonardo`

The functionality has been preserved and integrated into the unified CLI with improved:
- Command-line interface using Click
- Better help documentation
- Consistent option naming
- Environment variable support
- Error handling

## Common Usage Patterns

### Using Environment Variables

Create a `.env` file or export environment variables:

```bash
export USERNAME=myuser
export PASSWORD=mypassword
export BUCKET=my-photo-bucket
export BASE_URL=https://api.photosafe.example.com

# For iCloud sync
export ICLOUD_USERNAME=my@icloud.com
export ICLOUD_PASSWORD=myicloudpass

# For Leonardo sync
export LEONARDO_KEY=my-leonardo-api-key
```

Then run commands without explicit options:

```bash
photosafe sync macos
photosafe sync icloud
photosafe sync leonardo
```

### Interactive Password Entry

If you don't provide passwords via environment variables or command-line options, you'll be prompted to enter them interactively:

```bash
photosafe sync icloud --username myuser --password mypass
# Will prompt for iCloud credentials if not provided
```

## Notes

- All sync commands require valid AWS credentials configured for S3 access
- The sync commands perform incremental syncing based on date-based blocks
- Photos are uploaded to S3 before being registered in the PhotoSafe API
- Two-factor authentication is supported for iCloud sync
