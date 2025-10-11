#!/bin/bash
# Quick unit tests only (skip slow tests)

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running fast unit tests...${NC}\n"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Error: Virtual environment not found.${NC}"
        exit 1
    fi
fi

# Load test environment
if [ -f ".env.test" ]; then
    export $(grep -v '^#' .env.test | xargs)
fi

# Run only fast unit tests
pytest -v \
    -m "not slow" \
    --tb=short \
    --maxfail=3 \
    "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ Fast tests passed!${NC}"
else
    echo -e "\n${RED}✗ Some tests failed!${NC}"
fi

exit $EXIT_CODE
