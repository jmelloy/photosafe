# PhotoSafe Gallery

[![Backend Tests](https://github.com/jmelloy/photosafe/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/jmelloy/photosafe/actions/workflows/backend-tests.yml)

A modern photo gallery application built with FastAPI and Vue 3.

## Features

- 📷 Upload photos with drag & drop support
- 🖼️ Beautiful grid-based photo gallery
- 🔍 View photos in full-size modal
- 🗑️ Delete photos
- 💾 PostgreSQL database for production-ready metadata storage
- 🐳 Docker support for easy deployment
- 🔧 **CLI for bulk operations** - User management, library organization, and photo import
- 📚 **Multiple libraries per user** - Organize photos into separate collections
- 📥 **Import with metadata** - Import photos from folders with JSON/XMP sidecar files
- ☁️ **S3 integration** - Upload imported photos to S3 storage

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Production-grade relational database
- **Uvicorn**: ASGI server

### Frontend
- **Vue 3**: Progressive JavaScript framework
- **Vite**: Next-generation frontend build tool
- **Axios**: HTTP client for API calls

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 12+ (or use Docker Compose)
- Docker & Docker Compose (optional)

## Quick Start

### Using Docker Compose (Recommended)

#### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/jmelloy/photosafe.git
cd photosafe
```

2. Start the application (includes PostgreSQL database):
```bash
docker-compose up --build
```

> **Security Note**: The default docker-compose.yml uses simple credentials (photosafe/photosafe) for development. For production deployments, see the Production Setup section below.

3. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - PostgreSQL: localhost:5432 (user: photosafe, password: photosafe, database: photosafe)

#### Production Setup

For production deployments, use environment variables to configure the services:

1. Create a production environment file:
```bash
cp .env.production.example .env.production
# Edit .env.production and set a strong POSTGRES_PASSWORD
```

2. Start the application in production mode:
```bash
docker-compose --env-file .env.production up -d
```

Key production environment variables:
- `POSTGRES_PASSWORD`: **Required** - Set a strong database password
- `BACKEND_COMMAND`: Runs without --reload for better performance
- `FRONTEND_COMMAND`: Runs production preview build
- `RESTART_POLICY`: Set to "always" for auto-restart after reboot

For details, see `.env.production.example` and comments in `docker-compose.yml`.

> **Production Security Notes**:
> - Always set a strong `POSTGRES_PASSWORD`
> - Consider removing database port exposure from docker-compose.yml
> - Use a reverse proxy (nginx/traefik) in front of backend/frontend services
> - Consider using Docker secrets for sensitive data

### Manual Setup

#### Backend

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and set your configuration:
# - SECRET_KEY for JWT authentication (generate with: openssl rand -hex 32)
# - DATABASE_URL for PostgreSQL database connection
#   Example: postgresql://user:password@localhost:5432/photosafe
```

5. Set up PostgreSQL database:
```bash
# Create a PostgreSQL database
createdb photosafe

# Or use the default Docker Compose database
# PostgreSQL: localhost:5432 (user: photosafe, password: photosafe, database: photosafe)
```

6. Initialize the database with migrations:
```bash
alembic upgrade head
```

7. Run the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

#### Frontend

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get JWT access token
- `GET /api/auth/me` - Get current authenticated user information

### Photos (Requires Authentication)
- `GET /api/photos` - List all photos owned by the current user
- `GET /api/photos/{uuid}` - Get a specific photo by UUID
- `POST /api/photos/` - Create a new photo
- `PATCH /api/photos/{uuid}/` - Update a photo
- `DELETE /api/photos/{uuid}/` - Delete a photo
- `POST /api/photos/upload` - Upload a new photo file

### Albums (Requires Authentication)
- `GET /api/albums` - List all albums
- `GET /api/albums/{uuid}` - Get a specific album
- `POST /api/albums/` - Create a new album
- `PUT /api/albums/{uuid}/` - Update or create an album
- `DELETE /api/albums/{uuid}/` - Delete an album

Full API documentation is available at http://localhost:8000/docs when the backend is running.

## Database Configuration

The application requires PostgreSQL for all environments.

### PostgreSQL Setup

PostgreSQL provides better performance, scalability, and advanced features like JSONB and ARRAY types for structured data.

**Using Docker Compose (Recommended):**
```bash
docker-compose up --build
```
The PostgreSQL database is automatically configured and started.

**Manual Setup:**
1. Install PostgreSQL 12 or higher
2. Create a database: `createdb photosafe`
3. Set the `DATABASE_URL` environment variable:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/photosafe"
   ```
4. Run migrations: `alembic upgrade head`

## Database Migrations

The backend uses Alembic for database migrations. This provides version control for your database schema.

### Common Migration Commands

```bash
# Apply all pending migrations
alembic upgrade head

# View migration history
alembic history

# Create a new migration after modifying models
alembic revision --autogenerate -m "Description of changes"

# Rollback one migration
alembic downgrade -1
```

For more details, see [backend/MIGRATIONS.md](backend/MIGRATIONS.md).

## CLI - Command Line Interface

PhotoSafe includes a powerful CLI for bulk operations, user management, and photo imports.

### Installation

```bash
cd backend
pip install -e .
```

### Quick Examples

```bash
# Create a user
photosafe user create --username john --email john@example.com

# Create a library
photosafe library create --username john --name "My Photos"

# Import photos from a folder
photosafe import --username john --library-id 1 --folder /path/to/photos
```

For complete CLI documentation, see [backend/CLI_README.md](backend/CLI_README.md).

## Project Structure

```
photosafe/
├── backend/
│   ├── alembic/
│   │   ├── versions/        # Migration files
│   │   └── env.py          # Alembic environment config
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application
│   │   ├── models.py        # Database models (User, Photo, Album, Library, Version)
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── database.py      # Database configuration
│   │   └── auth.py          # Authentication
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py          # CLI entry point
│   │   ├── user_commands.py # User management commands
│   │   ├── library_commands.py # Library management commands
│   │   └── import_commands.py  # Photo import commands
│   ├── alembic.ini          # Alembic configuration
│   ├── CLI_README.md        # CLI documentation
│   ├── MIGRATIONS.md        # Migration documentation
│   ├── setup.py            # CLI package setup
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── photos.js    # API client
│   │   ├── components/
│   │   │   ├── PhotoGallery.vue
│   │   │   └── PhotoUpload.vue
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
└── docker-compose.yml
```

## Development

### Backend Development

The backend uses FastAPI with hot-reload enabled in development mode. Any changes to the Python files will automatically restart the server.

### Frontend Development

The frontend uses Vite with hot module replacement (HMR). Changes to Vue components will be reflected immediately in the browser.

## Building for Production

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run build
npm run preview
```

## License

MIT License - see LICENSE file for details
