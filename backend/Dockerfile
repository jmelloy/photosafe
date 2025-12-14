FROM python:3.11-slim

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /uvx /bin/

# Install PostgreSQL client tools
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY pyproject.toml .
COPY app ./app
COPY cli ./cli

RUN uv pip install --system .

# Copy application
COPY alembic ./alembic
COPY alembic.ini .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Run migrations and start the application
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
