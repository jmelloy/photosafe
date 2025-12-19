# Tests

This directory contains all tests for the PhotoSafe backend.

## Structure

- `unit/` - Unit tests for individual components and functions
  - `test_version.py` - Version checking tests
  - `test_blocks.py` - Block handling tests
  - `test_filtering.py` - Filtering logic tests

- `integration/` - Integration tests that test multiple components together
  - `test_auth_photos.py` - Authentication and photo access tests
  - `test_cli.py` - CLI command tests
  - `test_import_metadata.py` - Metadata import tests
  - `test_library_upsert.py` - Library update/insert tests
  - `test_migrations.py` - Database migration tests
  - `test_parity.py` - Parity checking tests
  - `test_refresh_manual.py` - Manual refresh tests
  - `test_sync_commands.py` - Sync command tests
  - `demo_auth.py` - Authentication demo/test script
  - `demo_metadata_import.py` - Metadata import demo/test script

- `fixtures/` - Test fixtures and sample data

## Running Tests

### Prerequisites

Tests require a PostgreSQL database. The easiest way to run tests is using the provided test database container.

### Quick Start (Recommended)

Use the provided script to automatically start the test database and run tests:

```bash
# From the backend directory
./run_tests.sh
```

This script will:
1. Start the test database container (photosafe-test-db)
2. Wait for it to be ready
3. Run pytest with all tests
4. Keep the database running for subsequent test runs

You can pass pytest arguments to the script:

```bash
# Run only unit tests
./run_tests.sh tests/unit

# Run only integration tests
./run_tests.sh tests/integration

# Run a specific test file
./run_tests.sh tests/unit/test_version.py

# Run with markers
./run_tests.sh -m unit

# Run with verbose output
./run_tests.sh -v
```

### Manual Setup

If you prefer to manage the test database manually:

1. **Start the test database container:**
```bash
# From the project root
docker compose --profile test up -d test-db
```

2. **Run tests:**
```bash
# From the backend directory
pytest
```

3. **Stop the test database (when done):**
```bash
# From the project root
docker compose --profile test down test-db
```

### Test Database Configuration

The test database runs on `localhost:5433` (different from the main database on 5432) with these defaults:
- Database: `photosafe_test`
- User: `photosafe`
- Password: `photosafe`

You can override the connection URL with the `TEST_DATABASE_URL` environment variable:

```bash
export TEST_DATABASE_URL="postgresql://user:pass@localhost:5433/photosafe_test"
pytest
```

### Running Specific Tests

Run all tests:
```bash
pytest
```

Run only unit tests:
```bash
pytest tests/unit
```

Run only integration tests:
```bash
pytest tests/integration
```

Run a specific test file:
```bash
pytest tests/unit/test_version.py
```

Run with markers:
```bash
pytest -m unit
pytest -m integration
```

### Test Isolation

Each test function gets a fresh database session with automatic cleanup. The test fixtures in `conftest.py` ensure:
- Tables are created once at the start of the test session
- Data is cleaned up after each test
- Tests are isolated from each other
