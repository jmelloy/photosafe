# Using sync_photos_linux with FastAPI Backend

## Overview

The FastAPI backend now supports the same data structure as the Django backend, making it compatible with the `sync_photos_linux` script.

## Supported Features

### Photo Model
- ✅ Full metadata support (uuid, masterFingerprint, date, title, description, etc.)
- ✅ Location data (latitude, longitude)
- ✅ Photo classifications (isphoto, ismovie, screenshot, panorama, etc.)
- ✅ EXIF data
- ✅ Multiple versions (original, medium, thumb, live)
- ✅ Library support
- ✅ S3 path tracking

### Album Model
- ✅ Album creation and updates
- ✅ Album-photo associations
- ✅ Album metadata (title, creation_date, start_date, end_date)

## API Endpoints

### Photos
- `POST /api/photos/` - Create a new photo
- `PATCH /api/photos/{uuid}/` - Update an existing photo
- `GET /api/photos/` - List all photos
- `GET /api/photos/{uuid}/` - Get a specific photo
- `DELETE /api/photos/{uuid}/` - Delete a photo

### Albums
- `POST /api/albums/` - Create a new album
- `PUT /api/albums/{uuid}/` - Update or create an album
- `GET /api/albums/` - List all albums
- `GET /api/albums/{uuid}/` - Get a specific album
- `DELETE /api/albums/{uuid}/` - Delete an album

## Compatibility Notes

### Authentication
The original `sync_photos_linux` script uses Django token authentication:
```python
r = requests.post(
    f"{base_url}/auth-token/",
    json={"username": api_username, "password": api_password}
)
```

The current FastAPI backend does **not** include authentication. To use `sync_photos_linux` with FastAPI:

**Option 1: Remove authentication from sync_photos_linux**
```python
# Comment out or remove lines 24-32 in photo_sync.py
# r = requests.post(...)
# token = r.json()["token"]
# r = requests.get(f"{base_url}/users/me", ...)

# Then remove the Authorization header from all API calls
# Change:
# headers={"Authorization": f"Token {token}", "Content-Type": "application/json"}
# To:
# headers={"Content-Type": "application/json"}
```

**Option 2: Add authentication to FastAPI backend**
You can add token-based authentication using FastAPI's security utilities:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
```

### Database Differences
- Django uses PostgreSQL with native support for ARRAY and JSONB fields
- FastAPI uses PostgreSQL with native support for ARRAY and JSONB fields
- Both backends provide full compatibility for photo metadata

### Configuration
Set the `BASE_URL` environment variable to point to your FastAPI backend:
```bash
export BASE_URL="http://localhost:8000"
export BUCKET="your-s3-bucket-name"
export PASSWORD="your-password"  # if authentication is added
```

## Testing

Run the included test script to verify compatibility:
```bash
# Start the FastAPI server
cd backend
uvicorn app.main:app --reload

# In another terminal, run the test
python test_sync_photos_linux_compat.py
```

## Example Photo Sync

```python
import requests
import json

base_url = "http://localhost:8000"

photo_data = {
    "uuid": "photo-uuid-123",
    "masterFingerprint": "fingerprint",
    "original_filename": "IMG_1234.JPG",
    "date": "2024-01-15T14:30:00",
    "library": "My Library",
    "versions": [
        {
            "version": "original",
            "s3_path": "path/to/original.jpg",
            "filename": "IMG_1234.JPG",
            "width": 4032,
            "height": 3024,
            "size": 2500000,
            "type": "jpg"
        }
    ]
}

# Create photo
response = requests.post(f"{base_url}/api/photos/", json=photo_data)
if response.status_code == 201:
    print("Photo created successfully")
elif response.status_code == 400 and "already exists" in response.text:
    # Update existing photo
    response = requests.patch(
        f"{base_url}/api/photos/{photo_data['uuid']}/",
        json=photo_data
    )
    print("Photo updated successfully")
```

## Differences from Django Backend

| Feature | Django Backend | FastAPI Backend | Notes |
|---------|---------------|-----------------|-------|
| Authentication | Token-based | Not implemented | Can be added if needed |
| User/Owner | Required | Not implemented | Photos not tied to users yet |
| Database | PostgreSQL | PostgreSQL | Full compatibility |
| Array Fields | Native ARRAY | Native ARRAY | Full compatibility |
| JSONB Fields | Native JSONB | Native JSONB | Full compatibility |

## Future Enhancements

- [ ] Add token-based authentication
- [ ] Add user/owner support
- [ ] Add PostgreSQL support for production
- [ ] Add filtering and search capabilities
- [ ] Add pagination
- [ ] Add batch operations
