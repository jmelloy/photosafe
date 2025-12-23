# Contributing to PhotoSafe

Thank you for your interest in contributing to PhotoSafe! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:
- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details (OS, Python version, etc.)

### Suggesting Enhancements

We welcome suggestions for new features or improvements. Please create an issue with:
- A clear and descriptive title
- Detailed description of the proposed enhancement
- Any relevant examples or mockups
- Explanation of why this enhancement would be useful

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests to ensure everything works
5. Commit your changes with clear, descriptive commit messages
6. Push to your fork
7. Create a pull request with a clear description of the changes

### Development Setup

#### Backend (FastAPI)

```bash
cd backend
pip install -e .[test]
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend (Vue 3)

```bash
cd frontend
npm ci
npm run dev
```

### Code Style

- **Python**: Follow PEP 8 guidelines. Use `ruff` for linting.
- **TypeScript**: Follow the project's ESLint configuration.

### Running Tests

#### Backend Tests (FastAPI + pytest)

The backend has comprehensive test coverage using pytest:

```bash
cd backend
./run_tests.sh                 # Easiest - auto-manages test DB
# OR manually:
docker compose --profile test up -d test-db
pytest -v --cov=app --cov=cli
```

Tests require PostgreSQL. The test database runs on port 5433 (not 5432) to avoid conflicts.

#### Frontend Tests (Vue 3 + Vitest)

The frontend uses Vitest for testing:

```bash
cd frontend
npm ci
npm run test        # Run tests in watch mode
npm run test:run    # Run tests once (CI mode)
npm run test:ui     # Run tests with UI
```

#### GitHub Actions CI/CD

All pull requests and pushes to `main` branches automatically trigger:
1. **Backend Tests**: Runs all backend tests with PostgreSQL 16 in CI
2. **Frontend Tests**: Runs all frontend tests and verifies build
3. **Version Increment**: On successful merge to main, automatically increments the backend CLI version in `backend/pyproject.toml` using calendar versioning (YYYY.MM.PATCH)

#### Pre-commit Hooks

We recommend using pre-commit hooks to ensure code quality:

```bash
pip install pre-commit
pre-commit install
```

### Commit Messages

- Use clear and descriptive commit messages
- Start with a verb in the imperative mood (e.g., "Add", "Fix", "Update")
- Keep the first line under 72 characters
- Add more detailed description in the body if needed

### Code Review Process

All submissions require review. We use GitHub pull requests for this purpose. The maintainers will review your pull request and may request changes before merging.

## Questions?

If you have questions, feel free to open an issue for discussion.

## License

By contributing to PhotoSafe, you agree that your contributions will be licensed under the MIT License.
