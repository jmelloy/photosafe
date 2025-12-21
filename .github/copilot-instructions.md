# PhotoSafe Gallery - Copilot Instructions

## Overview
Modern photo gallery: FastAPI backend (Python 3.13), Vue 3 frontend (TypeScript), PostgreSQL 16+, iOS app, CLI tools. Repository: ~155MB, full-stack with Docker support.

**Tech Stack:** FastAPI + SQLAlchemy, Vue 3 + Vite 7.3, PostgreSQL 16, JWT auth, Alembic migrations, Vitest, pytest

## Structure
```
backend/          # FastAPI: app/{main,models,auth,database,routers/}, cli/, alembic/versions/, tests/{unit,integration}, pyproject.toml, run_tests.sh
frontend/         # Vue 3: src/{components,views,api,router,main.ts}, vite.config.ts, tsconfig.json, package.json
iosapp/           # Swift iOS/tvOS app
.github/workflows/  # backend-tests.yml (pytest+auto-version), frontend-tests.yml (vitest+build)
```

## Critical Commands

### Backend (Python 3.13+ REQUIRED)
```bash
cd backend
pip install -e .[test]                      # Install deps (REQUIRES Python 3.13+, will fail on 3.12)
alembic upgrade head                        # ALWAYS run before backend start/tests
uvicorn app.main:app --reload               # Dev server
./run_tests.sh                              # Tests (auto-manages test DB on port 5433)
pytest -v --cov=app --cov=cli               # Manual tests (needs TEST_DATABASE_URL env)
ruff check --fix .                          # Lint
alembic revision --autogenerate -m "msg"    # Create migration
```

### Frontend (Node 20+)
```bash
cd frontend
npm ci                       # Install (use 'ci' not 'install' for reproducibility)
npm run dev                  # Dev server (localhost:5173)
npm run build                # Build (runs vue-tsc + vite build)
npm run test:run             # Tests (3-5s)
```

### Docker Compose
```bash
docker-compose up --build                   # Dev: all services (DB:5432, backend:8000, frontend:5173)
./build.sh && docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d  # Production
docker compose --profile test up -d test-db # Start test DB (port 5433)
docker compose run --rm cli user create --username john --email john@example.com  # CLI
```

## CI/CD Workflows

**backend-tests.yml:** Triggers on PR/push to main with backend/** changes. Runs pytest with PostgreSQL 16 service, Python 3.13, `pip install -e .[test]`, then `pytest -v --cov`. On merge to main: auto-increments version in backend/pyproject.toml (YYYY.MM.PATCH calendar versioning).

**frontend-tests.yml:** Triggers on PR/push to main/master with frontend/** changes. Node 20, `npm ci`, `npm run test:run`, `npm run build`.

## Database & Migrations

- **PostgreSQL 16+ REQUIRED** - No SQLite support
- **Dev DB:** localhost:5432 (docker-compose), **Test DB:** localhost:5433 (--profile test)
- **ALWAYS run `alembic upgrade head`** before backend start or after pulling migrations
- Create migration: `alembic revision --autogenerate -m "msg"` → review in alembic/versions/ → `alembic upgrade head`
- Rollback: `alembic downgrade -1`

## Critical Issues & Workarounds

1. **Python 3.13+ strictly required** - Backend fails on 3.12: "Package 'photosafe' requires a different Python". Use Docker or install 3.13.
2. **Test DB port 5433 not 5432** - Avoids conflicts. If tests fail: `docker compose --profile test up -d test-db`
3. **Production volume mounts** - MUST use docker-compose.prod.yml override to remove volume mounts (code baked in images)
4. **Migration state** - "Target database not up to date"? Run `alembic upgrade head`
5. **Frontend node_modules in Docker** - Uses volume mount `frontend_node_modules:/app/node_modules` to prevent host/container conflicts

## Environment Variables

**Backend:** DATABASE_URL (required), SECRET_KEY (JWT, generate: `openssl rand -hex 32`), TEST_DATABASE_URL (tests)
**Frontend:** VITE_API_URL (backend URL), GIT_SHA/VITE_GIT_SHA (version tracking)

## Key Config Files

- `backend/pyproject.toml` - deps, pylint/ruff config, CLI entry point
- `backend/pytest.ini` - test paths, markers, TEST_DATABASE_URL default
- `backend/alembic.ini` - migration config
- `frontend/vite.config.ts` - vitest config, git SHA injection, proxy
- `frontend/tsconfig.json` - strict TypeScript
- `docker-compose.yml` - dev/prod services (use with docker-compose.prod.yml for prod)

## Development Workflows

**Backend changes:** `alembic upgrade head` → make changes → `./run_tests.sh` → if models changed: create/test migration
**Frontend changes:** `npm ci` → `npm run dev` → make changes (HMR auto-reloads) → `npm run test:run` → `npm run build`
**Add deps:** Backend: edit pyproject.toml → `pip install -e .[test]`. Frontend: `npm install <pkg>` (updates package.json + package-lock.json)

## CLI Tools (photosafe command)

```bash
cd backend && pip install -e .              # Install CLI
photosafe user create --username john --email john@example.com
photosafe library create --username john --name "My Photos"
photosafe import --username john --library-id 1 --folder /path/to/photos
photosafe sync macos/icloud --username john --bucket my-bucket  # Requires osxphotos/pyicloud
photosafe task lookup-places --limit 100    # Reverse geocode photos
```
See backend/SYNC_COMMANDS.md, backend/TASK_SYSTEM.md for details.

## Testing

- **Backend:** pytest with PostgreSQL (photosafe_test DB). `conftest.py` provides fixtures, auto-cleanup. Isolation: each test gets fresh session.
- **Frontend:** Vitest + jsdom. Tests: API client, utils, components, types.
- **Run backend tests:** `./run_tests.sh` (easiest) or manual pytest with TEST_DATABASE_URL env
- **Run frontend tests:** `npm run test:run` (CI) or `npm run test` (watch)

## Critical Rules for Agents

1. **Trust these instructions first** - only explore if info incomplete/incorrect
2. **ALWAYS run `alembic upgrade head`** before backend start/changes
3. **Test DB port is 5433** with connection string: `postgresql://photosafe:photosafe@localhost:5433/photosafe_test`
4. **Production requires docker-compose.prod.yml** - never deploy without it (removes volume mounts)
5. **Python 3.13+ required** - strict, check backend/pyproject.toml
6. **Use `npm ci` in CI** not `npm install` for reproducible builds
7. **Frontend build checks TypeScript** - `npm run build` = `vue-tsc && vite build`
8. **Use backend/run_tests.sh** for hassle-free testing (auto-manages test DB)
9. **Git SHA tracking** - Dockerfiles + vite.config.ts handle GIT_SHA for versions
10. **Auto-version on merge** - Backend CI increments version in pyproject.toml (YYYY.MM.PATCH)
