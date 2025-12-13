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

#### Main PhotoSafe Application (Python/Django)

```bash
cd photosafe
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### V2 Backend (Go)

```bash
cd v2/go-backend
go mod download
go run main.go
```

#### V2 Frontend (Next.js)

```bash
cd v2/web
npm install
npm run dev
```

### Code Style

- **Python**: Follow PEP 8 guidelines. Use `black` for code formatting and run pre-commit hooks.
- **JavaScript/TypeScript**: Follow the project's ESLint configuration.
- **Go**: Follow standard Go formatting (`gofmt`).

### Running Tests

#### Backend Tests (FastAPI)

The backend has comprehensive test coverage and uses pytest:

```bash
cd backend
pip install -e .
pip install pytest pytest-cov
pytest -v --cov=app --cov=cli
```

**Note:** Tests require a PostgreSQL database. Set the `TEST_DATABASE_URL` environment variable:
```bash
export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/photosafe_test"
```

#### Frontend Tests (Vue 3 + Vitest)

The frontend uses Vitest for testing:

```bash
cd frontend
npm install
npm run test        # Run tests in watch mode
npm run test:run    # Run tests once
npm run test:ui     # Run tests with UI
```

Tests include:
- Unit tests for utility functions and API client
- Type validation tests for TypeScript definitions

#### Python Tests (Legacy Django)

```bash
cd photosafe
pytest
```

#### GitHub Actions CI/CD

All pull requests and pushes to `main`/`master` branches automatically trigger:
1. **Backend Tests**: Runs all backend tests with PostgreSQL in CI
2. **Frontend Tests**: Runs all frontend tests and verifies build
3. **Version Increment**: On successful merge to main/master, automatically increments the backend CLI version in `backend/pyproject.toml`

The version increment uses semantic versioning and bumps the patch version (e.g., 1.0.0 → 1.0.1).

#### Pre-commit Hooks

We use pre-commit hooks to ensure code quality. Install them with:

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
