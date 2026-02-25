# PhotoSafe - Claude AI Guide

## Critical Requirements

- **Python 3.13+** required (strict - 3.12 will fail)
- **PostgreSQL 16+** required (no SQLite support)
- Dev DB: `localhost:5432` | Test DB: `localhost:5433`
- Always run `alembic upgrade head` after pulling/switching branches

## Project Stack

- **Backend**: FastAPI + SQLModel + Alembic + Click CLI
- **Frontend**: Vue 3 (Composition API) + TypeScript + Vite
- **Auth**: JWT (web) + Personal Access Tokens (CLI)
- **Storage**: S3 + local filesystem

## Quick Start

```bash
# Backend
cd backend
pip install -e .[test]
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm ci
npm run dev

# Docker - Development
cp docker-compose.override.yml.example docker-compose.override.yml
docker-compose up --build
```

## Key File Locations

### Backend (`backend/`)
| Purpose | Location |
|---------|----------|
| Models | `app/models.py` |
| Auth | `app/auth.py` |
| API routes | `app/routers/{resource}.py` |
| CLI commands | `cli/{group}_commands.py` |
| Migrations | `alembic/versions/` |
| Tests | `tests/unit/`, `tests/integration/` |
| Fixtures | `tests/conftest.py` |

### Frontend (`frontend/src/`)
| Purpose | Location |
|---------|----------|
| Pages | `views/{Page}.vue` |
| Components | `components/{Name}.vue` |
| API clients | `api/{resource}.ts` |
| Types | `types/api.ts` |
| Routes | `router/index.ts` |
| Utils | `utils/{module}.ts` |

## Database Models

Key models in `backend/app/models.py`:
- **User**: Auth, ownership (`photos`, `libraries`, `personal_access_tokens`)
- **Photo**: UUID PK, JSONB (`exif`, `faces`, `place`), ARRAY (`keywords`, `labels`, `albums`, `persons`), soft delete (`deleted_at`)
- **Library**: Multi-library per user
- **Album**: Many-to-many with photos via `album_photos`
- **PersonalAccessToken**: Hashed, optional expiration

Photo URL resolution: Use `photo.url` property (returns S3 path if available, else local path).

## Migrations

```bash
# Before model changes
alembic upgrade head

# After model changes
alembic revision --autogenerate -m "Description"
# REVIEW the generated file - autogenerate has limitations
alembic upgrade head

# Other commands
alembic current              # Show current revision
alembic downgrade -1         # Rollback one
alembic history              # View history
```

**Autogenerate limitations**: Doesn't detect renames (sees drop+add), may miss indexes/constraints, can't infer data migrations. Always review.

## Testing

```bash
# Backend (easiest)
cd backend && ./run_tests.sh

# Backend (manual)
docker compose --profile test up -d test-db
pytest -v --cov=app --cov=cli

# Frontend
npm run test:run    # CI mode
npm run test        # Watch mode
```

Key fixtures: `client`, `auth_token`, `test_user`, `test_library`, `db_session`, `runner` (CLI)

## Authentication

**JWT (Web)**: Login → access token (30 min) + refresh token (7 days) → `Authorization: Bearer <token>`

**PAT (CLI/API)**: Create via `POST /api/auth/tokens` → bcrypt hashed storage → same Bearer header

Both use `get_current_active_user` dependency in `backend/app/auth.py`.

**Authorization**: Owner-based - all queries filter by `owner_id = current_user.id`.

## API Patterns

- RESTful with trailing slashes: `GET /api/photos/`, `POST /api/photos/`
- Pagination: `limit`/`offset` params, returns `has_more` + `next_offset`
- Errors: Standard HTTP codes, `{"detail": "message"}` format
- Batch: `POST /api/photos/batch/` for bulk operations

## CLI Commands

```bash
photosafe user create --username john --email john@example.com
photosafe library create --username john --name "My Photos"
photosafe import --username john --library-id 1 --folder /path --bucket s3-bucket
photosafe sync macos --username john --bucket bucket --library-id 1
photosafe task lookup-places --limit 100
```

Structure: `photosafe {user|library|import|sync|task|maintenance} [command] [options]`

## Code Conventions

**Python**: PEP 8, snake_case functions/vars, PascalCase classes, 100 char lines, `ruff check --fix .`

**TypeScript**: camelCase functions/vars, PascalCase types/components, avoid `any`

**Vue**: `<script setup lang="ts">`, Composition API, TypeScript required

**Commits**: Imperative mood, <72 chars first line. Optional: `feat:`, `fix:`, `docs:`, etc.

**Versioning**: Calendar-based (YYYY.MM.PATCH), auto-incremented by CI.

## Common Gotchas

1. **Migration not applied**: Run `alembic upgrade head`
2. **Test DB not running**: `docker compose --profile test up -d test-db` (port 5433)
3. **Python version**: Must be 3.13+
4. **Frontend proxy**: Only works with `npm run dev`, backend must be on :8000
5. **Missing env vars**: Copy `backend/.env.example` to `.env`, generate SECRET_KEY with `openssl rand -hex 32`
6. **Broken images**: Use `photo.url` not `photo.path` or `photo.s3_key_path`
7. **Token refresh race**: Handled in `frontend/src/api/client.ts` with request queue
8. **Docker development**: Copy `docker-compose.override.yml.example` to `docker-compose.override.yml` for development with hot-reload

## Environment Variables

**Backend** (`backend/.env`):
```bash
SECRET_KEY=<openssl rand -hex 32>
DATABASE_URL=postgresql://photosafe:photosafe@localhost:5432/photosafe
TEST_DATABASE_URL=postgresql://photosafe:photosafe@localhost:5433/photosafe_test
```

## Workflow Checklists

**Before changes**:
- [ ] `alembic upgrade head`
- [ ] Dependencies installed
- [ ] Test DB running (for tests)

**After changes**:
- [ ] Tests pass
- [ ] Linting passes (`ruff check --fix .`)
- [ ] Build succeeds (`npm run build`)
- [ ] Migration created (if models changed)

## Secrets Management (SOPS + age)

Kubernetes secrets in `k8s/**/secret*.yaml` are encrypted with [SOPS](https://github.com/getsops/sops) using age encryption. Config is in `.sops.yaml`.

```bash
# Edit secrets (decrypts, opens editor, re-encrypts on save)
sops k8s/base/secret.yaml

# Decrypt to stdout
sops decrypt k8s/base/secret.yaml

# Encrypt in-place (after editing plaintext)
sops encrypt -i k8s/base/secret.yaml
```

**Private key location**: `~/.config/sops/age/keys.txt` (SOPS default lookup path). Never commit this file.

## Additional Docs

- `backend/SYNC_COMMANDS.md` - Sync functionality
- `backend/TASK_SYSTEM.md` - Background tasks
- `backend/PERSONAL_ACCESS_TOKENS.md` - PAT auth
- API docs: `http://localhost:8000/docs` (when running)
