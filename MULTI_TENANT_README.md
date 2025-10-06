# Multi-Tenant RAG System - Setup Guide

## Overview

This system now supports full multi-tenancy with the following hierarchy:

```
Organization (Billing Entity)
  └── Workspace (Isolated Knowledge Base)
      └── Agent (Behavior Configuration)
```

**Key Features:**
- ✅ Complete workspace-level data isolation
- ✅ Multiple agents per workspace with shared knowledge
- ✅ Workspace-scoped API keys
- ✅ Usage tracking for billing
- ✅ Full CRUD API for management

---

## Quick Start

### 1. Run Database Migrations

```bash
./scripts/run-migrations.sh
```

This will:
- Create multi-tenancy tables (organizations, workspaces, agents, api_keys)
- Update existing tables with workspace_id
- Create a default organization, workspace, and agent
- Migrate existing data to the default workspace

**Default IDs** (for backward compatibility):
- Organization: `00000000-0000-0000-0000-000000000001`
- Workspace: `00000000-0000-0000-0000-000000000002`
- Agent: `00000000-0000-0000-0000-000000000003`

### 2. Start the API Server

```bash
python -m agent.api
```

The API will be available at `http://localhost:8000`

### 3. Test the Setup

```bash
./scripts/test-multi-tenant-setup.sh
```

This creates a complete example setup:
- New organization
- New workspace
- New agent
- API key

---

## API Endpoints

Base URL: `http://localhost:8000/v1`

### Organizations

```bash
# Create organization
POST /organizations
Body: {
  "name": "Acme Corp",
  "slug": "acme",
  "plan_tier": "pro",  # free, starter, pro, enterprise
  "contact_email": "admin@acme.com",
  "contact_name": "Admin User"
}

# Get organization
GET /organizations/{org_id}
```

### Workspaces

```bash
# Create workspace
POST /organizations/{org_id}/workspaces
Body: {
  "name": "Customer Support",
  "slug": "support",
  "description": "Support knowledge base",
  "settings": {}
}

# Get workspace
GET /workspaces/{workspace_id}

# List workspaces
GET /organizations/{org_id}/workspaces
```

### Agents

```bash
# Create agent
POST /workspaces/{workspace_id}/agents
Body: {
  "name": "Support Bot",
  "slug": "support-bot",
  "description": "Helpful support agent",
  "system_prompt": "You are a helpful support agent...",
  "model_provider": "openai",
  "model_name": "gpt-4",
  "temperature": 0.7,
  "enabled_tools": ["vector_search", "hybrid_search"],
  "tool_config": {}
}

# Get agent
GET /workspaces/{workspace_id}/agents/{agent_id}

# List agents
GET /workspaces/{workspace_id}/agents

# Update agent
PATCH /workspaces/{workspace_id}/agents/{agent_id}
Body: {
  "name": "Updated Name",
  "temperature": 0.8,
  "is_active": false
}

# Delete agent
DELETE /workspaces/{workspace_id}/agents/{agent_id}
```

### API Keys

```bash
# Create API key
POST /workspaces/{workspace_id}/api-keys
Body: {
  "name": "Production Key",
  "scopes": ["chat", "search"],
  "rate_limit_per_minute": 60
}

Response: {
  "id": "uuid",
  "name": "Production Key",
  "key": "sk_live_xxxxx...",  # ONLY SHOWN ONCE!
  "key_prefix": "sk_live_xxxxx",
  "workspace_id": "uuid",
  "created_at": "2025-01-06T..."
}

# List API keys
GET /workspaces/{workspace_id}/api-keys

# Revoke API key
DELETE /workspaces/{workspace_id}/api-keys/{key_id}
```

### Chat (Coming Soon)

```bash
# Chat with agent
POST /workspaces/{workspace_id}/chat
Headers:
  Authorization: Bearer sk_live_xxxxx...
Body: {
  "agent_id": "uuid",
  "query": "How do I reset my password?",
  "session_id": "uuid",  # optional
  "stream": false
}
```

### Health Check

```bash
GET /v1/health

Response: {
  "status": "healthy",
  "multi_tenant": true,
  "version": "1.0.0"
}
```

---

## Example Workflow

### 1. Create Organization

```bash
curl -X POST http://localhost:8000/v1/organizations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Startup Inc",
    "slug": "techstartup",
    "plan_tier": "starter",
    "contact_email": "founders@techstartup.com"
  }'

# Response:
{
  "id": "a1b2c3d4...",
  "name": "Tech Startup Inc",
  ...
}
```

### 2. Create Workspace

