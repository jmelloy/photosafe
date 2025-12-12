# Docker Compose Migration Guide

## Overview

PhotoSafe now uses a unified Docker Compose configuration that supports both development and production deployments. The separate `docker-compose.production.yml` file has been consolidated into a single `docker-compose.yml` with automatic development overrides.

## What Changed?

### Before (Two Files)
- `docker-compose.yml` - Development configuration
- `docker-compose.production.yml` - Production configuration
- Required: `docker-compose -f docker-compose.production.yml up -d` for production

### After (Unified Configuration)
- `docker-compose.yml` - Base configuration (production-ready)
- `docker-compose.override.yml` - Development overrides (automatically applied)
- `.env.example` - Environment variable template

## Migration Instructions

### For Development Users

**No changes needed!** The behavior remains the same:

```bash
# Start in development mode (with hot-reload, exposed DB port, etc.)
docker compose up --build
```

The `docker-compose.override.yml` file is automatically applied, providing development-specific settings.

### For Production Users

**Update your deployment commands:**

#### Old Command
```bash
docker-compose -f docker-compose.production.yml up -d
```

#### New Command
```bash
docker compose -f docker-compose.yml up -d
```

**Important:** Using `-f docker-compose.yml` explicitly prevents the development overrides from being applied.

### Environment Variables

The new configuration uses environment variables for flexibility. Create a `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
POSTGRES_DB=photosafe
POSTGRES_USER=photosafe
POSTGRES_PASSWORD=your_secure_password_here
VITE_API_URL=http://backend:8000
```

For development, the default values work out of the box (photosafe/photosafe).

For production, **you must set a secure `POSTGRES_PASSWORD`**.

## Key Differences

### Development Mode (default)
When running `docker compose up`:
- ✅ Source code mounted for hot-reload
- ✅ Database port exposed (5432) for direct access
- ✅ Development commands (`--reload`, `npm run dev`)
- ✅ Default credentials work without `.env` file

### Production Mode
When running `docker compose -f docker-compose.yml up`:
- ✅ No source code volumes (uses built images)
- ✅ Database port NOT exposed (internal network only)
- ✅ Production commands (no auto-reload)
- ✅ Healthchecks for all services
- ⚠️ Requires `.env` file with secure passwords

## Benefits

1. **Single Source of Truth**: One `docker-compose.yml` for all environments
2. **Automatic Dev Experience**: No flags needed for development
3. **Explicit Production**: Clear distinction with `-f` flag
4. **Environment-based Config**: Flexible via `.env` files
5. **Better Documentation**: Inline comments explain all options

## Troubleshooting

### Issue: Development mode not working
**Solution:** Ensure `docker-compose.override.yml` exists and is not ignored.

### Issue: Production mode using development settings
**Solution:** Use `docker compose -f docker-compose.yml up -d` (not just `docker compose up`)

### Issue: Database connection errors in production
**Solution:** Check your `.env` file has correct `POSTGRES_PASSWORD` set.

### Issue: Want to customize development settings
**Solution:** Edit `docker-compose.override.yml` - it won't affect production.

## Need the Old File?

If you need to reference the old `docker-compose.production.yml`, it's still available in git history:

```bash
git show ec15719:docker-compose.production.yml
```

## Questions?

Open an issue if you encounter any problems during migration.
