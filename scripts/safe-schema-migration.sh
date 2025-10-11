#!/bin/bash
# Safe Schema Migration Script
# This script allows running migrations WITHOUT destroying existing data

set -e

echo "=================================================="
echo "Safe Schema Migration Script"
echo "=================================================="
echo ""
echo "⚠️  IMPORTANT: This script modifies the database schema"
echo "    It does NOT drop existing tables or data"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if migration SQL file is provided
if [ -z "$1" ]; then
    echo "❌ Error: No migration SQL file provided"
    echo ""
    echo "Usage: $0 <migration-file.sql>"
    echo ""
    echo "Example:"
    echo "  $0 migrations/001_add_workspace_support.sql"
    echo ""
    exit 1
fi

MIGRATION_FILE="$1"

# Check if file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ Error: Migration file not found: $MIGRATION_FILE"
    exit 1
fi

# Check for dangerous commands in migration file
echo "🔍 Checking migration file for dangerous commands..."
DANGEROUS_COMMANDS=$(grep -iE "DROP TABLE|DROP DATABASE|TRUNCATE|DELETE FROM" "$MIGRATION_FILE" || true)

if [ ! -z "$DANGEROUS_COMMANDS" ]; then
    echo ""
    echo "⚠️  WARNING: Found potentially dangerous commands in migration:"
    echo "$DANGEROUS_COMMANDS"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "❌ Migration cancelled"
        exit 1
    fi
fi

# Create backup before migration
echo ""
echo "📦 Creating backup before migration..."
BACKUP_FILE="/tmp/postgres_backup_$(date +%Y%m%d_%H%M%S).sql"
docker exec agentic-rag-postgres pg_dump -U postgres agentic_rag > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup created: $BACKUP_FILE"
else
    echo "❌ Backup failed! Aborting migration."
    exit 1
fi

# Run migration
echo ""
echo "🔄 Running migration: $MIGRATION_FILE"
docker exec -i agentic-rag-postgres psql -U postgres -d agentic_rag < "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration completed successfully!"
    echo ""
    echo "Backup location: $BACKUP_FILE"
    echo ""
else
    echo ""
    echo "❌ Migration failed!"
    echo ""
    echo "To restore from backup:"
    echo "  docker exec -i agentic-rag-postgres psql -U postgres -d agentic_rag < $BACKUP_FILE"
    echo ""
    exit 1
fi

# Verify database is still accessible
echo "🔍 Verifying database..."
TABLES=$(docker exec agentic-rag-postgres psql -U postgres -d agentic_rag -c "\dt" -t | wc -l)
echo "✅ Database has $TABLES tables"

echo ""
echo "=================================================="
echo "Migration Complete"
echo "=================================================="
