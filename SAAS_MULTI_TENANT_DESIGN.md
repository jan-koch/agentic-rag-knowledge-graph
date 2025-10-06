# SaaS Multi-Tenant Architecture Design

## Executive Summary

This document outlines a complete multi-tenant SaaS architecture for the agentic RAG system, enabling organizations to create isolated workspaces with multiple specialized agents sharing workspace-specific knowledge.

**Key Features:**
- 🏢 **Organization-level billing and management**
- 🔐 **Workspace-level data isolation**
- 🤖 **Multiple agents per workspace with shared knowledge**
- 👥 **Team collaboration within workspaces**
- 📊 **Usage tracking and quotas**
- 🔑 **API key management per workspace**

---

## 1. Architecture Overview

### 1.1 Hierarchy

```
Organization (Customer/Billing Entity)
  │
  ├── Workspace 1 (Isolated Knowledge Base)
  │   ├── Agent: Customer Support
  │   ├── Agent: Sales Assistant
  │   └── Agent: Technical Documentation
  │   └── Documents, Chunks, Knowledge Graph
  │   └── Users, API Keys, Sessions
  │
  ├── Workspace 2 (Another Isolated Knowledge Base)
  │   ├── Agent: Internal HR Bot
  │   └── Agent: Employee Onboarding
  │   └── [Separate Documents & Knowledge]
  │
  └── Workspace 3...
```

### 1.2 Isolation Boundaries

| Level | Isolation Type | What's Isolated |
|-------|---------------|-----------------|
| **Organization** | Billing & Management | Plans, billing, organization settings |
| **Workspace** | Data & Knowledge | Documents, embeddings, knowledge graph, sessions |
| **Agent** | Behavior Only | System prompts, tools, model config (shares workspace data) |

### 1.3 Key Design Principles

1. **Workspace = Knowledge Boundary**: All data isolation happens at workspace level
2. **Agent = Behavior Variant**: Multiple agents can exist in a workspace with different personalities but same knowledge
3. **Organization = Billing Entity**: Maps to your customers/accounts
4. **Users belong to Organizations**: Can access multiple workspaces they're granted access to
5. **API Keys are Workspace-Scoped**: Each workspace has its own API keys

---

## 2. Database Schema

### 2.1 Core Multi-Tenancy Tables

```sql
-- Organizations (your customers)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL, -- for URLs: app.example.com/org/acme-corp
    plan_tier TEXT NOT NULL DEFAULT 'free' CHECK (plan_tier IN ('free', 'starter', 'pro', 'enterprise')),

    -- Subscription info
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    subscription_status TEXT DEFAULT 'active' CHECK (subscription_status IN ('active', 'trialing', 'past_due', 'canceled', 'paused')),
    trial_ends_at TIMESTAMP WITH TIME ZONE,

    -- Limits based on plan
    max_workspaces INTEGER DEFAULT 1,
    max_documents_per_workspace INTEGER DEFAULT 100,
    max_monthly_requests INTEGER DEFAULT 10000,

    -- Contact info
    contact_email TEXT NOT NULL,
    contact_name TEXT,

    -- Metadata
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE -- Soft delete
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_plan_tier ON organizations(plan_tier);
CREATE INDEX idx_organizations_stripe_customer ON organizations(stripe_customer_id);


-- Workspaces (isolated knowledge bases)
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    slug TEXT NOT NULL, -- URL-friendly identifier
    description TEXT,

    -- Settings
    settings JSONB DEFAULT '{}', -- e.g., {"default_search_limit": 10, "enable_graph_search": true}

    -- Resource usage tracking
    document_count INTEGER DEFAULT 0,
    total_tokens_used BIGINT DEFAULT 0,
    monthly_requests INTEGER DEFAULT 0,
    last_request_reset_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(organization_id, slug)
);

CREATE INDEX idx_workspaces_organization ON workspaces(organization_id);
CREATE INDEX idx_workspaces_slug ON workspaces(organization_id, slug);
CREATE INDEX idx_workspaces_created_at ON workspaces(created_at DESC);


-- Agents (behavior configurations within workspaces)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    slug TEXT NOT NULL, -- URL-friendly: customer-support, sales-assistant
    description TEXT,

    -- Agent configuration
    system_prompt TEXT NOT NULL,
    model_provider TEXT NOT NULL DEFAULT 'openai', -- openai, anthropic, ollama, etc.
    model_name TEXT NOT NULL DEFAULT 'gpt-4',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER,

    -- Tool configuration (which tools this agent can use)
    enabled_tools JSONB DEFAULT '["vector_search", "hybrid_search"]', -- Array of tool names
    tool_config JSONB DEFAULT '{}', -- Tool-specific settings

    -- Behavior settings
    settings JSONB DEFAULT '{}',

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(workspace_id, slug)
);

CREATE INDEX idx_agents_workspace ON agents(workspace_id);
CREATE INDEX idx_agents_slug ON agents(workspace_id, slug);
CREATE INDEX idx_agents_active ON agents(workspace_id, is_active);


-- Users (people who access the system)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT, -- NULL for SSO users
    full_name TEXT,

    -- Auth
    email_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);


-- Organization members (users belong to organizations with roles)
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(organization_id, user_id)
);

CREATE INDEX idx_org_members_org ON organization_members(organization_id);
CREATE INDEX idx_org_members_user ON organization_members(user_id);


-- Workspace members (users can access specific workspaces)
CREATE TABLE workspace_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(workspace_id, user_id)
);

CREATE INDEX idx_workspace_members_workspace ON workspace_members(workspace_id);
CREATE INDEX idx_workspace_members_user ON workspace_members(user_id);


-- API Keys (workspace-scoped for programmatic access)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,

    name TEXT NOT NULL, -- "Production Key", "Development Key"
    key_prefix TEXT NOT NULL, -- First 8 chars for display: "sk_live_abc123..."
    key_hash TEXT NOT NULL, -- Hashed full key

    -- Permissions
    scopes JSONB DEFAULT '["chat", "search"]', -- What this key can do

    -- Rate limiting
    rate_limit_per_minute INTEGER DEFAULT 60,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_api_keys_workspace ON api_keys(workspace_id);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_active ON api_keys(workspace_id, is_active);
```

