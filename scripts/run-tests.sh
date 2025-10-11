#!/bin/bash
# Full test suite with coverage report

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running full test suite with coverage...${NC}\n"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Virtual environment not activated. Attempting to activate...${NC}"
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Error: Virtual environment not found. Please create one first:${NC}"
        echo "python -m venv venv"
        echo "source venv/bin/activate"
        echo "pip install -r requirements.txt"
        exit 1
    fi
fi

# Check if required packages are installed
if ! python -c "import pytest" &> /dev/null; then
    echo -e "${RED}Error: pytest not installed. Installing test dependencies...${NC}"
    pip install pytest pytest-asyncio pytest-cov
fi

# Load test environment variables
if [ -f ".env.test" ]; then
    echo -e "${GREEN}Loading test environment from .env.test${NC}"
    export $(grep -v '^#' .env.test | xargs)
else
    echo -e "${YELLOW}Warning: .env.test not found. Using defaults.${NC}"
fi

# Run tests with coverage
echo -e "\n${GREEN}Running tests...${NC}\n"
pytest -v \
    --cov=agent \
    --cov=ingestion \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml \
    --cov-fail-under=80 \
    "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    echo -e "${GREEN}Coverage report: htmlcov/index.html${NC}"
else
    echo -e "\n${RED}✗ Some tests failed!${NC}"
fi

exit $EXIT_CODE
