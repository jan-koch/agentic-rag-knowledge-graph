-- Migration: Add encrypted key storage support
-- Date: 2025-10-28
-- Description: Add key_encrypted column and is_legacy flag to support retrievable API keys

-- Add new columns to api_keys table
ALTER TABLE api_keys
ADD COLUMN IF NOT EXISTS key_encrypted TEXT,
ADD COLUMN IF NOT EXISTS is_legacy BOOLEAN DEFAULT false;

-- Mark all existing keys as legacy (they only have key_hash, not key_encrypted)
UPDATE api_keys
SET is_legacy = true
WHERE key_encrypted IS NULL;

-- Add index for efficient legacy key filtering
CREATE INDEX IF NOT EXISTS idx_api_keys_is_legacy ON api_keys (is_legacy);

-- Add comment explaining the columns
COMMENT ON COLUMN api_keys.key_encrypted IS 'Encrypted API key (AES-256), only for non-legacy keys';
COMMENT ON COLUMN api_keys.is_legacy IS 'True for old keys that only have hash (not retrievable)';

-- Verification: Show migration results
DO $$
DECLARE
    legacy_count INTEGER;
    total_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO legacy_count FROM api_keys WHERE is_legacy = true;
    SELECT COUNT(*) INTO total_count FROM api_keys;
    RAISE NOTICE 'Migration complete: % legacy keys out of % total keys', legacy_count, total_count;
END $$;