### 2.2 Updated Data Tables (Add workspace_id)

```sql
-- Update documents table
ALTER TABLE documents ADD COLUMN workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE;
CREATE INDEX idx_documents_workspace ON documents(workspace_id);

-- Update chunks table (inherited from document, but explicit for queries)
ALTER TABLE chunks ADD COLUMN workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE;
CREATE INDEX idx_chunks_workspace ON chunks(workspace_id);

-- Update sessions table
ALTER TABLE sessions
    ADD COLUMN workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    ADD COLUMN agent_id UUID REFERENCES agents(id) ON DELETE SET NULL;
CREATE INDEX idx_sessions_workspace ON sessions(workspace_id);
CREATE INDEX idx_sessions_agent ON sessions(agent_id);

-- Messages already linked via session, but can add for faster queries
ALTER TABLE messages ADD COLUMN workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE;
CREATE INDEX idx_messages_workspace ON messages(workspace_id);
```

### 2.3 Updated Search Functions

```sql
-- Updated vector search with workspace isolation
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(1536),
    workspace_id_filter UUID,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_source TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id AS chunk_id,
        c.document_id,
        c.content,
        1 - (c.embedding <=> query_embedding) AS similarity,
        c.metadata,
        d.title AS document_title,
        d.source AS document_source
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE c.embedding IS NOT NULL
      AND c.workspace_id = workspace_id_filter
      AND d.workspace_id = workspace_id_filter
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- Updated hybrid search with workspace isolation
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(1536),
    query_text TEXT,
    workspace_id_filter UUID,
    match_count INT DEFAULT 10,
    text_weight FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    combined_score FLOAT,
    vector_similarity FLOAT,
    text_similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_source TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            1 - (c.embedding <=> query_embedding) AS vector_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.embedding IS NOT NULL
          AND c.workspace_id = workspace_id_filter
          AND d.workspace_id = workspace_id_filter
    ),
    text_results AS (
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', query_text)) AS text_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', query_text)
          AND c.workspace_id = workspace_id_filter
          AND d.workspace_id = workspace_id_filter
    )
    SELECT
        COALESCE(v.chunk_id, t.chunk_id) AS chunk_id,
        COALESCE(v.document_id, t.document_id) AS document_id,
        COALESCE(v.content, t.content) AS content,
        (COALESCE(v.vector_sim, 0) * (1 - text_weight) + COALESCE(t.text_sim, 0) * text_weight) AS combined_score,
        COALESCE(v.vector_sim, 0) AS vector_similarity,
        COALESCE(t.text_sim, 0) AS text_similarity,
        COALESCE(v.metadata, t.metadata) AS metadata,
        COALESCE(v.doc_title, t.doc_title) AS document_title,
        COALESCE(v.doc_source, t.doc_source) AS document_source
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.chunk_id = t.chunk_id
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$;
```

### 2.4 Usage Tracking Tables

