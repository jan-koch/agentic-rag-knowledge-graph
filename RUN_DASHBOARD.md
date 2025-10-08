# Running the Streamlit Dashboard

## Quick Start

### Local Development

```bash
# 1. Make sure the API server is running
python -m agent.api_multi_tenant

# 2. In a separate terminal, run the Streamlit dashboard
streamlit run webui.py
```

The dashboard will open at http://localhost:8501

### Docker Deployment

```bash
# Build and run dashboard in Docker (uses localhost:8058 for API)
docker compose -f docker-compose.dashboard.yml up -d --build

# View logs
docker compose -f docker-compose.dashboard.yml logs -f

# Stop dashboard
docker compose -f docker-compose.dashboard.yml down
```

Dashboard accessible at:
- Local: http://localhost:8501
- Public (when mapped): https://bot.kobra-dataworks.de

**Note**: The dashboard uses `localhost` for all connections. Set up your reverse proxy/tunnel to map `localhost:8501` to your public domain.

## Features

### 📊 Dashboard Page
- System-wide metrics and analytics
- Organization, workspace, document counts
- Top workspaces by document count
- Agent status overview
- Monthly request tracking

### 🏢 Organizations
- Create and manage organizations
- View organization details
- Set plan tiers (free, starter, pro, enterprise)
- Track workspace usage vs limits

### 📁 Workspaces
- Comprehensive workspace overview
- Document count with capacity warnings
- Sync status indicators:
  - 🟢 Active (< 1 hour)
  - 🟡 Recent (< 24 hours)
  - ⚪ Idle (> 24 hours)
- Quick actions for document ingestion
- Per-workspace metrics

### 🤖 Agents
- Create and configure AI agents
- Select model provider (OpenAI, Ollama, etc.)
- Configure tools and parameters
- View agent status

### 🔑 API Keys
- Generate workspace-specific API keys
- Set scopes and rate limits
- Manage key expiration

### 💬 Chat
- Interactive chat with workspace agents
- Select workspace and agent
- Session management
- Message history
- Tool usage visibility
- Clear chat history

### 🏥 Health
- System health status
- API connectivity check
- Multi-tenant mode verification

## Configuration

The dashboard is configured to use `localhost` for all connections:
- **API**: `http://localhost:8058/v1` (line 14 in `webui.py`)
- **Dashboard**: `http://localhost:8501` (Streamlit default)

**Do not change these URLs.** Your reverse proxy/tunnel will map `localhost:8501` to `bot.kobra-dataworks.de`.

For detailed Docker deployment and reverse proxy setup, see [DASHBOARD_DEPLOYMENT.md](DASHBOARD_DEPLOYMENT.md).

## Requirements

The dashboard uses the following from requirements.txt:
- streamlit
- requests

These should already be installed if you ran `pip install -r requirements.txt`.

## Tips

1. **First Time Setup**:
   - Start on the Dashboard page to see overall status
   - Create an organization first
   - Then create workspaces under that organization
   - Ingest documents using `python ingest_workspace.py`
   - Create agents to enable chat

2. **Monitoring**:
   - Use Dashboard page for quick overview
   - Check Workspaces page for capacity warnings
   - Monitor sync status to identify idle workspaces

3. **Chat**:
   - Select workspace and agent from sidebar
   - Chat history persists during the session
   - Use "Clear Chat History" to start fresh
   - Expand tool usage to see what the agent did

## Troubleshooting

**Dashboard shows "API Unavailable"**:
- Make sure `python -m agent.api_multi_tenant` is running
- Check that the API is accessible at http://localhost:8058

**No organizations/workspaces shown**:
- Create them using the Organizations and Workspaces pages
- Or use the API directly to create test data

**Chat not working**:
- Ensure you have created at least one organization, workspace, and agent
- Check that the agent is marked as "Active"
- Verify the workspace has documents ingested
