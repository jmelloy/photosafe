# PhotoSafe Gallery - Claude AI Assistant Guide

This document provides comprehensive guidance for AI assistants (particularly Claude) working on the PhotoSafe codebase. It covers architecture, conventions, workflows, and critical information needed to make effective changes.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture Summary](#architecture-summary)
- [Codebase Structure](#codebase-structure)
- [Critical Setup Requirements](#critical-setup-requirements)
- [Development Workflows](#development-workflows)
- [Database & Migrations](#database--migrations)
- [Testing Strategy](#testing-strategy)
- [Authentication & Authorization](#authentication--authorization)
- [API Design Patterns](#api-design-patterns)
- [Frontend Architecture](#frontend-architecture)
- [CLI Commands](#cli-commands)
- [Code Conventions](#code-conventions)
- [Common Gotchas](#common-gotchas)
- [File Organization Patterns](#file-organization-patterns)
- [Making Changes: Best Practices](#making-changes-best-practices)

---

## Project Overview

**PhotoSafe** is a modern, production-ready photo gallery application with:

- **Backend**: FastAPI (Python 3.13+) with SQLModel/SQLAlchemy ORM
- **Frontend**: Vue 3 (TypeScript) with Composition API
- **Database**: PostgreSQL 16+ (required, no SQLite support)
- **Authentication**: Dual system (JWT for web, Personal Access Tokens for CLI)
- **Storage**: Hybrid (S3 + local filesystem)
- **CLI**: Comprehensive Click-based CLI for bulk operations
- **Sync**: Multi-source photo sync (macOS Photos, iCloud, Leonardo.ai)
- **Testing**: pytest (backend) + Vitest (frontend) with dedicated test database
- **Deployment**: Docker Compose with dev/prod configurations

### Key Features

- Multi-library support per user
- Rich photo metadata (EXIF, geolocation, faces, labels)
- Advanced search and filtering
- Album management
- Map view with Leaflet
- Background task system for place lookup and aggregation
- Batch photo operations
- S3 integration for storage

---

## Architecture Summary

### High-Level Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   Vue 3     │────▶│   FastAPI    │────▶│ PostgreSQL │
│  Frontend   │     │   Backend    │     │  Database  │
└─────────────┘     └──────────────┘     └────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   S3/Local   │
                    │   Storage    │
                    └──────────────┘
```

### Technology Stack

**Backend:**
- FastAPI 0.115.5+ (ASGI web framework)
- SQLModel 0.0.22+ (Pydantic + SQLAlchemy)
- Alembic 1.17.2+ (database migrations)
- PostgreSQL driver: psycopg2-binary
- Auth: python-jose (JWT), bcrypt (passwords)
- CLI: Click 8.0+
- Sync: osxphotos (macOS), pyicloud (iCloud)
- Utilities: boto3 (S3), Pillow (images), tqdm (progress bars)

**Frontend:**
- Vue 3.5+ with Composition API
- Vite 6.0+ (build tool)
- TypeScript 5.6+
- Axios (HTTP client)
- Vue Router (routing)
- Leaflet (maps)
- Vitest (testing)

**Infrastructure:**
- PostgreSQL 16+
- Docker & Docker Compose
- GitHub Actions (CI/CD)
- S3-compatible storage (optional)

---

## Codebase Structure

### Repository Layout

```
photosafe/
├── backend/              # Python FastAPI backend
│   ├── app/              # Main application
│   │   ├── main.py       # FastAPI app + router registration
│   │   ├── database.py   # DB config + session management
│   │   ├── models.py     # SQLModel database models
│   │   ├── auth.py       # JWT + PAT authentication
│   │   ├── utils.py      # Utility functions
│   │   ├── version.py    # Version management
│   │   └── routers/      # API endpoints
│   │       ├── auth.py       # /api/auth/* (login, register, tokens)
│   │       ├── photos.py     # /api/photos/* (CRUD, batch, filters)
│   │       ├── albums.py     # /api/albums/*
│   │       ├── places.py     # /api/places/*, /api/place-summaries/*
│   │       └── search.py     # /api/search/*
│   ├── cli/              # Click CLI commands
│   │   ├── main.py           # CLI entry point
│   │   ├── user_commands.py  # User management
│   │   ├── library_commands.py
│   │   ├── import_commands.py
│   │   ├── sync_commands.py  # macOS/iCloud/Leonardo sync
│   │   ├── sync_tools.py     # Shared sync utilities
│   │   ├── task_commands.py  # Background tasks
│   │   └── maintenance_commands.py
│   ├── alembic/          # Database migrations
│   │   ├── versions/     # Migration files
│   │   └── env.py        # Alembic config
│   ├── tests/            # pytest tests
│   │   ├── conftest.py   # Fixtures + test config
│   │   ├── unit/         # Unit tests
│   │   ├── integration/  # API integration tests
│   │   └── fixtures/     # Test data files
│   ├── pyproject.toml    # Dependencies + CLI registration
│   ├── pytest.ini        # pytest configuration
│   ├── .env.example      # Environment template
│   └── Dockerfile        # Backend container
│
├── frontend/             # Vue 3 frontend
│   ├── src/
│   │   ├── main.ts       # Vue app entry point
│   │   ├── App.vue       # Root component (auth handling)
│   │   ├── router/       # Vue Router config
│   │   │   └── index.ts
│   │   ├── views/        # Page components
│   │   │   ├── HomePage.vue
│   │   │   ├── SearchPage.vue
│   │   │   ├── PhotoDetailPage.vue
│   │   │   ├── PhotoMapView.vue
│   │   │   └── VersionPage.vue
│   │   ├── components/   # Reusable components
│   │   │   ├── Login.vue
│   │   │   ├── Register.vue
│   │   │   ├── PhotoGallery.vue
│   │   │   ├── PhotoUpload.vue
│   │   │   ├── PhotoMap.vue
│   │   │   └── LoadingSpinner.vue
│   │   ├── api/          # API client modules
│   │   │   ├── client.ts     # Axios config + interceptors
│   │   │   ├── auth.ts       # Auth API calls
│   │   │   ├── photos.ts     # Photo API calls
│   │   │   ├── places.ts
│   │   │   ├── search.ts
│   │   │   └── version.ts
│   │   ├── types/        # TypeScript types
│   │   │   ├── api.ts
│   │   │   └── auth.ts
│   │   └── utils/        # Utility functions
│   │       ├── formatPlace.ts
│   │       ├── queryParams.ts
│   │       ├── errorHandling.ts
│   │       ├── format.ts
│   │       └── imageUrl.ts
│   ├── package.json      # NPM dependencies + scripts
│   ├── vite.config.ts    # Vite + Vitest config
│   ├── tsconfig.json     # TypeScript config
│   └── Dockerfile        # Frontend container
│
├── iosapp/               # iOS/tvOS Swift app
├── .github/
│   ├── workflows/
│   │   ├── backend-tests.yml   # Backend CI (pytest + coverage)
│   │   └── frontend-tests.yml  # Frontend CI (Vitest + build)
│   └── copilot-instructions.md # GitHub Copilot guidance
├── docker-compose.yml        # Dev services
├── docker-compose.prod.yml   # Production override
├── build.sh                  # Build script with git SHA
├── README.md                 # Main documentation
├── CONTRIBUTING.md           # Contribution guide
└── CLAUDE.md                 # This file
```

---

## Critical Setup Requirements

### Python Version Requirement

⚠️ **CRITICAL**: Backend requires **Python 3.13+** (strict requirement)
- Python 3.12 or earlier will fail
- Use Docker if local Python version is older
- Check version: `python --version`

### Database Requirements

⚠️ **PostgreSQL 16+ is REQUIRED**
- No SQLite support (codebase uses PostgreSQL-specific features)
- Dev database: `localhost:5432`
- Test database: `localhost:5433` (separate to avoid conflicts)
- Both databases must be running for development + testing

### Environment Variables

**Backend** (`backend/.env`):
```bash
# Required
SECRET_KEY=generate-with-openssl-rand-hex-32
DATABASE_URL=postgresql://photosafe:photosafe@localhost:5432/photosafe

# Optional
ACCESS_TOKEN_EXPIRE_MINUTES=30
TEST_DATABASE_URL=postgresql://photosafe:photosafe@localhost:5433/photosafe_test
```

**Frontend** (build time):
- `VITE_API_URL`: Backend URL (default: `/api` via proxy)
- `GIT_SHA`: Injected by build script for version tracking

---

## Development Workflows

### Backend Development

#### Initial Setup

```bash
cd backend

# Install dependencies (Python 3.13+ required)
pip install -e .[test]

# Run database migrations (CRITICAL - always run this!)
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

**Important**: Always run `alembic upgrade head` after:
- Initial clone
- Pulling new migrations
- Switching branches
- Before running tests

#### Making Backend Changes

1. **Before changing models**:
   - Ensure migrations are up to date: `alembic upgrade head`
   - Review existing model in `backend/app/models.py`

2. **After changing models**:
   ```bash
   # Generate migration
   alembic revision --autogenerate -m "Description of changes"

   # Review generated migration in alembic/versions/
   # IMPORTANT: Auto-generated migrations may need manual adjustments

   # Apply migration
   alembic upgrade head
   ```

3. **Testing changes**:
   ```bash
   # Run all tests
   ./run_tests.sh

   # Or manually
   docker compose --profile test up -d test-db
   pytest -v --cov=app --cov=cli
   ```

4. **Linting**:
   ```bash
   ruff check --fix .
   ```

#### Common Backend Tasks

**Add new API endpoint:**
1. Add route function in appropriate router (e.g., `backend/app/routers/photos.py`)
2. Define Pydantic schemas if needed
3. Add tests in `backend/tests/integration/`
4. Update this documentation if it's a major feature

**Add new CLI command:**
1. Add command in appropriate file (e.g., `backend/cli/user_commands.py`)
2. Register in `backend/cli/main.py` if new command group
3. Add tests in `backend/tests/integration/test_cli.py`
4. Update `README.md` and `backend/SYNC_COMMANDS.md` if applicable

### Frontend Development

#### Initial Setup

```bash
cd frontend

# Install dependencies (use 'ci' for reproducible builds)
npm ci

# Start development server
npm run dev
```

Frontend available at `http://localhost:5173` with hot module replacement (HMR).

#### Making Frontend Changes

1. **Component changes**:
   - Vue components use Composition API with `<script setup>` syntax
   - TypeScript is required for all `.ts` and `.vue` files
   - Add tests for non-trivial logic

2. **API changes**:
   - Update types in `frontend/src/types/api.ts`
   - Update API client in relevant `frontend/src/api/*.ts` file
   - Ensure error handling is in place

3. **Testing changes**:
   ```bash
   # Run tests in watch mode
   npm run test

   # Run tests once (CI mode)
   npm run test:run

   # Run with UI
   npm run test:ui
   ```

4. **Building**:
   ```bash
   npm run build
   npm run preview  # Preview production build
   ```

### Docker Development

#### Development Mode

```bash
# Start all services (db, backend, frontend)
docker-compose up --build

# Services:
# - PostgreSQL: localhost:5432
# - Backend: localhost:8000
# - Frontend: localhost:5173
# - API Docs: localhost:8000/docs
```

**Features**:
- Source code volume-mounted for hot reload
- Database persisted in Docker volume

#### Production Mode

```bash
# Create production environment file
cp .env.production.example .env.production
# Edit .env.production - set strong POSTGRES_PASSWORD!

# Build with git SHA
./build.sh

# Start production services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.production up -d
```

**Key differences**:
- No volume mounts (code baked into images)
- No reload on file changes
- Optimized for performance

#### Test Database

```bash
# Start test database only
docker compose --profile test up -d test-db

# Access at localhost:5433
```

---

## Database & Migrations

### Database Architecture

**PostgreSQL-Specific Features Used:**
- UUID types (native UUID, not strings)
- JSONB columns (for flexible metadata: `exif`, `faces`, `place`, etc.)
- ARRAY columns (for `keywords`, `labels`, `albums`, `persons`)
- Full-text search capabilities
- Advanced indexing

**Key Models** (see `backend/app/models.py`):

1. **User**: Authentication and ownership
   - Relationships: `photos`, `libraries`, `personal_access_tokens`

2. **Photo**: Main entity with rich metadata
   - UUID primary key
   - JSONB fields: `exif`, `faces`, `place`, `score`, `search_info`, `fields`
   - ARRAY fields: `keywords`, `labels`, `albums`, `persons`
   - Boolean flags: `favorite`, `hidden`, `isphoto`, `ismovie`, `portrait`, `screenshot`, etc.
   - S3 paths: `s3_key_path`, `s3_thumbnail_path`, `s3_edited_path`, `s3_original_path`
   - Soft delete: `deleted_at` timestamp
   - Computed property: `url` (returns S3 path or local path)

3. **Library**: Multi-library support
   - Each user can have multiple libraries
   - Photos belong to one library

4. **Album**: Photo groupings (many-to-many via `album_photos` table)

5. **Version**: Photo variants (thumbnails, different sizes)

6. **Task**: Background task tracking
   - Used for place lookup, place summary generation

7. **PlaceSummary**: Aggregated location data
   - One record per unique coordinate
   - Unique constraint on `latitude`/`longitude`

8. **PersonalAccessToken**: Long-lived API tokens for CLI
   - Hashed storage
   - Expiration support

### Migration Workflow

**Before modifying models:**
```bash
alembic upgrade head  # Ensure DB is current
```

**After modifying models:**
```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add field X to Photo model"

# IMPORTANT: Review the generated file!
# Location: backend/alembic/versions/XXXXXX_description.py
# Check for:
# - Correct column types
# - Proper indexes
# - Data migration needs
# - Downgrade logic

# Apply migration
alembic upgrade head

# Test rollback (good practice)
alembic downgrade -1
alembic upgrade head
```

**Common migration commands:**
```bash
alembic history              # View migration history
alembic current              # Show current revision
alembic upgrade head         # Apply all pending migrations
alembic downgrade -1         # Rollback one migration
alembic downgrade <revision> # Rollback to specific revision
```

**Migration Best Practices:**
1. **Always review auto-generated migrations** - Alembic's autogenerate is helpful but not perfect
2. **Test migrations both ways** - Ensure `upgrade` and `downgrade` work
3. **Be careful with data migrations** - Use `op.execute()` for complex data changes
4. **Never edit applied migrations** - Create a new migration to fix issues
5. **Coordinate with team** - Migrations affect everyone's local database

---

## Testing Strategy

### Backend Testing (pytest)

**Test Database:**
- Port: `5433` (not 5432, to avoid dev DB conflicts)
- Connection: `postgresql://photosafe:photosafe@localhost:5433/photosafe_test`
- Managed by `./run_tests.sh` or manually via `docker compose --profile test up -d test-db`

**Test Organization:**
```
backend/tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests (fast, no DB)
│   ├── test_filtering.py
│   ├── test_version.py
│   ├── test_tasks.py
│   └── test_maintenance_commands.py
└── integration/          # Integration tests (use DB)
    ├── test_auth_photos.py
    ├── test_albums.py
    ├── test_search.py
    ├── test_sync.py
    └── test_cli.py
```

**Key Fixtures** (from `conftest.py`):
- `engine`: Session-scoped DB engine (runs Alembic migrations once)
- `db_session`: Function-scoped clean session (tables cleared after each test)
- `client`: FastAPI TestClient with DB override
- `test_user`: Pre-created user for tests
- `test_library`: Pre-created library
- `auth_token`: JWT token for authenticated requests
- `runner`: Click CliRunner for CLI tests

**Running Tests:**
```bash
cd backend

# Easiest: Auto-manages test DB
./run_tests.sh

# Manual:
docker compose --profile test up -d test-db
pytest -v --cov=app --cov=cli
pytest tests/unit/           # Only unit tests
pytest tests/integration/    # Only integration tests
pytest -k "test_name"        # Specific test
pytest -m "slow"             # Tests marked as slow
```

**Writing Tests:**

Example API test:
```python
def test_create_photo(client, auth_token, test_library):
    response = client.post(
        "/api/photos/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "Test Photo",
            "library_id": test_library.id,
            # ... other fields
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Photo"
```

Example CLI test:
```python
def test_user_create(runner, db_session):
    result = runner.invoke(cli, [
        "user", "create",
        "--username", "testuser",
        "--email", "test@example.com"
    ])
    assert result.exit_code == 0
    assert "created successfully" in result.output
```

### Frontend Testing (Vitest)

**Test Organization:**
- Tests co-located with source: `*.test.ts`
- Examples: `client.test.ts`, `format.test.ts`, `PhotoMap.test.ts`

**Running Tests:**
```bash
cd frontend

npm run test        # Watch mode
npm run test:run    # CI mode (single run)
npm run test:ui     # Interactive UI
```

**Writing Tests:**

Example utility test:
```typescript
import { describe, it, expect } from 'vitest'
import { formatPlace } from './formatPlace'

describe('formatPlace', () => {
  it('formats place with city and country', () => {
    const place = {
      city: 'San Francisco',
      country: 'United States'
    }
    expect(formatPlace(place)).toBe('San Francisco, United States')
  })
})
```

### Test Best Practices

1. **Isolation**: Each test should be independent (fixtures handle cleanup)
2. **Clarity**: Test names should describe what they test
3. **Coverage**: Aim for high coverage but prioritize critical paths
4. **Speed**: Keep tests fast (use mocks for external services)
5. **Data**: Use fixtures for test data, not hardcoded values

---

## Authentication & Authorization

### Dual Authentication System

PhotoSafe uses two authentication methods:

#### 1. JWT Tokens (Web Frontend)

**Flow:**
1. User logs in via `/api/auth/login` with username/password
2. Backend returns access token (30 min) and refresh token (7 days)
3. Frontend stores tokens in localStorage
4. Access token sent in `Authorization: Bearer <token>` header
5. On 401 error, frontend auto-refreshes using refresh token

**Implementation:**
- Location: `backend/app/auth.py`
- Algorithm: HS256
- Secret: `SECRET_KEY` environment variable
- Token types: "access" and "refresh"
- Dependency: `get_current_active_user(token: str = Depends(oauth2_scheme))`

**Frontend handling:**
- Axios request interceptor adds token
- Axios response interceptor handles 401 refresh
- Token management: `frontend/src/api/client.ts`

#### 2. Personal Access Tokens (CLI/API)

**Flow:**
1. User creates PAT via web UI or API: `POST /api/auth/tokens`
2. Backend returns token string (only shown once)
3. User uses token in `Authorization: Bearer <PAT>` header
4. Backend validates via bcrypt hash comparison

**Implementation:**
- Location: `backend/app/auth.py` (same `get_current_active_user` dependency)
- Storage: Hashed with bcrypt in `personal_access_tokens` table
- Features: Named tokens, optional expiration, last-used tracking
- Documentation: `backend/PERSONAL_ACCESS_TOKENS.md`

**CLI usage:**
```bash
# Create token
photosafe user create --username john --email john@example.com
# Login to get JWT, then create PAT via web UI

# Use token in API calls
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/photos
```

### Authorization Pattern

**Owner-based access control:**
- All photos, libraries, albums are user-owned
- Queries automatically filter by `owner_id = current_user.id`
- Superusers can bypass (for admin operations)

**Example:**
```python
@router.get("/api/photos/")
async def get_photos(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Automatically filters to current user's photos
    photos = db.query(Photo).filter(Photo.owner_id == current_user.id).all()
    return photos
```

### Password Security

- Hashing: bcrypt with automatic salt generation
- Storage: Only hashed passwords in database
- Validation: Timing-safe comparison via bcrypt

---

## API Design Patterns

### RESTful Conventions

**Standard CRUD endpoints:**
```
GET    /api/resource/           # List all (paginated)
GET    /api/resource/{id}/      # Get single
POST   /api/resource/           # Create
PATCH  /api/resource/{id}/      # Partial update
PUT    /api/resource/{id}/      # Full update/create
DELETE /api/resource/{id}/      # Delete
```

**Note**: Trailing slashes are used consistently.

### Pagination

**Pattern**: Cursor-based pagination (no total count for performance)

```python
@router.get("/api/photos/")
async def get_photos(
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    # ... filters
):
    photos = query.limit(limit + 1).offset(offset).all()
    has_more = len(photos) > limit
    return {
        "photos": photos[:limit],
        "has_more": has_more,
        "next_offset": offset + limit if has_more else None
    }
```

**Rationale**: Counting total records is expensive for large datasets.

### Filtering & Searching

**Query parameters for filtering:**
```
GET /api/photos?favorite=true&date_start=2024-01-01&location=San+Francisco
```

**Available filters** (see `backend/app/routers/photos.py`):
- Date ranges: `date_start`, `date_end`
- Boolean flags: `favorite`, `hidden`, `isphoto`, `ismovie`, `portrait`, etc.
- Location: `location` (text search in place hierarchy)
- Keywords: `keywords` (array filter)
- Albums: `album_uuid` (photos in specific album)
- Search query: `q` (full-text search across multiple fields)

**Filter metadata endpoint:**
```
GET /api/photos/filters/  # Returns available values for filtering
```

### Batch Operations

**Pattern**: Single endpoint for bulk create/update

```python
@router.post("/api/photos/batch/")
async def batch_photos(photos: List[PhotoCreate], ...):
    # Process multiple photos in one transaction
    created = []
    for photo_data in photos:
        photo = Photo(**photo_data.dict())
        db.add(photo)
        created.append(photo)
    db.commit()
    return {"created": created}
```

**Use case**: Importing multiple photos from CLI or sync operations.

### Error Handling

**Standard HTTP status codes:**
- `200 OK`: Successful GET/PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Missing/invalid authentication
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource doesn't exist
- `422 Unprocessable Entity`: Pydantic validation error
- `500 Internal Server Error`: Server error

**Error response format:**
```json
{
  "detail": "Photo not found"
}
```

---

## Frontend Architecture

### Vue 3 Composition API

**Pattern**: `<script setup>` with TypeScript

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getPhotos } from '@/api/photos'
import type { Photo } from '@/types/api'

const photos = ref<Photo[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const data = await getPhotos({ limit: 50 })
    photos.value = data.photos
  } catch (error) {
    console.error('Failed to load photos:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="loading">Loading...</div>
  <div v-else>
    <div v-for="photo in photos" :key="photo.uuid">
      {{ photo.title }}
    </div>
  </div>
</template>
```

### State Management

**No global state library**: Uses Vue 3 reactivity with local state

**Authentication state** (managed in `App.vue`):
```typescript
const isAuthenticatedRef = ref<boolean>(false)
const currentUser = ref<User | null>(null)

const handleLoginSuccess = (token: string, refreshToken: string) => {
  setToken(token)
  setRefreshToken(refreshToken)
  isAuthenticatedRef.value = true
  loadCurrentUser()
}
```

**Component state**: Each component manages its own reactive state

**Prop drilling**: Props passed down, events emitted up (standard Vue pattern)

### Routing

**Vue Router configuration** (`frontend/src/router/index.ts`):

```typescript
const routes = [
  { path: '/', component: HomePage },
  { path: '/search', component: SearchPage },
  { path: '/photos/:uuid', component: PhotoDetailPage },
  { path: '/map', component: PhotoMapView },
  { path: '/version', component: VersionPage }
]
```

**Navigation:**
```vue
<router-link to="/search">Search</router-link>
<button @click="router.push({ name: 'photo', params: { uuid } })">
  View Photo
</button>
```

### API Client Architecture

**Centralized Axios instance** (`frontend/src/api/client.ts`):

```typescript
const apiClient = axios.create({
  baseURL: '/api',
})

// Request interceptor: Add auth token
apiClient.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: Handle 401 refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Attempt token refresh
      const refreshToken = getRefreshToken()
      if (refreshToken) {
        // Refresh logic...
      }
    }
    return Promise.reject(error)
  }
)
```

**API modules** (one per resource):
- `auth.ts`: login, register, logout, getCurrentUser, createToken
- `photos.ts`: getPhotos, getPhoto, uploadPhoto, deletePhoto, getAvailableFilters
- `places.ts`: getPlaceSummaries
- `search.ts`: search
- `version.ts`: getVersion

### Type Safety

**TypeScript interfaces** (`frontend/src/types/api.ts`):

```typescript
export interface Photo {
  uuid: string
  title: string
  description?: string
  date?: string
  url?: string
  favorite: boolean
  hidden: boolean
  // ... all other fields
}

export interface PhotoListResponse {
  photos: Photo[]
  has_more: boolean
  next_offset?: number
}
```

**Type inference**:
```typescript
const photos = ref<Photo[]>([])  // Typed array
const photo = await getPhoto(uuid) // Inferred as Photo
```

---

## CLI Commands

### CLI Architecture

**Framework**: Click (Python CLI framework)

**Entry point**: `photosafe` command (registered in `pyproject.toml`)

**Command structure**:
```
photosafe
├── user
│   ├── create
│   ├── list
│   ├── delete
│   └── set-password
├── library
│   ├── create
│   ├── list
│   └── delete
├── import (folder import with metadata)
├── sync
│   ├── macos (macOS Photos)
│   ├── icloud (iCloud Photos)
│   ├── leonardo (Leonardo.ai)
│   └── list-libraries (iCloud)
├── task
│   ├── lookup-places
│   ├── update-place-summary
│   └── list
└── maintenance
    └── (various maintenance commands)
```

### Common CLI Usage

**User management:**
```bash
# Create user
photosafe user create --username john --email john@example.com

# List users
photosafe user list

# Set password
photosafe user set-password --username john
```

**Library management:**
```bash
# Create library
photosafe library create --username john --name "My Photos"

# List libraries
photosafe library list --username john
```

**Import photos:**
```bash
# Import from folder with S3 upload
photosafe import \
  --username john \
  --library-id 1 \
  --folder /path/to/photos \
  --bucket my-s3-bucket
```

**Sync from sources:**
```bash
# macOS Photos (requires osxphotos)
photosafe sync macos \
  --username john \
  --bucket my-bucket \
  --library-id 1

# iCloud Photos (requires pyicloud)
photosafe sync icloud \
  --username john \
  --icloud-username user@icloud.com \
  --bucket my-bucket \
  --library-id 1

# Leonardo.ai
photosafe sync leonardo \
  --username john \
  --library-id 1
```

**Background tasks:**
```bash
# Reverse geocode photos
photosafe task lookup-places --limit 100

# Update place summaries
photosafe task update-place-summary

# List task status
photosafe task list
```

### CLI Development

**Adding a new command:**

1. Add function in appropriate file (e.g., `backend/cli/user_commands.py`):
```python
@user_group.command("example")
@click.option("--username", required=True)
def example_command(username: str):
    """Example command description."""
    click.echo(f"Running example for {username}")
    # Implementation...
```

2. If new command group, register in `backend/cli/main.py`:
```python
cli.add_command(example_group)
```

3. Add tests in `backend/tests/integration/test_cli.py`:
```python
def test_example_command(runner):
    result = runner.invoke(cli, ["user", "example", "--username", "john"])
    assert result.exit_code == 0
```

**CLI Best Practices:**
- Use Click's validation (`required=True`, types, choices)
- Provide helpful error messages with `click.echo()`
- Use `tqdm` for progress bars on long operations
- Always wrap DB operations in try/except
- Use `click.confirm()` for destructive operations

---

## Code Conventions

### Python (Backend)

**Style**: PEP 8 with pylint + ruff

**Naming**:
- `snake_case`: functions, variables, module names
- `PascalCase`: classes
- `UPPER_CASE`: constants
- Private: prefix with `_` (e.g., `_internal_function`)

**Formatting**:
- Line length: 100 characters (see `pyproject.toml`)
- Indentation: 4 spaces
- Imports: Grouped (standard, third-party, local) with blank lines between

**Docstrings**: Optional (disabled in pylint for FastAPI/CLI apps)
- Use for complex logic or public APIs
- Not required for simple CRUD endpoints

**Type hints**: Encouraged but not enforced
```python
def get_photo(db: Session, photo_uuid: str) -> Photo | None:
    return db.query(Photo).filter(Photo.uuid == photo_uuid).first()
```

**Linting**:
```bash
ruff check --fix .  # Auto-fix issues
```

### TypeScript (Frontend)

**Style**: ESLint configuration

**Naming**:
- `camelCase`: functions, variables
- `PascalCase`: types, interfaces, components
- `UPPER_CASE`: constants

**Types**:
- Use interfaces for objects: `interface Photo { ... }`
- Use types for unions/aliases: `type Status = 'loading' | 'success' | 'error'`
- Avoid `any` (use `unknown` if type is truly unknown)

**Vue conventions**:
- Component names: `PascalCase.vue` (e.g., `PhotoGallery.vue`)
- Props: Define with TypeScript interfaces
- Emits: Define with `defineEmits<{ ... }>()`

Example:
```vue
<script setup lang="ts">
interface Props {
  photos: Photo[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  select: [photo: Photo]
  delete: [uuid: string]
}>()
</script>
```

### Database

**Naming**:
- Tables: lowercase plural (e.g., `users`, `photos`, `albums`)
- Columns: lowercase snake_case (e.g., `created_at`, `owner_id`)
- Foreign keys: `{table}_id` (e.g., `user_id`, `library_id`)

**SQLModel models**:
```python
class Photo(SQLModel, table=True):
    __tablename__ = "photos"

    uuid: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str
    owner_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Git Commits

**Format**: Imperative mood, concise
```
Add place summary aggregation endpoint
Fix photo upload S3 path handling
Update README with CLI examples
Refactor auth token refresh logic
```

**First line**: Under 72 characters
**Body**: Optional, detailed explanation if needed

**Conventional commits** (optional but recommended):
```
feat: Add map view for photos
fix: Resolve token refresh race condition
docs: Update CLAUDE.md with testing guide
chore: Bump version to 2025.12.37
test: Add integration tests for albums
```

---

## Common Gotchas

### 1. Migration Not Applied

**Symptom**: `alembic.util.exc.CommandError: Target database is not up to date.`

**Solution**:
```bash
cd backend
alembic upgrade head
```

**Prevention**: Always run `alembic upgrade head` after pulling or switching branches.

---

### 2. Test Database Not Running

**Symptom**: Tests fail with database connection errors

**Solution**:
```bash
# Start test database
docker compose --profile test up -d test-db

# Or use the script
cd backend
./run_tests.sh
```

**Note**: Test DB runs on port **5433**, not 5432.

---

### 3. Python Version Mismatch

**Symptom**: Import errors, syntax errors, or dependency installation failures

**Solution**: Verify Python version
```bash
python --version  # Must be 3.13+
```

**Fix**: Use Docker or install Python 3.13+
```bash
# Docker development
docker-compose up --build

# Or install Python 3.13
# (varies by OS)
```

---

### 4. Frontend Proxy Not Working

**Symptom**: API calls fail with CORS errors or 404

**Cause**: Vite proxy only works in dev mode (`npm run dev`)

**Solution**:
- For development: Ensure backend is running on `localhost:8000`
- For production build: Set `VITE_API_URL` environment variable

**Vite config** (`frontend/vite.config.ts`):
```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/uploads': 'http://localhost:8000'
  }
}
```

---

### 5. Missing Environment Variables

**Symptom**: Backend fails to start with KeyError or validation error

**Solution**: Copy example and configure
```bash
cd backend
cp .env.example .env
# Edit .env and set SECRET_KEY, DATABASE_URL
```

**Generate SECRET_KEY**:
```bash
openssl rand -hex 32
```

---

### 6. S3 Paths vs Local Paths

**Symptom**: Images not displaying, broken URLs

**Cause**: Photo model has multiple path fields (S3 vs local)

**Understanding**: `Photo.url` property returns S3 path if available, else local path
```python
@property
def url(self) -> str | None:
    if self.s3_key_path:
        return self.s3_key_path
    return self.path
```

**Solution**: Always use `photo.url` in frontend, not `photo.path` or `photo.s3_key_path` directly.

---

### 7. Token Refresh Race Condition

**Symptom**: Multiple simultaneous requests cause repeated 401 errors

**Solution**: Already handled in `frontend/src/api/client.ts` with request queue:
```typescript
let isRefreshing = false
let failedQueue: any[] = []

// Queue requests during refresh
if (error.response?.status === 401 && !originalRequest._retry) {
  if (isRefreshing) {
    // Add to queue
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject })
    }).then(token => { /* retry */ })
  }
  // Refresh token logic...
}
```

**Note**: If modifying auth logic, maintain this pattern.

---

### 8. Auto-Generated Migrations Need Review

**Symptom**: Migration doesn't capture all changes or fails to apply

**Cause**: Alembic's autogenerate has limitations:
- Doesn't detect table/column renames (sees as drop + add)
- May miss index or constraint changes
- Can't infer data migrations

**Solution**: Always review and edit generated migrations
```bash
alembic revision --autogenerate -m "description"
# Review backend/alembic/versions/XXXX_description.py
# Edit if necessary
alembic upgrade head
```

---

### 9. Calendar Versioning

**Symptom**: Version number format looks unusual (e.g., `2025.12.36`)

**Explanation**: Project uses calendar versioning (YYYY.MM.PATCH), not semantic versioning

**Auto-increment**: CI workflow bumps version on merge to `main`
- `backend/.github/workflows/backend-tests.yml` has increment step
- Commits with `[skip ci]` to avoid infinite loop

**Manual versioning**: If needed, edit `backend/pyproject.toml` directly.

---

### 10. Production Volume Mounts

**Symptom**: Production build doesn't reflect code changes

**Cause**: Using `docker-compose.yml` alone mounts source code volumes

**Solution**: Use production override
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Difference**: `docker-compose.prod.yml` removes volume mounts so built code in images is used.

---

## File Organization Patterns

### Backend File Locations

**When adding/modifying backend code:**

| Change | File(s) |
|--------|---------|
| Database model | `backend/app/models.py` |
| Pydantic schemas | `backend/app/models.py` (SQLModel combines both) or create separate in router file |
| API endpoint | `backend/app/routers/{resource}.py` |
| Authentication logic | `backend/app/auth.py` |
| Database config | `backend/app/database.py` |
| Utility function | `backend/app/utils.py` |
| CLI command | `backend/cli/{group}_commands.py` |
| Migration | `alembic revision --autogenerate` → `backend/alembic/versions/` |
| Test (unit) | `backend/tests/unit/test_{module}.py` |
| Test (integration) | `backend/tests/integration/test_{feature}.py` |
| Test fixture | `backend/tests/conftest.py` |

### Frontend File Locations

**When adding/modifying frontend code:**

| Change | File(s) |
|--------|---------|
| Page component | `frontend/src/views/{PageName}.vue` |
| Reusable component | `frontend/src/components/{ComponentName}.vue` |
| API client function | `frontend/src/api/{resource}.ts` |
| TypeScript interface | `frontend/src/types/api.ts` or `frontend/src/types/{feature}.ts` |
| Route | `frontend/src/router/index.ts` |
| Utility function | `frontend/src/utils/{module}.ts` |
| Global style | `frontend/src/style.css` |
| Test | `frontend/src/{module}.test.ts` |

---

## Making Changes: Best Practices

### General Guidelines

1. **Read before writing**: Always read existing code in the area you're modifying
2. **Test your changes**: Run relevant tests (`./run_tests.sh`, `npm run test:run`)
3. **Follow conventions**: Match existing code style in the file
4. **Keep changes focused**: One logical change per commit
5. **Update documentation**: If adding features, update README or specialized docs

### Before Making Changes

**Checklist**:
- [ ] Database migrations are up to date (`alembic upgrade head`)
- [ ] Dependencies are installed (`pip install -e .[test]`, `npm ci`)
- [ ] Test database is running (for backend tests)
- [ ] Understand the existing code structure (read related files)

### After Making Changes

**Checklist**:
- [ ] Tests pass (`./run_tests.sh`, `npm run test:run`)
- [ ] Linting passes (`ruff check --fix .` for backend)
- [ ] Build succeeds (`npm run build` for frontend)
- [ ] Manual testing completed (if applicable)
- [ ] Documentation updated (if user-facing change)
- [ ] Migration created (if models changed)

### Specific Change Workflows

#### Adding a New API Endpoint

1. **Define route** in `backend/app/routers/{resource}.py`:
```python
@router.post("/api/photos/favorite/")
async def set_favorite(
    photo_uuid: str,
    favorite: bool,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    photo = db.query(Photo).filter(
        Photo.uuid == photo_uuid,
        Photo.owner_id == current_user.id
    ).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    photo.favorite = favorite
    db.commit()
    db.refresh(photo)
    return photo
```

2. **Add test** in `backend/tests/integration/test_auth_photos.py`:
```python
def test_set_favorite(client, auth_token, test_photo):
    response = client.post(
        "/api/photos/favorite/",
        headers={"Authorization": f"Bearer {auth_token}"},
        params={"photo_uuid": test_photo.uuid, "favorite": True}
    )
    assert response.status_code == 200
    assert response.json()["favorite"] is True
```

3. **Update frontend API client** in `frontend/src/api/photos.ts`:
```typescript
export async function setFavorite(uuid: string, favorite: boolean): Promise<Photo> {
  const response = await apiClient.post('/photos/favorite/', null, {
    params: { photo_uuid: uuid, favorite }
  })
  return response.data
}
```

4. **Use in component**:
```vue
<script setup lang="ts">
import { setFavorite } from '@/api/photos'

const toggleFavorite = async (photo: Photo) => {
  try {
    await setFavorite(photo.uuid, !photo.favorite)
    photo.favorite = !photo.favorite
  } catch (error) {
    console.error('Failed to toggle favorite:', error)
  }
}
</script>
```

#### Adding a Database Field

1. **Modify model** in `backend/app/models.py`:
```python
class Photo(SQLModel, table=True):
    # ... existing fields
    rating: int | None = Field(default=None)  # New field
```

2. **Create migration**:
```bash
cd backend
alembic revision --autogenerate -m "Add rating field to photos"
# Review generated file in alembic/versions/
alembic upgrade head
```

3. **Test migration**:
```bash
# Test downgrade
alembic downgrade -1
# Verify column removed

# Test upgrade
alembic upgrade head
# Verify column added
```

4. **Update tests** to use new field if needed

5. **Update frontend types** in `frontend/src/types/api.ts`:
```typescript
export interface Photo {
  // ... existing fields
  rating?: number  // New field
}
```

#### Adding a CLI Command

1. **Add command** in `backend/cli/{group}_commands.py`:
```python
@photo_group.command("export")
@click.option("--username", required=True)
@click.option("--output", type=click.Path(), required=True)
def export_photos(username: str, output: str):
    """Export user's photos to JSON."""
    from app.database import get_db_session
    from app.models import User, Photo

    db = next(get_db_session())
    user = db.query(User).filter(User.username == username).first()
    if not user:
        click.echo(f"User {username} not found", err=True)
        return

    photos = db.query(Photo).filter(Photo.owner_id == user.id).all()

    import json
    with open(output, 'w') as f:
        json.dump([photo.dict() for photo in photos], f, indent=2)

    click.echo(f"Exported {len(photos)} photos to {output}")
```

2. **Register command group** (if new) in `backend/cli/main.py`:
```python
cli.add_command(photo_group)
```

3. **Add test** in `backend/tests/integration/test_cli.py`:
```python
def test_export_photos(runner, test_user, tmp_path):
    output = tmp_path / "export.json"
    result = runner.invoke(cli, [
        "photo", "export",
        "--username", test_user.username,
        "--output", str(output)
    ])
    assert result.exit_code == 0
    assert output.exists()
```

4. **Update documentation** in README or relevant docs

---

## Additional Resources

### Documentation Files

- **README.md**: Main project documentation
- **CONTRIBUTING.md**: Contribution guidelines
- **backend/SYNC_COMMANDS.md**: Sync functionality (macOS, iCloud, Leonardo)
- **backend/TASK_SYSTEM.md**: Background task system
- **backend/PERSONAL_ACCESS_TOKENS.md**: PAT authentication
- **backend/tests/README.md**: Testing guide
- **.github/copilot-instructions.md**: GitHub Copilot guidance (condensed version)

### External Documentation

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLModel**: https://sqlmodel.tiangolo.com/
- **Vue 3**: https://vuejs.org/
- **Vite**: https://vitejs.dev/
- **Alembic**: https://alembic.sqlalchemy.org/
- **pytest**: https://docs.pytest.org/
- **Vitest**: https://vitest.dev/
- **Click**: https://click.palletsprojects.com/

### API Documentation

When backend is running:
- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

---

## Conclusion

This guide covers the essential information needed to work effectively with the PhotoSafe codebase. Remember:

1. **Always run migrations** before starting work
2. **Test your changes** thoroughly
3. **Follow existing conventions** in the codebase
4. **Ask questions** by creating issues if documentation is unclear
5. **Update this file** if you discover important information that should be documented

For questions or clarifications, open an issue on GitHub or contact the maintainers.

---

**Last Updated**: 2026-01-18
**Version**: 1.0.0
**Maintained By**: PhotoSafe Team
