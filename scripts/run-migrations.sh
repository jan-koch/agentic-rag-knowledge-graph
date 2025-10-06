#!/bin/bash

# Run database migrations for multi-tenancy support

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}Running Multi-Tenancy Migrations${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL not set${NC}"
    echo "Please set DATABASE_URL in .env file"
    exit 1
fi

# Extract connection details from DATABASE_URL
# Format: postgresql://user:password@host:port/database
DB_URL=$DATABASE_URL

echo -e "${GREEN}✓${NC} Found DATABASE_URL"
echo ""

# Function to run SQL file
run_migration() {
    local file=$1
    local description=$2

    echo -e "${YELLOW}Running: ${description}${NC}"
    echo "  File: $file"

    if psql "$DB_URL" -f "$file" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Success"
    else
        echo -e "${RED}✗${NC} Failed"
        echo "  Re-running with verbose output:"
        psql "$DB_URL" -f "$file"
        exit 1
    fi
    echo ""
}

# Run migrations in order
echo "Starting migrations..."
echo ""

run_migration "sql/migrations/001_add_multi_tenancy.sql" "Add multi-tenancy tables and update schema"
run_migration "sql/migrations/002_seed_default_data.sql" "Seed default data and migrate existing records"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}All migrations completed successfully!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Show summary
echo "Summary:"
psql "$DB_URL" -c "
SELECT
    'organizations' as table_name, COUNT(*) as count FROM organizations
UNION ALL
SELECT 'workspaces', COUNT(*) FROM workspaces
UNION ALL
SELECT 'agents', COUNT(*) FROM agents
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks
ORDER BY table_name;
"

echo ""
echo -e "${GREEN}Ready to use multi-tenant system!${NC}"
echo ""
echo "Default workspace ID: 00000000-0000-0000-0000-000000000002"
echo "Default agent ID: 00000000-0000-0000-0000-000000000003"
