# Running the Streamlit Dashboard

## Quick Start

```bash
# 1. Make sure the API server is running
python -m agent.api_multi_tenant

# 2. In a separate terminal, run the Streamlit dashboard
streamlit run webui.py
```

The dashboard will open at http://localhost:8501

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

The dashboard connects to the API at `http://localhost:8058/v1` by default.

To change the API URL, edit `webui.py`:
```python
API_BASE_URL = "http://your-api-url:port/v1"
```

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
