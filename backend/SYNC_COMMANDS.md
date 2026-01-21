# Sync Commands

## Installation

```bash
cd backend
pip install -e .              # Base
pip install -e ".[macos]"     # + macOS Photos support
pip install -e ".[icloud]"    # + iCloud support
pip install -e ".[macos,icloud]"  # All
```

## Commands

### macOS Photos
```bash
photosafe sync macos --username USER --password PASS --bucket S3_BUCKET --base-url URL
# --output-json: Write JSON files for each photo
```
Requires macOS + `osxphotos` package.

### iCloud Photos
```bash
photosafe sync icloud --username USER --password PASS \
  --icloud-username ICLOUD_EMAIL --icloud-password ICLOUD_PASS \
  --bucket S3_BUCKET --base-url URL \
  --stop-after 1000 --offset 0 --batch-size 10 --library "Library Name"
```
Requires `pyicloud` package. Supports 2FA. Auto-processes shared albums.

### List iCloud Libraries
```bash
photosafe sync list-libraries --icloud-username EMAIL --icloud-password PASS
```

### Leonardo AI
```bash
photosafe sync leonardo --username USER --password PASS \
  --leonardo-key API_KEY --bucket S3_BUCKET --base-url URL \
  --stop-after 5 --log-level info
```

## Environment Variables

```bash
USERNAME, PASSWORD          # API credentials
BUCKET                      # S3 bucket (default: jmelloy-photo-backup)
BASE_URL                    # API URL (default: http://localhost:8000)
ICLOUD_USERNAME, ICLOUD_PASSWORD  # iCloud credentials
LEONARDO_KEY                # Leonardo.ai API key
```

All sync commands require AWS credentials configured for S3 access.
