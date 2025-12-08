# Django and FastAPI Application Parity Report

This document describes the parity between the Django app (photosafe/photosafe/) and the FastAPI app (backend/app/).

## Executive Summary

Both applications now have functional parity for core photo management features, with some intentional architectural differences documented below.

## Architecture Comparison

### Django App (photosafe/photosafe/)
- **Framework**: Django with Django REST Framework (DRF)
- **Database**: PostgreSQL (uses ArrayField, JSONField)
- **Authentication**: Token + Session authentication
- **API Pattern**: ViewSets with ModelSerializers
- **Base Path**: `/api/`

### FastAPI App (backend/app/)
- **Framework**: FastAPI with Pydantic
- **Database**: PostgreSQL and SQLite support
- **Authentication**: JWT (Bearer tokens)
- **API Pattern**: Function-based routes with Pydantic schemas
- **Base Path**: `/api/`

## Feature Parity Matrix

### ✅ Photo Management

| Feature | Django | FastAPI | Notes |
|---------|--------|---------|-------|
| List photos | ✅ | ✅ | Both support pagination |
| Create photo | ✅ | ✅ | Both support nested versions |
| Retrieve photo | ✅ | ✅ | |
| Update photo | ✅ | ✅ | Both PATCH supported |
| Delete photo | ✅ | ✅ | Added to Django |
| Filter by filename | ✅ | ✅ | Added to FastAPI |
| Filter by albums | ✅ | ✅ | Added to FastAPI |
| Filter by date | ✅ | ✅ | Added to FastAPI |
| File upload | ❌ | ✅ | FastAPI has legacy upload endpoint |
| Ownership enforcement | ✅ | ✅ | Both filter by user |

### ✅ Album Management

| Feature | Django | FastAPI | Notes |
|---------|--------|---------|-------|
| List albums | ✅ | ✅ | |
| Create album | ✅ | ✅ | |
| Retrieve album | ✅ | ✅ | |
| Update album (PATCH) | ✅ | ✅ | Added to FastAPI |
| Update album (PUT) | ✅ | ✅ | |
| Delete album | ✅ | ✅ | Added to Django |
| Update or create (PUT) | ❌ | ✅ | FastAPI only (for sync compatibility) |

### ✅ User Management

| Feature | Django | FastAPI | Notes |
|---------|--------|---------|-------|
| User registration | ✅ | ✅ | Added to Django at `/api/users/register/` |
| User login | ✅ | ✅ | Different auth mechanisms |
| Get current user | ✅ | ✅ | `/api/users/me/` vs `/api/auth/me` |
| List users | ✅ | ❌ | Django only (filtered to current user) |
| Update user | ✅ | ❌ | Django only |

## Model Parity

### Photo Model

Both applications now have equivalent Photo models with these fields:

**Core Fields:**
- uuid, masterFingerprint, original_filename, date, description, title

**Array Fields:**
- keywords, labels, albums, persons

**JSON Fields:**
- faces, place, exif, score, search_info, fields

**Boolean Flags:**
- favorite, hidden, isphoto, ismovie, burst, live_photo, portrait, screenshot, 
  slow_mo, time_lapse, hdr, selfie, panorama, intrash

**Location:**
- latitude, longitude

**Metadata:**
- uti, date_modified

**Dimensions:**
- height, width, size, orientation

**S3 Paths:**
- s3_key_path, s3_thumbnail_path, s3_edited_path, s3_original_path, s3_live_path

**Library:**
- library (string field in both)
- library_id (FK in FastAPI only)

**Upload Fields:** (Added to Django for parity)
- filename, file_path, content_type, file_size, uploaded_at

### Version Model

Identical in both applications:
- id, photo_uuid, version, s3_path, filename, width, height, size, type

### Album Model

Identical in both applications:
- uuid, title, creation_date, start_date, end_date
- Many-to-many relationship with photos

### User Model

**Django**: Uses built-in Django User model (AbstractUser)
**FastAPI**: Custom User model with equivalent fields

Both have:
- id, username, email, name, is_active, is_superuser, date_joined, last_login

### Library Model

**Django**: Does NOT have a Library model (only library string field on Photo)
**FastAPI**: Has Library model with FK relationships to User and Photo

## API Endpoints

### Authentication Endpoints

#### Django
- `POST /auth-token/` - Get auth token (DRF token)
- `POST /api/users/register/` - Register new user (ADDED)
- `GET /api/users/me/` - Get current user info

#### FastAPI
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (returns JWT)
- `GET /api/auth/me` - Get current user info