```bash
curl -X POST http://localhost:8000/v1/organizations/a1b2c3d4.../workspaces \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product Documentation",
    "slug": "docs",
    "description": "Technical documentation workspace"
  }'

# Response:
{
  "id": "e5f6g7h8...",
  "organization_id": "a1b2c3d4...",
  "name": "Product Documentation",
  ...
}
```

### 3. Create Multiple Agents

```bash
# Create documentation agent
curl -X POST http://localhost:8000/v1/workspaces/e5f6g7h8.../agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Docs Expert",
    "slug": "docs-expert",
    "system_prompt": "You are a technical documentation expert...",
    "temperature": 0.3,
    "enabled_tools": ["vector_search", "hybrid_search"]
  }'

# Create API helper agent
curl -X POST http://localhost:8000/v1/workspaces/e5f6g7h8.../agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Helper",
    "slug": "api-helper",
    "system_prompt": "You help developers integrate with our API...",
    "temperature": 0.5,
    "enabled_tools": ["vector_search", "graph_search"]
  }'
```

### 4. Create API Key

```bash
curl -X POST http://localhost:8000/v1/workspaces/e5f6g7h8.../api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Key",
    "scopes": ["chat", "search"],
    "rate_limit_per_minute": 100
  }'

# Response includes full key (save it!):
{
  "id": "i9j0k1l2...",
  "key": "apikey_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456...",
  ...
}
```

### 5. Ingest Documents

```bash
# Coming soon: Workspace-aware ingestion
python -m ingestion.ingest \
  --workspace-id e5f6g7h8... \
  --directory documents/product-docs
```

### 6. Chat with Agent

```bash
curl -X POST http://localhost:8000/v1/workspaces/e5f6g7h8.../chat \
  -H "Authorization: Bearer {YOUR_API_KEY_HERE}" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "docs-expert-id",
    "query": "How do I authenticate with the API?"
  }'
```

---

## Architecture Details

### Data Isolation

**Workspace Level:**
- All documents/chunks filtered by `workspace_id`
- PostgreSQL functions include workspace parameter
- Knowledge graph uses unique `group_id` per workspace

**Agent Level:**
- Agents share workspace knowledge
- Different system prompts and tool configurations
- Separate behavior, same data

### Database Schema

```sql
organizations
  - id, name, slug, plan_tier
  - max_workspaces, max_documents_per_workspace
  - contact_email

workspaces
  - id, organization_id
  - name, slug, description
  - document_count, monthly_requests

agents
  - id, workspace_id
  - name, slug, system_prompt
  - model_provider, model_name, temperature
  - enabled_tools, is_active

api_keys
  - id, workspace_id
  - name, key_prefix, key_hash
  - scopes, rate_limit_per_minute
  - is_active, expires_at

documents
  - id, workspace_id  # NEW
  - title, source, content

chunks
  - id, workspace_id, document_id  # workspace_id added
  - content, embedding

sessions
  - id, workspace_id, agent_id  # NEW
  - user_id, metadata
```

### Search Functions

All search functions now require `workspace_id`:

```python
# Vector search
results = await vector_search(
    embedding=embedding,
    workspace_id="uuid",
    limit=10
)

# Hybrid search
results = await hybrid_search(
    embedding=embedding,
    query_text="search query",
    workspace_id="uuid",
    limit=10,
    text_weight=0.3
)

# Graph search (uses Graphiti group_id)
graphiti_client = GraphitiClient(
    group_id=f"workspace_{workspace_id}"
)
results = await graphiti_client.search(query)
```

---

## Migration from Single-Tenant

### Option A: Use Default Workspace

Your existing data is already migrated to the default workspace:

```python
DEFAULT_WORKSPACE_ID = "00000000-0000-0000-0000-000000000002"
DEFAULT_AGENT_ID = "00000000-0000-0000-0000-000000000003"
```

Continue using existing endpoints or switch to new multi-tenant endpoints with these IDs.

### Option B: Create New Workspaces

1. Create new organization
2. Create new workspaces
3. Re-ingest documents per workspace
4. Create agents per workspace

---

## Configuration

### Environment Variables

```bash
# Existing variables (still used)
DATABASE_URL=postgresql://...
NEO4J_URI=bolt://...
OPENAI_API_KEY=sk-...

# New multi-tenant settings (optional)
DEFAULT_WORKSPACE_ID=00000000-0000-0000-0000-000000000002
DEFAULT_AGENT_ID=00000000-0000-0000-0000-000000000003

# Rate limiting
DEFAULT_RATE_LIMIT=60  # requests per minute

# Plan limits
FREE_TIER_MAX_WORKSPACES=1
FREE_TIER_MAX_DOCUMENTS=50
STARTER_TIER_MAX_WORKSPACES=3
```

