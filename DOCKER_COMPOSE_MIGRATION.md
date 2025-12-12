# Docker Compose Migration Summary

## Changes Made

The `docker-compose.yml` and `docker-compose.production.yml` files have been combined into a single unified `docker-compose.yml` file that supports both development and production environments.

## Key Benefits

1. **Single Source of Truth**: Only one docker-compose file to maintain
2. **Flexible Configuration**: Use environment variables to switch between dev and production modes
3. **Clear Defaults**: Development mode works out-of-the-box with sensible defaults
4. **Production Ready**: Easy to configure for production with environment variables or `.env` files

## How It Works

### Development Mode (Default)

Simply run:
```bash
docker-compose up --build
```

This will:
- Use default credentials (photosafe/photosafe)
- Mount code directories for hot-reload
- Enable uvicorn's --reload flag
- Run npm dev server
- Expose database port for debugging

### Production Mode

Create a `.env.production` file based on `.env.production.example`:
```bash
cp .env.production.example .env.production
# Edit .env.production to set strong passwords and production settings
```

Then run:
```bash
docker-compose --env-file .env.production up -d
```

This will:
- Use environment-provided credentials
- Disable code mounting (uses built images)
- Disable hot-reload for better performance
- Run production preview builds
- Use "always" restart policy

## Environment Variables

Key variables that control the behavior:

- `POSTGRES_PASSWORD`: Database password (must be set for production)
- `BACKEND_COMMAND`: Controls backend startup (dev: with --reload, prod: without)
- `FRONTEND_COMMAND`: Controls frontend startup (dev: npm dev, prod: npm preview)
- `BACKEND_CODE_MOUNT`: Mount backend code (dev: ./backend, prod: empty)
- `FRONTEND_CODE_MOUNT`: Mount frontend code (dev: ./frontend, prod: empty)
- `RESTART_POLICY`: Container restart policy (dev: unless-stopped, prod: always)

## Files Modified

- ✅ `docker-compose.yml` - Updated to support both dev and production
- ✅ `.env.production.example` - Created as production configuration template
- ✅ `README.md` - Updated with new usage instructions
- ✅ `.gitignore` - Updated to ignore `.env.production` files
- ❌ `docker-compose.production.yml` - Removed (no longer needed)

## Migration Path

### For Developers

No changes needed! Continue using:
```bash
docker-compose up --build
```

### For Production Deployments

Instead of:
```bash
docker-compose -f docker-compose.production.yml up -d
```

Use:
```bash
docker-compose --env-file .env.production up -d
```

Or set environment variables directly and use:
```bash
docker-compose up -d
```

## Security Considerations

The unified configuration maintains all security best practices from the production file:

1. Environment variable support for credentials
2. Healthchecks for all services
3. Network isolation with custom network
4. Support for hiding database port exposure
5. Production-optimized restart policies
6. Comments warning about production security

## Testing

The configuration has been validated with:
```bash
docker compose config --quiet
```

All syntax is valid and the configuration parses correctly.
