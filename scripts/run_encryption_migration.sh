#!/bin/bash
# Run the API key encryption migration

set -e

echo "🔄 Running API key encryption migration..."
echo

# Get database URL from .env
source .env

# Check if we have the right credentials
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set in .env"
    exit 1
fi

# Try to connect and run migration
echo "📊 Adding encryption columns to api_keys table..."

psql "$DATABASE_URL" << 'EOF'
-- Add encryption columns if they don't exist
DO $$
BEGIN
    -- Add key_encrypted column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_keys' AND column_name = 'key_encrypted'
    ) THEN
        ALTER TABLE api_keys ADD COLUMN key_encrypted TEXT;
        RAISE NOTICE 'Added key_encrypted column';
    ELSE
        RAISE NOTICE 'key_encrypted column already exists';
    END IF;

    -- Add is_legacy column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_keys' AND column_name = 'is_legacy'
    ) THEN
        ALTER TABLE api_keys ADD COLUMN is_legacy BOOLEAN DEFAULT false;
        RAISE NOTICE 'Added is_legacy column';
    ELSE
        RAISE NOTICE 'is_legacy column already exists';
    END IF;
END$$;

-- Mark existing keys as legacy
UPDATE api_keys
SET is_legacy = true
WHERE key_encrypted IS NULL;

-- Add index
CREATE INDEX IF NOT EXISTS idx_api_keys_is_legacy ON api_keys (is_legacy);

-- Show results
SELECT
    COUNT(*) FILTER (WHERE is_legacy = true) AS legacy_keys,
    COUNT(*) FILTER (WHERE is_legacy = false) AS new_keys,
    COUNT(*) AS total_keys
FROM api_keys;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully!"
    echo "🔄 Restart the API service for changes to take effect:"
    echo "   sudo systemctl restart rag-api"
else
    echo "❌ Migration failed"
    exit 1
fi
