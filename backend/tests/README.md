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
