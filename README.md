# PhotoSafe Gallery

[![Backend Tests](https://github.com/jmelloy/photosafe/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/jmelloy/photosafe/actions/workflows/backend-tests.yml)
[![Frontend Tests](https://github.com/jmelloy/photosafe/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/jmelloy/photosafe/actions/workflows/frontend-tests.yml)

Photo gallery with FastAPI backend, Vue 3 frontend, and CLI tools.

## Requirements

- Python 3.13+
- Node.js 20+
- PostgreSQL 16+

## Quick Start

```bash
# Docker (recommended)
docker-compose up --build
# Frontend: http://localhost:5173 | Backend: http://localhost:8000 | Docs: http://localhost:8000/docs

# Manual - Backend
cd backend && pip install -e .[test] && alembic upgrade head && uvicorn app.main:app --reload

# Manual - Frontend
cd frontend && npm ci && npm run dev
```

## CLI

```bash
cd backend && pip install -e .

photosafe user create --username john --email john@example.com
photosafe library create --username john --name "My Photos"
photosafe import --username john --library-id 1 --folder /path/to/photos
photosafe sync macos --username john --bucket my-bucket
photosafe task lookup-places --limit 100
```

See [backend/SYNC_COMMANDS.md](backend/SYNC_COMMANDS.md) and [backend/TASK_SYSTEM.md](backend/TASK_SYSTEM.md).

## API Endpoints

**Auth:** `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`

**Photos:** `GET/POST /api/photos/`, `GET/PATCH/DELETE /api/photos/{uuid}/`, `POST /api/photos/upload`

**Albums:** `GET/POST /api/albums/`, `GET/PUT/DELETE /api/albums/{uuid}/`

Full docs at http://localhost:8000/docs

## Production

```bash
cp .env.production.example .env.production  # Set strong POSTGRES_PASSWORD
./build.sh
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d
```

## Contributing

1. Fork and create a branch
2. Run tests: `cd backend && ./run_tests.sh` | `cd frontend && npm run test:run`
3. Lint: `ruff check --fix .`
4. Submit PR

## License

MIT