```sql
-- Track API usage per workspace for billing
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

    event_type TEXT NOT NULL, -- 'chat', 'search', 'ingest'

    -- Token usage
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,

    -- Metadata
    session_id UUID,
    user_id UUID,
    api_key_id UUID,

    -- Costs (if tracking)
    estimated_cost_usd DECIMAL(10, 6),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_workspace ON usage_events(workspace_id, created_at DESC);
CREATE INDEX idx_usage_org_date ON usage_events(workspace_id, date_trunc('day', created_at));


-- Aggregate usage per workspace per day (for billing)
CREATE TABLE daily_usage_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    date DATE NOT NULL,

    total_requests INTEGER DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,
    chat_requests INTEGER DEFAULT 0,
    search_requests INTEGER DEFAULT 0,

    estimated_cost_usd DECIMAL(10, 2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(workspace_id, date)
);

CREATE INDEX idx_daily_usage_workspace ON daily_usage_summary(workspace_id, date DESC);
```

---

## 3. API Architecture

### 3.1 API Structure

```
Base URL: https://api.example.com/v1

Authentication:
  - User JWT: For web app access
  - API Key: For programmatic access (workspace-scoped)

Endpoints Structure:
  /organizations/{org_id}/*           - Organization management
  /workspaces/{workspace_id}/*        - Workspace management
  /workspaces/{workspace_id}/agents/* - Agent management
  /workspaces/{workspace_id}/chat     - Chat with agents
  /workspaces/{workspace_id}/search   - Search workspace knowledge
  /workspaces/{workspace_id}/documents/* - Document management
```

### 3.2 Core Endpoints

#### Organization Management

```
POST   /organizations                    - Create organization
GET    /organizations/{org_id}           - Get organization details
PATCH  /organizations/{org_id}           - Update organization
DELETE /organizations/{org_id}           - Delete organization

GET    /organizations/{org_id}/workspaces - List workspaces
POST   /organizations/{org_id}/workspaces - Create workspace

GET    /organizations/{org_id}/members    - List members
POST   /organizations/{org_id}/members    - Add member
DELETE /organizations/{org_id}/members/{user_id} - Remove member

GET    /organizations/{org_id}/usage      - Get usage statistics
GET    /organizations/{org_id}/billing    - Get billing info
```

#### Workspace Management

```
GET    /workspaces/{workspace_id}         - Get workspace details
PATCH  /workspaces/{workspace_id}         - Update workspace
DELETE /workspaces/{workspace_id}         - Delete workspace

GET    /workspaces/{workspace_id}/agents  - List agents
POST   /workspaces/{workspace_id}/agents  - Create agent
GET    /workspaces/{workspace_id}/agents/{agent_id} - Get agent
PATCH  /workspaces/{workspace_id}/agents/{agent_id} - Update agent
DELETE /workspaces/{workspace_id}/agents/{agent_id} - Delete agent

GET    /workspaces/{workspace_id}/api-keys - List API keys
POST   /workspaces/{workspace_id}/api-keys - Create API key
DELETE /workspaces/{workspace_id}/api-keys/{key_id} - Revoke API key

GET    /workspaces/{workspace_id}/members  - List workspace members
POST   /workspaces/{workspace_id}/members  - Add member
```

#### Agent Chat & Search

```
POST   /workspaces/{workspace_id}/chat
       Body: {
         "agent_id": "uuid",
         "query": "string",
         "session_id": "uuid?",
         "stream": boolean
       }

POST   /workspaces/{workspace_id}/search
       Body: {
         "query": "string",
         "search_type": "vector|graph|hybrid",
         "limit": 10
       }
```

#### Document Management

```
GET    /workspaces/{workspace_id}/documents - List documents
POST   /workspaces/{workspace_id}/documents - Upload document
GET    /workspaces/{workspace_id}/documents/{doc_id} - Get document
DELETE /workspaces/{workspace_id}/documents/{doc_id} - Delete document

POST   /workspaces/{workspace_id}/ingest   - Bulk ingest documents
```

### 3.3 Authentication Flow

**Option 1: User JWT (Web App)**
```
1. User logs in → GET /auth/login
2. Returns JWT with claims: {user_id, org_id, role}
3. Include in requests: Authorization: Bearer <jwt>
4. Server validates JWT and checks workspace membership
```

**Option 2: API Key (Programmatic)**
```
1. User creates API key in dashboard
2. Key format: sk_{env}_{random}
   - sk_live_abc123...  (production)
   - sk_test_xyz789...  (testing)
3. Include in requests: Authorization: Bearer <api_key>
4. Server:
   - Hashes key and looks up in database
   - Validates workspace_id matches request
   - Checks scopes and rate limits
```

### 3.4 Authorization Middleware

