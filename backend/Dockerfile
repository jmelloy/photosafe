FROM python:3.13-slim

WORKDIR /app
RUN pip install --system uv

# Install PostgreSQL client tools and git
RUN apt-get update && apt-get install -y \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY pyproject.toml .
RUN uv pip install --system .

COPY app ./app
COPY cli ./cli
COPY alembic ./alembic
COPY alembic.ini .

# Install the package in editable mode so volume mounts work properly
RUN uv pip install --system -e .

# Create uploads directory
RUN mkdir -p uploads

# Capture git SHA at build time (if .git exists)
ARG GIT_SHA=unknown
ENV GIT_SHA=${GIT_SHA}

# Expose port
EXPOSE 8000

# Run migrations and start the application
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
