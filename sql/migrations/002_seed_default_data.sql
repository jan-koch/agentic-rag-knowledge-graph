-- Migration: Seed Default Data
-- Version: 002
-- Description: Creates default organization, workspace, and agent, then migrates existing data

-- ====================
-- 1. CREATE DEFAULT ORGANIZATION
-- ====================

INSERT INTO organizations (id, name, slug, plan_tier, max_workspaces, contact_email, contact_name)
VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    'Default Organization',
    'default',
    'enterprise',
    999,
    'admin@example.com',
    'System Admin'
)
ON CONFLICT (id) DO NOTHING;


-- ====================
-- 2. CREATE DEFAULT WORKSPACE
-- ====================

INSERT INTO workspaces (id, organization_id, name, slug, description)
VALUES (
    '00000000-0000-0000-0000-000000000002'::uuid,
    '00000000-0000-0000-0000-000000000001'::uuid,
    'Default Workspace',
    'default',
    'Default workspace for existing data'
)
ON CONFLICT (id) DO NOTHING;


-- ====================
-- 3. CREATE DEFAULT AGENT
-- ====================

INSERT INTO agents (id, workspace_id, name, slug, description, system_prompt, enabled_tools)
VALUES (
    '00000000-0000-0000-0000-000000000003'::uuid,
    '00000000-0000-0000-0000-000000000002'::uuid,
    'General Assistant',
    'general',
    'Default agent for general queries',
    'You are a helpful AI assistant with access to a knowledge base. Use the available search tools to find relevant information and provide accurate, helpful responses based on the knowledge base content.',
    '["vector_search", "graph_search", "hybrid_search", "list_documents", "get_document"]'::jsonb
)
ON CONFLICT (id) DO NOTHING;


-- ====================
-- 4. MIGRATE EXISTING DATA
-- ====================

-- Update all existing documents to belong to default workspace
UPDATE documents
SET workspace_id = '00000000-0000-0000-0000-000000000002'::uuid
WHERE workspace_id IS NULL;

-- Update all existing chunks to belong to default workspace
UPDATE chunks
SET workspace_id = '00000000-0000-0000-0000-000000000002'::uuid
WHERE workspace_id IS NULL;

-- Update all existing sessions to belong to default workspace and agent
UPDATE sessions
SET
    workspace_id = '00000000-0000-0000-0000-000000000002'::uuid,
    agent_id = '00000000-0000-0000-0000-000000000003'::uuid
WHERE workspace_id IS NULL;

-- Update all existing messages to belong to default workspace
UPDATE messages m
SET workspace_id = '00000000-0000-0000-0000-000000000002'::uuid
WHERE workspace_id IS NULL
  AND EXISTS (SELECT 1 FROM sessions s WHERE s.id = m.session_id);


-- ====================
-- 5. ADD NOT NULL CONSTRAINTS (after migration)
-- ====================

-- Now that all data has workspace_id, make it NOT NULL
ALTER TABLE documents ALTER COLUMN workspace_id SET NOT NULL;
ALTER TABLE chunks ALTER COLUMN workspace_id SET NOT NULL;
ALTER TABLE sessions ALTER COLUMN workspace_id SET NOT NULL;
ALTER TABLE messages ALTER COLUMN workspace_id SET NOT NULL;


-- ====================
-- MIGRATION COMPLETE
-- ====================

-- Verify migration
SELECT
    'organizations' as table_name, COUNT(*) as count FROM organizations
UNION ALL
SELECT 'workspaces', COUNT(*) FROM workspaces
UNION ALL
SELECT 'agents', COUNT(*) FROM agents
UNION ALL
SELECT 'documents', COUNT(*) FROM documents WHERE workspace_id IS NOT NULL
UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks WHERE workspace_id IS NOT NULL
UNION ALL
SELECT 'sessions', COUNT(*) FROM sessions WHERE workspace_id IS NOT NULL;