### Plan Tiers

| Tier | Max Workspaces | Max Docs/Workspace | Monthly Requests |
|------|---------------|-------------------|------------------|
| Free | 1 | 100 | 1,000 |
| Starter | 3 | 500 | 10,000 |
| Pro | 10 | 5,000 | 100,000 |
| Enterprise | Unlimited | Unlimited | Unlimited |

---

## Security

### API Key Format

```
apikey_live_xxxxxxxxxxxxx...  (production)
apikey_test_xxxxxxxxxxxxx...  (testing)
```

- Keys are hashed (SHA-256) before storage
- Only prefix (`sk_live_xxxxx`) stored for lookup
- Full key only shown once at creation

### Authentication Flow

1. Client includes API key in header: `Authorization: Bearer {api_key}`
2. Server extracts prefix for lookup
3. Server verifies full key hash
4. Server checks expiration, active status
5. Server validates workspace access
6. Server updates `last_used_at`
7. Request proceeds

### Rate Limiting

- Per API key
- Configurable per key
- Tracked via Redis (coming soon)
- Returns 429 when exceeded

---

## Monitoring

### Usage Tracking

Every request increments:
```sql
UPDATE workspaces
SET monthly_requests = monthly_requests + 1
WHERE id = workspace_id;
```

For detailed usage:
```sql
SELECT
    w.name,
    w.monthly_requests,
    w.document_count,
    COUNT(a.id) as agent_count
FROM workspaces w
LEFT JOIN agents a ON a.workspace_id = w.id
GROUP BY w.id, w.name;
```

### Health Checks

```bash
# System health
curl http://localhost:8000/v1/health

# Database health
curl http://localhost:8000/health

# Agent health (existing)
curl http://localhost:8000/health/agent
```

---

## Troubleshooting

### Common Issues

**1. "Organization not found"**
- Verify organization ID is correct
- Check organization wasn't deleted

**2. "Agent does not belong to this workspace"**
- Agent IDs are workspace-specific
- Use correct workspace_id in URL

**3. "API key expired or revoked"**
- Create new API key
- Check expiration date

**4. "Database connection failed"**
- Run migrations: `./scripts/run-migrations.sh`
- Check DATABASE_URL in `.env`

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run API server
python -m agent.api
```

### Check Database State

```bash
# Connect to PostgreSQL
psql $DATABASE_URL

# Check multi-tenant tables
\dt organizations workspaces agents api_keys

# Count resources
SELECT 'organizations' as table, COUNT(*) FROM organizations
UNION ALL
SELECT 'workspaces', COUNT(*) FROM workspaces
UNION ALL
SELECT 'agents', COUNT(*) FROM agents;

# Verify workspace isolation
SELECT
    w.name as workspace,
    COUNT(d.id) as documents,
    COUNT(DISTINCT c.id) as chunks
FROM workspaces w
LEFT JOIN documents d ON d.workspace_id = w.id
LEFT JOIN chunks c ON c.workspace_id = w.id
GROUP BY w.id, w.name;
```

---

## Development

### Running Tests

```bash
# Coming soon
pytest tests/test_multi_tenant_isolation.py
pytest tests/test_workspace_management.py
pytest tests/test_agent_management.py
```

### Adding New Endpoints

See `agent/api_multi_tenant.py` for examples.

### Database Changes

1. Create new migration: `sql/migrations/00X_description.sql`
2. Update schema
3. Run migration script

---

## Roadmap

### Phase 1: Core Multi-Tenancy ✅
- [x] Database schema
- [x] Data models
- [x] Database utilities
- [x] Tool updates
- [x] API endpoints

### Phase 2: Integration (In Progress)
- [ ] Authentication middleware
- [ ] Workspace-aware ingestion
- [ ] Multi-tenant chat implementation
- [ ] Agent system updates

### Phase 3: Production Features
- [ ] Rate limiting
- [ ] Usage tracking & billing
- [ ] Audit logging
- [ ] Backup automation
- [ ] Admin dashboard

### Phase 4: Advanced Features
- [ ] Agent-to-agent communication
- [ ] Workspace knowledge sharing
- [ ] Agent templates
- [ ] Usage analytics
- [ ] Multi-region support

---

## Support

For issues or questions:
1. Check `SAAS_MULTI_TENANT_DESIGN.md` for architecture details
2. Check `MULTI_TENANT_IMPLEMENTATION_STATUS.md` for current status
3. Review test scripts in `scripts/`
4. Check migration logs

---

**Last Updated**: 2025-01-06
**Version**: 1.0.0-alpha
**Status**: Core implementation complete, integration in progress
