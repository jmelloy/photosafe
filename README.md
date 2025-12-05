# PhotoSafe Gallery

A modern photo gallery application built with FastAPI and Vue 3.

## Features

- 📷 Upload photos with drag & drop support
- 🖼️ Beautiful grid-based photo gallery
- 🔍 View photos in full-size modal
- 🗑️ Delete photos
- 💾 SQLite database for metadata storage
- 🐳 Docker support for easy deployment

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **SQLite**: Lightweight database
- **Uvicorn**: ASGI server

### Frontend
- **Vue 3**: Progressive JavaScript framework
- **Vite**: Next-generation frontend build tool
- **Axios**: HTTP client for API calls

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/jmelloy/photosafe.git
cd photosafe
```

2. Start the application:
```bash
docker-compose up --build
```

3. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

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

4. Configure environment variables (optional):
```bash
cp .env.example .env
# Edit .env and set your SECRET_KEY for JWT authentication
# Generate a secure key with: openssl rand -hex 32
```

5. Run the server:
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

## Project Structure

```
photosafe/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application
│   │   ├── models.py        # Database models
│   │   ├── schemas.py       # Pydantic schemas
│   │   └── database.py      # Database configuration
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
