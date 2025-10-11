#!/bin/bash
# Set up test environment with databases

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up test environment...${NC}\n"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Create .env.test if it doesn't exist
if [ ! -f ".env.test" ]; then
    echo -e "${YELLOW}Creating .env.test file...${NC}"
    cat > .env.test << 'EOF'
# Test Environment Configuration
# Using alternative ports to avoid conflicts with production databases
DATABASE_URL=postgresql://test_user:test_password@localhost:5433/test_db
NEO4J_URI=bolt://localhost:7688
NEO4J_USER=neo4j
NEO4J_PASSWORD=test_password
LLM_API_KEY=sk-test-key-for-testing
EMBEDDING_API_KEY=sk-test-key-for-testing
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_CHOICE=gpt-4-turbo-preview
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
INGESTION_LLM_CHOICE=gpt-4o-mini
APP_ENV=test
LOG_LEVEL=WARNING
EOF
    echo -e "${GREEN}Created .env.test${NC}"
fi

# Start test databases (using test-specific compose file with alternative ports)
echo -e "\n${YELLOW}Starting test databases...${NC}"
docker compose -f docker-compose.test.yml up -d postgres neo4j

# Wait for PostgreSQL (on test port 5433)
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
for i in {1..30}; do
    if pg_isready -h localhost -p 5433 -U test_user &> /dev/null; then
        echo -e "${GREEN}PostgreSQL is ready on port 5433!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Wait for Neo4j (on test port 7475)
echo -e "\n${YELLOW}Waiting for Neo4j to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:7475 > /dev/null 2>&1; then
        echo -e "${GREEN}Neo4j is ready on ports 7475/7688!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Initialize test database if needed (on test port 5433)
echo -e "\n${YELLOW}Initializing test database schema...${NC}"
if [ -f "sql/schema.sql" ]; then
    PGPASSWORD=test_password psql -h localhost -p 5433 -U test_user -d postgres -c "DROP DATABASE IF EXISTS test_db;" || true
    PGPASSWORD=test_password psql -h localhost -p 5433 -U test_user -d postgres -c "CREATE DATABASE test_db;" || true
    PGPASSWORD=test_password psql -h localhost -p 5433 -U test_user -d test_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
    echo -e "${GREEN}Test database initialized on port 5433${NC}"
fi

# Check virtual environment
echo -e "\n${YELLOW}Checking virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -q --upgrade pip
pip install -q pytest pytest-asyncio pytest-cov pytest-xdist

echo -e "\n${GREEN}✓ Test environment is ready!${NC}"
echo -e "\nTo run tests:"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}./scripts/run-tests.sh${NC}"
echo -e "\nOr use the Makefile:"
echo -e "  ${YELLOW}make test${NC}"