```python
# Pseudo-code for authorization

async def require_workspace_access(
    workspace_id: str,
    user_id: str,
    required_role: str = "member"
) -> bool:
    """Check if user has access to workspace."""

    # Check if user is workspace member
    member = await get_workspace_member(workspace_id, user_id)
    if not member:
        # Maybe user has org-level access?
        workspace = await get_workspace(workspace_id)
        org_member = await get_org_member(workspace.org_id, user_id)
        if not org_member:
            raise HTTPException(403, "Access denied")
        if org_member.role not in ["owner", "admin"]:
            raise HTTPException(403, "Access denied")

    # Check role
    if not has_sufficient_role(member.role, required_role):
        raise HTTPException(403, "Insufficient permissions")

    return True


async def validate_api_key(api_key: str) -> Tuple[UUID, UUID]:
    """Validate API key and return (workspace_id, api_key_id)."""

    # Extract prefix
    prefix = api_key[:15]  # sk_live_abc123

    # Find key by prefix
    key_record = await get_api_key_by_prefix(prefix)
    if not key_record:
        raise HTTPException(401, "Invalid API key")

    # Verify full key hash
    key_hash = hash_api_key(api_key)
    if key_hash != key_record.key_hash:
        raise HTTPException(401, "Invalid API key")

    # Check if active
    if not key_record.is_active or (key_record.expires_at and key_record.expires_at < now()):
        raise HTTPException(401, "API key expired or revoked")

    # Check rate limit
    await check_rate_limit(key_record.id, key_record.rate_limit_per_minute)

    # Update last used
    await update_api_key_last_used(key_record.id)

    return (key_record.workspace_id, key_record.id)
```

---

## 4. Knowledge Graph Isolation

### 4.1 Graphiti Group IDs

Each workspace gets a unique Graphiti `group_id`:

```python
def get_workspace_graphiti_group_id(workspace_id: UUID) -> str:
    """Generate Graphiti group ID for workspace."""
    return f"workspace_{workspace_id}"

# When initializing Graphiti client:
graphiti_client = GraphitiClient(
    group_id=get_workspace_graphiti_group_id(workspace_id)
)
```

### 4.2 Graph Queries

All graph queries automatically filtered by group_id:

```cypher
// Graphiti handles this internally
MATCH (e:Entity {group_id: 'workspace_abc123'})
RETURN e

// No risk of cross-workspace data leakage
```

---

## 5. Data Models

### 5.1 Pydantic Models

```python
# models.py additions

class Organization(BaseModel):
    id: UUID
    name: str
    slug: str
    plan_tier: str
    max_workspaces: int
    max_documents_per_workspace: int
    contact_email: EmailStr
    created_at: datetime

class Workspace(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: Optional[str]
    settings: Dict[str, Any]
    document_count: int
    created_at: datetime

class Agent(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    slug: str
    description: Optional[str]
    system_prompt: str
    model_provider: str
    model_name: str
    temperature: float
    enabled_tools: List[str]
    is_active: bool

class User(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

class OrganizationMember(BaseModel):
    organization_id: UUID
    user_id: UUID
    role: str  # owner, admin, member, viewer

class WorkspaceMember(BaseModel):
    workspace_id: UUID
    user_id: UUID
    role: str  # admin, member, viewer

class APIKey(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    key_prefix: str  # For display only: "sk_live_abc123..."
    scopes: List[str]
    rate_limit_per_minute: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]

class ChatRequest(BaseModel):
    agent_id: UUID
    query: str
    session_id: Optional[UUID]
    stream: bool = False

class SearchRequest(BaseModel):
    query: str
    search_type: str = "hybrid"  # vector, graph, hybrid
    limit: int = 10
```

---

## 6. Pricing & Billing Integration

### 6.1 Plan Tiers

```python
PLAN_TIERS = {
    "free": {
        "price_monthly": 0,
        "max_workspaces": 1,
        "max_documents_per_workspace": 50,
        "max_monthly_requests": 1000,
        "max_agents_per_workspace": 2,
    },
    "starter": {
        "price_monthly": 29,
        "max_workspaces": 3,
        "max_documents_per_workspace": 500,
        "max_monthly_requests": 10000,
        "max_agents_per_workspace": 5,
    },
    "pro": {
        "price_monthly": 99,
        "max_workspaces": 10,
        "max_documents_per_workspace": 5000,
        "max_monthly_requests": 100000,
        "max_agents_per_workspace": 20,
    },
    "enterprise": {
        "price_monthly": None,  # Custom
        "max_workspaces": None,  # Unlimited
        "max_documents_per_workspace": None,
        "max_monthly_requests": None,
        "max_agents_per_workspace": None,
    }
}
```

### 6.2 Usage Metering

```python
async def track_usage(
    workspace_id: UUID,
    event_type: str,
    input_tokens: int,
    output_tokens: int,
    agent_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    api_key_id: Optional[UUID] = None
):
    """Track usage event for billing."""

    total_tokens = input_tokens + output_tokens

    # Estimate cost (example rates)
    cost = calculate_cost(
        model="gpt-4",
        input_tokens=input_tokens,
        output_tokens=output_tokens
    )

    # Insert usage event
    await db.insert_usage_event(
        workspace_id=workspace_id,
        event_type=event_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=cost,
        agent_id=agent_id,
        user_id=user_id,
        api_key_id=api_key_id
    )

    # Update workspace monthly counter
    await db.increment_workspace_monthly_requests(workspace_id)

    # Check if over limit
    workspace = await get_workspace_with_org(workspace_id)
    if workspace.monthly_requests > workspace.org.max_monthly_requests:
        # Send alert, block requests, etc.
        await send_overage_alert(workspace.org.id)
```