### Photo Endpoints

#### Django
- `GET /api/photos/` - List photos (with filtering: original_filename, albums, date)
- `POST /api/photos/` - Create photo
- `GET /api/photos/{uuid}/` - Get photo
- `PATCH /api/photos/{uuid}/` - Update photo
- `PUT /api/photos/{uuid}/` - Update photo
- `DELETE /api/photos/{uuid}/` - Delete photo (ADDED)

#### FastAPI
- `GET /api/photos/` - List photos (with filtering: original_filename, albums, date - ADDED)
- `POST /api/photos/` - Create photo
- `GET /api/photos/{uuid}/` - Get photo
- `PATCH /api/photos/{uuid}/` - Update photo
- `DELETE /api/photos/{uuid}/` - Delete photo
- `POST /api/photos/upload` - Upload photo file (legacy)

### Album Endpoints

#### Django
- `GET /api/albums/` - List albums
- `POST /api/albums/` - Create album
- `GET /api/albums/{uuid}/` - Get album
- `PATCH /api/albums/{uuid}/` - Update album
- `PUT /api/albums/{uuid}/` - Update album
- `DELETE /api/albums/{uuid}/` - Delete album (ADDED)

#### FastAPI
- `GET /api/albums/` - List albums
- `POST /api/albums/` - Create album
- `GET /api/albums/{uuid}/` - Get album
- `PUT /api/albums/{uuid}/` - Update or create album
- `PATCH /api/albums/{uuid}/` - Update album (ADDED)
- `DELETE /api/albums/{uuid}/` - Delete album

## Intentional Differences

These differences are by design and do not represent gaps in functionality:

### 1. Authentication Mechanism
- **Django**: Token authentication (DRF standard)
- **FastAPI**: JWT Bearer tokens
- **Reason**: Different framework standards, both secure and functional

### 2. Pagination Parameters
- **Django**: `offset` and `limit`
- **FastAPI**: `skip` and `limit`
- **Reason**: Different naming conventions, functionally equivalent

### 3. Photo Owner Field
- **Django**: `owner` FK is required (on_delete=CASCADE)
- **FastAPI**: `owner_id` is nullable
- **Reason**: FastAPI maintains backward compatibility with existing data

### 4. Library Model
- **Django**: Only has `library` string field on Photo
- **FastAPI**: Has full Library model with FK relationships
- **Reason**: FastAPI has evolved to support multiple libraries per user; Django could be updated if needed

### 5. Album Update Semantics
- **Django**: PUT requires resource to exist
- **FastAPI**: PUT creates resource if it doesn't exist (upsert)
- **Reason**: FastAPI supports sync_photos_linux compatibility

### 6. Database Support
- **Django**: PostgreSQL only (uses ArrayField)
- **FastAPI**: PostgreSQL and SQLite
- **Reason**: FastAPI has conditional type system for flexibility

## Changes Made for Parity

### Django Application
1. ✅ Added `DestroyModelMixin` to PhotoViewSet and AlbumViewSet for DELETE support
2. ✅ Added user registration endpoint (`POST /api/users/register/`)
3. ✅ Added Photo model fields: filename, file_path, content_type, file_size, uploaded_at
4. ✅ Created migration 0018_add_upload_fields.py for new fields

### FastAPI Application
1. ✅ Added filtering support to `GET /api/photos/` (original_filename, albums, date)
2. ✅ Added `PATCH /api/albums/{uuid}/` endpoint for partial updates
3. ✅ Imported IS_POSTGRESQL for database-specific filtering logic

## Testing

Parity verification tests have been added in `backend/test_parity.py`:
- Endpoint parity tests
- Model field parity tests
- Feature parity tests
- Documentation of intentional differences

All tests pass successfully.

## Recommendations

### For Production Use

1. **Choose one app**: Both apps are feature-complete but should not be run simultaneously
2. **Migration path**: If migrating from one to the other:
   - Django → FastAPI: Ensure owner_id is populated for all photos
   - FastAPI → Django: May need to handle nullable owner_id fields

### Future Enhancements

1. **Django**: Consider adding Library model to match FastAPI
2. **FastAPI**: Could add user list/update endpoints if admin functionality is needed
3. **Both**: Standardize on one authentication mechanism for easier client development

## Conclusion

Both applications now have functional parity for core photo management features. The remaining differences are intentional architectural choices that don't impact functionality. The applications can be considered equivalent for photo management purposes, with the choice between them depending on framework preference and specific deployment requirements.
