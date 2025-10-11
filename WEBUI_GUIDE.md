# Web UI Guide

## Quick Start

The multi-tenant RAG system now has a web-based admin dashboard built with Streamlit!

### Starting the Web UI

```bash
# Start the API server (if not already running)
source venv/bin/activate
python -m agent.api

# In another terminal, start the Web UI
source venv/bin/activate
streamlit run webui.py --server.port 8012
```

The Web UI will be available at: **http://localhost:8012**

**Production Access**: https://bot.kobra-dataworks.de (via Cloudflare tunnel)

### Features

#### 📤 Document Ingestion (NEW!)
- **Ingest via Web UI**: Navigate to Workspaces page → Show workspace details → "📤 Ingest Documents"
- **Browse local files**: Automatically finds `.md`, `.markdown`, and `.txt` files in specified folder
- **Real-time progress**: See ingestion status with progress indicators
- **Detailed results**: View chunks created, entities extracted, and any errors
- **Multi-tenant support**: Each workspace has isolated document storage
- **Clean mode**: Option to remove existing documents before ingesting
- **Documentation**: See `STREAMLIT_INGESTION_GUIDE.md` for detailed guide

#### 🏢 Organizations Management
- **Create** new organizations with custom plan tiers
- **View** organization details
- Manage billing entities

#### 📁 Workspaces Management
- **Create** workspaces within organizations
- **List** all workspaces for an organization
- **View** workspace details and statistics
- Track document count and monthly requests

#### 🤖 Agents Management
- **Create** agents with custom configurations
  - Set system prompts
  - Choose LLM providers (OpenAI, Ollama, OpenRouter, Gemini)
  - Configure temperature and max tokens
  - Enable/disable tools (vector_search, hybrid_search, graph_search, etc.)
- **List** all agents in a workspace
- **View** agent details and configurations
- Filter active/inactive agents

#### 🔑 API Keys Management
- **Create** workspace-scoped API keys
- Set custom scopes (chat, search, ingest, admin)
- Configure rate limits
- Set expiration dates
- **⚠️ API keys are only shown once at creation!**

#### 💬 Chat Interface
- **Interactive chat**: Test agents directly in the UI
- **Session management**: Persistent conversation history
- **Tool usage tracking**: See which tools the agent uses
- **Workspace & agent selection**: Choose from available workspaces and agents

#### 📊 Health & Status
- Real-time system health monitoring
- API availability status
- Version information

## Navigation

Use the sidebar to navigate between different sections:
- 📊 Dashboard - System overview and metrics
- 🏢 Organizations - Create and manage organizations
- 📁 Workspaces - Manage workspaces and ingest documents
- 🤖 Agents - Configure AI agents
- 🔑 API Keys - Generate workspace-scoped API keys
- 💬 Chat - Interactive chat with agents
- 🏥 Health - System health and API status

## Example Workflow

### 1. Create an Organization
1. Go to **🏢 Organizations**
2. Fill in the form:
   - Organization Name: "Acme Corporation"
   - Slug: "acme"
   - Contact Email: "admin@acme.com"
   - Plan Tier: Select from dropdown
3. Click **Create Organization**
4. Copy the Organization ID

### 2. Create a Workspace
1. Go to **📁 Workspaces**
2. Fill in the form:
   - Organization ID: Paste from step 1
   - Workspace Name: "Customer Support"
   - Slug: "support"
   - Description: "Support knowledge base"
3. Click **Create Workspace**
4. Copy the Workspace ID

### 3. Create an Agent
1. Go to **🤖 Agents**
2. Fill in the form:
   - Workspace ID: Paste from step 2
   - Agent Name: "Support Bot"
   - System Prompt: "You are a helpful support agent..."
   - Model Provider: "openai"
   - Model Name: "gpt-4"
   - Temperature: 0.7
   - Tools: Select from multiselect
3. Click **Create Agent**
4. Copy the Agent ID

### 4. Create an API Key
1. Go to **🔑 API Keys**
2. Fill in the form:
   - Workspace ID: Paste from step 2
   - Key Name: "Production Key"
   - Scopes: Select "chat" and "search"
   - Rate Limit: 60 requests/minute
3. Click **Create API Key**
4. **⚠️ SAVE THE API KEY IMMEDIATELY - IT WON'T BE SHOWN AGAIN!**

### 5. Use the API
Now you can use the created resources via the REST API or (coming soon) the chat interface.

## Configuration

The Web UI connects to the API at: `http://localhost:8058/v1`

**Note**: Both the API and Web UI run on `localhost` by default. External access is provided via Cloudflare tunnel.

### Systemd Services

For production deployments, use systemd services to auto-start on boot:

```bash
# Install both API and Dashboard services
sudo ./install-services.sh

# Or manually manage services
sudo systemctl start rag-api rag-dashboard
sudo systemctl enable rag-api rag-dashboard
```

See `SYSTEMD_SERVICES.md` for complete documentation.

## Deployment

### Development
```bash
streamlit run webui.py --server.port 8012 --server.address 127.0.0.1
```

### Production (Systemd)
```bash
# Install services (recommended)
sudo ./install-services.sh

# The dashboard runs on 127.0.0.1:8012
# External access via Cloudflare tunnel: https://bot.kobra-dataworks.de
```

For production deployment:
- ✅ **Systemd services** provide auto-start and auto-restart
- ✅ **Cloudflare tunnel** provides secure external access
- ✅ **Localhost binding** (127.0.0.1) prevents direct external access
- ✅ **Service logs** available via `journalctl`

## Troubleshooting

### Port Already in Use
If port 8012 is in use, specify a different port:
```bash
streamlit run webui.py --server.port 8013
```

### API Connection Failed
- Ensure the API server is running: `python -m agent.api`
- Check the API is accessible at: `http://localhost:8058/v1/health`
- Verify the `API_BASE_URL` in `webui.py`

### Missing Dependencies
```bash
pip install streamlit requests
```

## Screenshots

The Web UI features:
- ✅ Clean, modern interface
- ✅ Sidebar navigation
- ✅ Form-based resource creation
- ✅ Real-time status indicators
- ✅ JSON response viewers
- ✅ Expandable lists
- ✅ Color-coded alerts

## Next Steps

After setting up your resources in the Web UI:
1. **Ingest documents**: Use the built-in ingestion feature in Workspaces page
2. **Test chat**: Use the Chat page to interact with your agents
3. **Monitor usage**: View statistics on the Dashboard page
4. **Create agents**: Configure multiple agents with different behaviors
5. **Generate API keys**: Create keys for programmatic access

## Support

For issues or questions:
- Check `MULTI_TENANT_README.md` for API documentation
- Review `MULTI_TENANT_IMPLEMENTATION_STATUS.md` for current features
- Check the API logs for detailed error messages

---

**Version**: 1.1.0
**Last Updated**: 2025-01-09
**New Features**: Document ingestion via Web UI, systemd services, chat interface