### 6.3 Stripe Integration Points

```python
# When creating organization
stripe_customer = stripe.Customer.create(
    email=contact_email,
    name=org_name,
    metadata={"org_id": str(org_id)}
)

# When upgrading plan
stripe_subscription = stripe.Subscription.create(
    customer=stripe_customer_id,
    items=[{"price": STRIPE_PRICE_IDS[plan_tier]}],
    metadata={"org_id": str(org_id)}
)

# Webhook handlers
@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    event = stripe.Webhook.construct_event(...)

    if event.type == "invoice.payment_succeeded":
        # Reset monthly usage counters
        await reset_monthly_usage(org_id)

    elif event.type == "customer.subscription.deleted":
        # Downgrade to free plan
        await downgrade_organization(org_id, "free")
```

---

## 7. Security Considerations

### 7.1 Isolation Guarantees

- ✅ **Database-level isolation**: All queries filtered by workspace_id
- ✅ **Graph isolation**: Graphiti group_id prevents cross-workspace queries
- ✅ **API key scoping**: Keys can only access their workspace
- ✅ **Session validation**: Sessions tied to specific workspace+agent
- ✅ **Row-level security**: Consider PostgreSQL RLS policies

### 7.2 PostgreSQL Row-Level Security (Optional)

```sql
-- Enable RLS on documents table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see documents in their accessible workspaces
CREATE POLICY workspace_isolation_policy ON documents
    USING (
        workspace_id IN (
            SELECT workspace_id
            FROM workspace_members
            WHERE user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- Set current user context before queries
SET LOCAL app.current_user_id = '<user_uuid>';
```

### 7.3 Rate Limiting

```python
# Per workspace rate limits
WORKSPACE_RATE_LIMITS = {
    "free": 10,      # req/min
    "starter": 60,
    "pro": 300,
    "enterprise": 1000
}

# Per API key rate limits (configurable)
async def check_rate_limit(api_key_id: UUID, limit: int):
    """Check rate limit for API key."""
    key = f"ratelimit:apikey:{api_key_id}"

    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)  # 1 minute window

    if current > limit:
        raise HTTPException(429, "Rate limit exceeded")
```

### 7.4 Data Encryption

- Encrypt API keys at rest (hashed)
- Encrypt sensitive organization data
- Use HTTPS/TLS for all API communication
- Encrypt backups

---

## 8. Migration Strategy

### 8.1 Phase 1: Add Multi-Tenancy Schema (Week 1)

```bash
# Run migration scripts
psql < migrations/001_add_organizations.sql
psql < migrations/002_add_workspaces.sql
psql < migrations/003_add_agents.sql
psql < migrations/004_add_users_and_members.sql
psql < migrations/005_add_api_keys.sql
psql < migrations/006_update_data_tables.sql
psql < migrations/007_add_usage_tracking.sql
```

### 8.2 Phase 2: Migrate Existing Data (Week 1-2)

```python
# migration_script.py

async def migrate_existing_data():
    """Migrate existing single-tenant data to multi-tenant structure."""

    # 1. Create default organization
    default_org = await create_organization(
        name="Default Organization",
        slug="default",
        plan_tier="enterprise",
        contact_email="admin@example.com"
    )

    # 2. Create default workspace
    default_workspace = await create_workspace(
        organization_id=default_org.id,
        name="Default Workspace",
        slug="default"
    )

    # 3. Create default agent(s)
    default_agent = await create_agent(
        workspace_id=default_workspace.id,
        name="General Assistant",
        slug="general",
        system_prompt=SYSTEM_PROMPT,  # Existing prompt
        enabled_tools=["vector_search", "graph_search", "hybrid_search"]
    )

    # 4. Update all existing documents
    await db.execute(
        "UPDATE documents SET workspace_id = $1",
        default_workspace.id
    )

    # 5. Update all existing chunks
    await db.execute(
        "UPDATE chunks SET workspace_id = $1",
        default_workspace.id
    )

    # 6. Update all existing sessions
    await db.execute(
        "UPDATE sessions SET workspace_id = $1, agent_id = $2",
        default_workspace.id,
        default_agent.id
    )

    print("Migration complete!")
```

### 8.3 Phase 3: Update Application Code (Week 2-3)

