# PhotoSafe Gallery - Copilot Instructions

## Overview
Modern photo gallery: FastAPI backend (Python 3.13+), Vue 3 frontend (TypeScript), PostgreSQL 16+, iOS app, CLI tools.

**Tech Stack:** FastAPI + SQLAlchemy, Vue 3 + Vite, PostgreSQL 16, JWT auth, Alembic migrations, Vitest, pytest

## Structure
```
backend/          # FastAPI: app/{main,models,auth,database,routers/}, cli/, alembic/versions/, tests/, pyproject.toml
frontend/         # Vue 3: src/{components,views,api,router,main.ts}, vite.config.ts, package.json
iosapp/           # Swift iOS/tvOS app
.github/workflows/  # backend-tests.yml, frontend-tests.yml
```

## Critical Commands

### Backend (Python 3.13+ REQUIRED)
```bash
cd backend
pip install -e .[test]           # Install deps (REQUIRES Python 3.13+)
alembic upgrade head             # ALWAYS run before backend start/tests
uvicorn app.main:app --reload    # Dev server
./run_tests.sh                   # Tests (auto-manages test DB on port 5433)
ruff check --fix .               # Lint
```

### Frontend (Node 20+)
```bash
cd frontend
npm ci                   # Install (use 'ci' not 'install')
npm run dev              # Dev server (localhost:5173)
npm run build            # Build (runs vue-tsc + vite build)
npm run test:run         # Tests
```

### Docker
```bash
cp docker-compose.override.yml.example docker-compose.override.yml && docker-compose up --build  # Dev: all services
./build.sh && docker-compose --env-file .env.production up -d  # Production
docker compose --profile test up -d test-db  # Test DB (port 5433)
```

## Database & Migrations

- **PostgreSQL 16+ REQUIRED** - No SQLite support
- **Dev DB:** localhost:5432, **Test DB:** localhost:5433
- **ALWAYS run `alembic upgrade head`** before backend start or after pulling migrations
- Create migration: `alembic revision --autogenerate -m "msg"` → review → `alembic upgrade head`

## Key Issues & Solutions

1. **Python 3.13+ required** - Backend fails on 3.12. Use Docker or install 3.13.
2. **Test DB port 5433** - Avoids conflicts with dev DB on 5432
3. **Docker development** - Copy docker-compose.override.yml.example to docker-compose.override.yml for dev setup
4. **Always run migrations** - "Target database not up to date"? Run `alembic upgrade head`

## Environment Variables

**Backend:** DATABASE_URL (required), SECRET_KEY (JWT), TEST_DATABASE_URL (tests)
**Frontend:** VITE_API_URL (backend URL), GIT_SHA (version tracking)

## Key Files

- `backend/pyproject.toml` - Python deps, ruff config, CLI entry point
- `backend/pytest.ini` - Test paths, markers
- `frontend/vite.config.ts` - Vitest config, proxy
- `docker-compose.yml` - Production-ready config
- `docker-compose.override.yml.example` - Development overrides

## Development Workflows

**Backend:** `alembic upgrade head` → make changes → `./run_tests.sh` → create migration if models changed
**Frontend:** `npm ci` → `npm run dev` → make changes (HMR) → `npm run test:run` → `npm run build`

## CLI & Tasks

```bash
photosafe user create --username john --email john@example.com
photosafe library create --username john --name "Photos"
photosafe import --username john --library-id 1 --folder /path
photosafe sync macos/icloud --username john --bucket my-bucket
photosafe task lookup-places --limit 100
```
See backend/SYNC_COMMANDS.md and backend/TASK_SYSTEM.md for details.

## Testing

- **Backend:** pytest with PostgreSQL. `./run_tests.sh` auto-manages test DB
- **Frontend:** Vitest. `npm run test:run` for CI mode
- **Test DB:** port 5433, connection: `postgresql://photosafe:photosafe@localhost:5433/photosafe_test`

## Critical Rules

1. **ALWAYS run `alembic upgrade head`** before backend start/changes
2. **Test DB uses port 5433** (not 5432)
3. **Docker development** - Copy docker-compose.override.yml.example to docker-compose.override.yml
4. **Python 3.13+ strictly required**
5. **Use `npm ci` in CI** not `npm install`
6. **Use backend/run_tests.sh** for hassle-free testing
