#!/bin/bash
# Helper script to run tests with the test database container

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting test database container...${NC}"

# Start the test database container (using the 'test' profile)
cd "$(dirname "$0")/.."
docker compose --profile test up -d test-db

echo -e "${YELLOW}Waiting for test database to be ready...${NC}"

# Wait for the database to be healthy
max_attempts=30
attempt=0
until docker compose --profile test ps test-db | grep -q "healthy" || [ $attempt -eq $max_attempts ]; do
    attempt=$((attempt + 1))
    echo "Waiting for database... (attempt $attempt/$max_attempts)"
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}Test database failed to start within timeout${NC}"
    exit 1
fi

echo -e "${GREEN}Test database is ready!${NC}"

# Run pytest with any additional arguments passed to this script
echo -e "${YELLOW}Running tests...${NC}"
cd backend

# Set the test database URL environment variable
export TEST_DATABASE_URL="postgresql://photosafe:photosafe@localhost:5433/photosafe_test"

# Set the Apple credentials encryption key for tests
export APPLE_CREDENTIALS_ENCRYPTION_KEY="T1lmgBYDgxCurwiSjGvaJxKwPxPrmtOTbTFJsrm205M="

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

pytest "$@"

# Capture the exit code
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}Tests passed!${NC}"
else
    echo -e "${RED}Tests failed with exit code $exit_code${NC}"
fi

# Optionally stop the test database (uncomment if you want to stop after tests)
# echo -e "${YELLOW}Stopping test database...${NC}"
# docker compose --profile test down test-db

exit $exit_code