- Update API endpoints to use workspace/agent structure
- Add authentication middleware
- Implement API key management
- Update tools to filter by workspace_id
- Add usage tracking

### 8.4 Phase 4: Testing & Rollout (Week 3-4)

- Test multi-workspace isolation
- Test agent behavior within workspaces
- Load testing with multiple workspaces
- Security audit
- Documentation update
- Gradual rollout to beta users

---

## 9. Example Usage Scenarios

### 9.1 Scenario 1: SaaS Customer (Marketing Agency)

**Organization**: "Acme Marketing Agency"
- Plan: Pro ($99/mo)
- 3 Workspaces created:

**Workspace 1: "Client Alpha"**
- Documents: Client Alpha's brand guidelines, past campaigns
- Agents:
  - `content-writer`: Writes blog posts in client's voice
  - `social-media`: Creates social media content
  - `campaign-analyst`: Analyzes campaign performance

**Workspace 2: "Client Beta"**
- Documents: Client Beta's product catalog, market research
- Agents:
  - `product-copywriter`: Writes product descriptions
  - `seo-specialist`: SEO optimization recommendations

**Workspace 3: "Internal Knowledge"**
- Documents: Agency SOPs, templates, best practices
- Agents:
  - `onboarding-assistant`: Helps new employees
  - `process-expert`: Answers questions about internal processes

**Key Benefits:**
- Complete client data separation
- Specialized agents per client
- Shared internal knowledge workspace for employees

### 9.2 Scenario 2: Enterprise Customer (Software Company)

**Organization**: "TechCorp Inc"
- Plan: Enterprise (custom pricing)
- 5 Workspaces created:

**Workspace 1: "Customer Support"**
- Documents: Product docs, FAQs, troubleshooting guides
- Agents:
  - `tier1-support`: Handles common questions
  - `technical-support`: Deep technical assistance
  - `escalation-helper`: Helps decide when to escalate

**Workspace 2: "Sales Enablement"**
- Documents: Sales playbooks, competitor analysis, case studies
- Agents:
  - `sales-assistant`: Answers product questions for sales team
  - `demo-helper`: Helps prepare custom demos
  - `proposal-writer`: Drafts proposal sections

**Workspace 3: "Engineering Docs"**
- Documents: Architecture docs, API references, code standards
- Agents:
  - `code-reviewer`: Reviews code against standards
  - `api-expert`: Answers API integration questions
  - `architecture-advisor`: Architectural decisions

---

## 10. Monitoring & Observability

### 10.1 Key Metrics to Track

**Per Organization:**
- Total workspaces
- Total documents across workspaces
- Monthly request count
- Monthly token usage
- Estimated monthly cost
- Plan tier

**Per Workspace:**
- Document count
- Total vectors stored
- Graph size (nodes/edges)
- Request count (daily/monthly)
- Active agents
- API key usage
- Average response time

**Per Agent:**
- Request count
- Average tokens per request
- Tool usage distribution
- Error rate
- User satisfaction (if collecting feedback)

### 10.2 Alerting

```python
# Alert conditions
ALERTS = {
    "org_over_limit": {
        "condition": "monthly_requests > max_monthly_requests * 0.9",
        "action": "email_admin"
    },
    "workspace_over_document_limit": {
        "condition": "document_count > max_documents * 0.9",
        "action": "email_workspace_admins"
    },
    "high_error_rate": {
        "condition": "error_rate > 0.05",
        "action": "page_oncall"
    },
    "api_key_suspicious_usage": {
        "condition": "sudden_spike_in_requests",
        "action": "auto_revoke_and_alert"
    }
}
```

### 10.3 Logging

```python
# Structured logging format
{
    "timestamp": "2025-01-06T12:00:00Z",
    "level": "INFO",
    "event": "chat_request",
    "organization_id": "uuid",
    "workspace_id": "uuid",
    "agent_id": "uuid",
    "user_id": "uuid",
    "session_id": "uuid",
    "query_length": 150,
    "response_time_ms": 1234,
    "tokens_used": 500,
    "tools_called": ["vector_search", "graph_search"],
    "success": true
}
```

---

## 11. API Documentation Example

### 11.1 OpenAPI Spec Excerpt

