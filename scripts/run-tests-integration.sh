#!/bin/bash
# Integration tests with real database services

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running integration tests...${NC}\n"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Error: Virtual environment not found.${NC}"
        exit 1
    fi
fi

# Check if Docker services are running
echo -e "${YELLOW}Checking Docker services...${NC}"

if ! docker ps | grep -q "rag-postgres"; then
    echo -e "${YELLOW}PostgreSQL container not running. Starting services...${NC}"
    docker compose up -d postgres neo4j
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 10
fi

# Verify services are accessible
if ! pg_isready -h localhost -p 5432 -U postgres &> /dev/null; then
    echo -e "${RED}Error: PostgreSQL not accessible${NC}"
    echo -e "${YELLOW}Run: docker compose up -d${NC}"
    exit 1
fi

echo -e "${GREEN}Database services are ready${NC}\n"

# Load test environment
if [ -f ".env.test" ]; then
    export $(grep -v '^#' .env.test | xargs)
fi

# Run integration tests
pytest -v \
    -m integration \
    --tb=short \
    "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ Integration tests passed!${NC}"
else
    echo -e "\n${RED}✗ Some integration tests failed!${NC}"
fi

exit $EXIT_CODE