```yaml
openapi: 3.0.0
info:
  title: Agentic RAG Multi-Tenant API
  version: 1.0.0

paths:
  /workspaces/{workspace_id}/chat:
    post:
      summary: Chat with an agent
      description: Send a message to a workspace agent with optional session context
      parameters:
        - in: path
          name: workspace_id
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                agent_id:
                  type: string
                  format: uuid
                  description: ID of the agent to chat with
                query:
                  type: string
                  description: User message
                session_id:
                  type: string
                  format: uuid
                  description: Optional session ID for context
                stream:
                  type: boolean
                  default: false
              required:
                - agent_id
                - query
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ChatResponse'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden - no access to workspace
        '429':
          description: Rate limit exceeded
      security:
        - ApiKeyAuth: []
        - BearerAuth: []

components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: Authorization
      description: "Format: Bearer sk_live_xxxxx"
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

## 12. Frontend Considerations

### 12.1 Dashboard Structure

```
App Layout:
  ├── Organization Selector (if user belongs to multiple)
  ├── Workspace Selector (dropdown)
  └── Main Content
      ├── Chat Interface
      │   ├── Agent Selector (dropdown)
      │   ├── Chat History
      │   └── Input Area
      ├── Documents Tab
      │   ├── Upload Documents
      │   ├── Document List
      │   └── Ingest Status
      ├── Agents Tab
      │   ├── Create/Edit Agents
      │   ├── Configure Tools
      │   └── Test Agent
      ├── Settings Tab
      │   ├── Workspace Settings
      │   ├── API Keys Management
      │   ├── Members Management
      │   └── Usage & Billing
      └── Analytics Tab
          ├── Request Volume
          ├── Token Usage
          └── Cost Estimates
```

### 12.2 Context Management (React Example)

```typescript
// WorkspaceContext.tsx
interface WorkspaceContextType {
  currentOrg: Organization | null;
  currentWorkspace: Workspace | null;
  currentAgent: Agent | null;
  setWorkspace: (workspaceId: string) => void;
  setAgent: (agentId: string) => void;
}

// Usage in components
function ChatInterface() {
  const { currentWorkspace, currentAgent } = useWorkspace();

  const sendMessage = async (query: string) => {
    const response = await fetch(
      `/workspaces/${currentWorkspace.id}/chat`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          agent_id: currentAgent.id,
          query: query
        })
      }
    );

    return response.json();
  };
}
```

---

## 13. Testing Strategy

### 13.1 Unit Tests

```python
# test_multi_tenancy.py

async def test_workspace_isolation():
    """Ensure workspaces cannot access each other's data."""

    # Create two workspaces
    workspace1 = await create_workspace(org_id, "Workspace 1")
    workspace2 = await create_workspace(org_id, "Workspace 2")

    # Add documents to each
    doc1 = await add_document(workspace1.id, "Secret doc 1")
    doc2 = await add_document(workspace2.id, "Secret doc 2")

    # Search in workspace1 should not return doc2
    results = await vector_search(
        workspace_id=workspace1.id,
        query="secret"
    )

    assert doc1.id in [r.document_id for r in results]
    assert doc2.id not in [r.document_id for r in results]


async def test_api_key_scope():
    """Ensure API keys only work for their workspace."""

    workspace1 = await create_workspace(org_id, "WS1")
    workspace2 = await create_workspace(org_id, "WS2")

    key1 = await create_api_key(workspace1.id, "Key 1")

    # Should work for workspace1
    response = await client.post(
        f"/workspaces/{workspace1.id}/chat",
        headers={"Authorization": f"Bearer {key1.key}"},
        json={"agent_id": agent1.id, "query": "test"}
    )
    assert response.status_code == 200

    # Should fail for workspace2
    response = await client.post(
        f"/workspaces/{workspace2.id}/chat",
        headers={"Authorization": f"Bearer {key1.key}"},
        json={"agent_id": agent2.id, "query": "test"}
    )
    assert response.status_code == 403


async def test_agent_shares_workspace_knowledge():
    """Agents in same workspace should see same documents."""

    workspace = await create_workspace(org_id, "Shared WS")
    agent1 = await create_agent(workspace.id, "Agent 1")
    agent2 = await create_agent(workspace.id, "Agent 2")

    doc = await add_document(workspace.id, "Shared knowledge")

    # Both agents should find the document
    results1 = await agent_search(workspace.id, agent1.id, "shared")
    results2 = await agent_search(workspace.id, agent2.id, "shared")

    assert doc.id in [r.document_id for r in results1]
    assert doc.id in [r.document_id for r in results2]
```

### 13.2 Integration Tests

```python
async def test_complete_workflow():
    """Test complete workflow from org creation to chat."""

    # 1. Create organization
    org = await create_organization("Test Corp", "test-corp")

    # 2. Create workspace
    workspace = await create_workspace(
        org.id,
        name="Customer Support",
        slug="support"
    )

    # 3. Create agent
    agent = await create_agent(
        workspace.id,
        name="Support Bot",
        slug="support-bot",
        system_prompt="You are helpful support agent",
        enabled_tools=["vector_search", "hybrid_search"]
    )

    # 4. Add documents
    await ingest_documents(workspace.id, "test_docs/")

    # 5. Create API key
    api_key = await create_api_key(workspace.id, "Test Key")

    # 6. Chat with agent
    response = await client.post(
        f"/workspaces/{workspace.id}/chat",
        headers={"Authorization": f"Bearer {api_key.key}"},
        json={
            "agent_id": agent.id,
            "query": "How do I reset my password?"
        }
    )

    assert response.status_code == 200
    assert "password" in response.json()["response"].lower()
```

---

## 14. Performance Considerations

### 14.1 Connection Pooling

```python
# Adjust pool size based on expected workspaces
db_pool = await asyncpg.create_pool(
    database_url,
    min_size=10,  # Base connections
    max_size=50,  # Scale with number of active workspaces
    max_inactive_connection_lifetime=300
)
```

### 14.2 Caching Strategy

```python
# Cache frequently accessed data
CACHE_TTL = {
    "workspace": 300,      # 5 minutes
    "agent": 300,
    "organization": 600,   # 10 minutes
    "api_key": 60,         # 1 minute (security sensitive)
}

async def get_workspace_cached(workspace_id: UUID) -> Workspace:
    """Get workspace with caching."""

    cache_key = f"workspace:{workspace_id}"

    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        return Workspace.parse_raw(cached)

    # Fetch from DB
    workspace = await db.get_workspace(workspace_id)

    # Cache it
    await redis.setex(
        cache_key,
        CACHE_TTL["workspace"],
        workspace.json()
    )

    return workspace
```

### 14.3 Query Optimization

```sql
-- Ensure proper indexes
CREATE INDEX idx_chunks_workspace_embedding ON chunks(workspace_id, embedding);
CREATE INDEX idx_documents_workspace_created ON documents(workspace_id, created_at DESC);
CREATE INDEX idx_sessions_workspace_updated ON sessions(workspace_id, updated_at DESC);

-- Consider partitioning for large datasets
CREATE TABLE chunks_partitioned (
    LIKE chunks INCLUDING ALL
) PARTITION BY HASH (workspace_id);

CREATE TABLE chunks_part_0 PARTITION OF chunks_partitioned FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE chunks_part_1 PARTITION OF chunks_partitioned FOR VALUES WITH (MODULUS 4, REMAINDER 1);
-- etc.
```

---

## 15. Deployment Architecture

### 15.1 Infrastructure Components

```
┌─────────────────┐
│   Load Balancer │ (CloudFlare, AWS ALB)
└────────┬────────┘
         │
    ┌────┴────┐
    │   API   │ (Auto-scaling FastAPI instances)
    │ Servers │ (3+ instances for HA)
    └────┬────┘
         │
    ┌────┴──────────────────────┐
    │                           │
┌───▼────┐                 ┌───▼─────┐
│ Postgres│                │  Neo4j  │
│ (Primary)│               │ Cluster │
│   +     │                └─────────┘
│ Replicas│
└─────────┘
    │
┌───▼────┐
│  Redis │ (Caching + Rate Limiting)
└────────┘
```

### 15.2 Scaling Considerations

**Database Scaling:**
- PostgreSQL: Use read replicas for search queries
- Neo4j: Use clustering for high availability
- Consider sharding by workspace_id for extreme scale

**API Scaling:**
- Stateless API servers (horizontal scaling)
- Load balance based on workspace_id for cache efficiency
- Use CDN for static assets

**Vector Search Scaling:**
- Consider dedicated vector DB (Pinecone, Weaviate) for 100k+ workspaces
- Shard vectors by workspace

---

## 16. Next Steps (Prototype Implementation)

### Phase 1: Core Multi-Tenancy (Days 1-3)
1. Create database migrations
2. Add Organization, Workspace, Agent models
3. Update database utilities
4. Basic workspace isolation in tools

### Phase 2: API Updates (Days 4-6)
5. Add workspace/agent management endpoints
6. Update chat endpoint for workspace/agent routing
7. Implement API key authentication
8. Add basic authorization checks

### Phase 3: Testing & Validation (Days 7-8)
9. Write isolation tests
10. Test with 2-3 example workspaces
11. Load testing
12. Security audit

### Phase 4: Documentation (Day 9-10)
13. API documentation
14. Migration guide
15. Example configurations
16. Deployment guide

**Timeline: 2 weeks for complete prototype**

---

## 17. Summary

This SaaS multi-tenant architecture provides:

✅ **Complete data isolation** at workspace level
✅ **Flexible agent configuration** within workspaces
✅ **Scalable billing structure** with usage tracking
✅ **Secure API access** with workspace-scoped keys
✅ **Team collaboration** with organization/workspace membership
✅ **Production-ready** security and performance considerations

The design balances:
- **Simplicity**: One database cluster, logical partitioning
- **Security**: Strong isolation guarantees
- **Flexibility**: Multiple agents per workspace
- **Scalability**: Can grow to thousands of workspaces
- **Cost-effectiveness**: Efficient resource utilization

Ready to proceed with prototype implementation?
