# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📋 Essential Commands

### Development Environment Setup
- **Virtual environment**: `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
- **Install dependencies**: `pip install -r requirements.txt`
- **Docker setup**: `./scripts/docker-setup.sh` (sets up PostgreSQL + Neo4j containers)
- **Alternative manual database setup**: Execute SQL in `sql/schema.sql` (adjust embedding dimensions for your model)

### Docker Database Management
- **Start databases**: `docker compose up -d` (PostgreSQL on 5432, Neo4j on 7474/7687)
- **Stop databases**: `docker compose down`
- **View logs**: `docker compose logs -f [postgres|neo4j]`
- **Restart databases**: `docker compose restart`
- **Remove volumes/reset**: `docker compose down -v` (⚠️ destroys all data)

### Running the System
- **Document ingestion (CLI)**: `python -m ingestion.ingest` (required first step)
- **Document ingestion (Web UI)**: Use Streamlit dashboard (see below)
- **Workspace-specific ingestion**: `python ingest_workspace.py --workspace-id <UUID> --directory documents/`
- **Clean and re-ingest**: `python -m ingestion.ingest --clean`
- **Start API server**: `python -m agent.api` (defaults to port 8058)
- **Start Web UI**: `streamlit run webui.py --server.port 8012` (admin dashboard on 127.0.0.1:8012)
- **CLI interface**: `python cli.py` (connects to API at 127.0.0.1:8058)

### Web UI & Document Ingestion
- **Admin Dashboard**: `streamlit run webui.py` - Multi-tenant admin interface on port 8012
- **Ingestion via Web UI**: Navigate to Workspaces page → Expand workspace details → "📤 Ingest Documents"
  - Browse documents in `/documents` folder
  - Select workspace for multi-tenant ingestion
  - View real-time ingestion progress and results
  - See detailed statistics (chunks, entities, errors)
- **Features**: Organizations, workspaces, agents, API keys management, chat interface, health monitoring
- **Documentation**: See `STREAMLIT_INGESTION_GUIDE.md` for detailed ingestion guide
- **Access**: Deployed at `https://bot.kobra-dataworks.de` via Cloudflare tunnel (maps to localhost:8012)

### Systemd Services (Auto-Start on Boot)
- **Installation**: `sudo ./install-services.sh` - Sets up both API and Dashboard as system services
- **Service management**:
  - Start: `sudo systemctl start rag-api` / `sudo systemctl start rag-dashboard`
  - Stop: `sudo systemctl stop rag-api` / `sudo systemctl stop rag-dashboard`
  - Restart: `sudo systemctl restart rag-api` / `sudo systemctl restart rag-dashboard`
  - Status: `sudo systemctl status rag-api` / `sudo systemctl status rag-dashboard`
  - Logs: `sudo journalctl -u rag-api -f` / `sudo journalctl -u rag-dashboard -f`
- **Services**: `rag-api.service` (port 8058), `rag-dashboard.service` (port 8012)
- **Documentation**: See `SYSTEMD_SERVICES.md` for complete setup guide

### Testing and Quality
- **Run all tests**: `pytest` (58 tests, >80% coverage required)
- **Run with coverage**: `pytest --cov=agent --cov=ingestion --cov-report=html`
- **Run specific test modules**: `pytest tests/agent/` or `pytest tests/ingestion/`
- **Test markers available**: `-m "not slow"`, `-m integration`, `-m unit`

### Production Deployment
- **Deploy to production**: `./scripts/deploy-production.sh`
- **Setup Cloudflare tunnel**: `./scripts/setup-cloudflare-tunnel.sh`
- **Backup PostgreSQL**: `./scripts/backup-database.sh`
- **Backup Neo4j**: `./scripts/backup-neo4j.sh`
- **Production compose**: `docker compose -f docker-compose.prod.yml up -d`

## 🏗 Architecture Overview

This is a hybrid RAG system combining vector search with knowledge graphs, built on:

**Core Stack**: Python 3.11+ with Pydantic AI agents, FastAPI, PostgreSQL+pgvector, Neo4j+Graphiti

**Key Components**:
- `/agent/` - Pydantic AI agent system with tools, providers, and FastAPI API
- `/ingestion/` - Document processing pipeline with semantic chunking and graph building
- `/tests/` - Comprehensive test suite with mocks for external dependencies
- `/cli.py` - Interactive CLI with tool usage visibility and streaming responses

**Agent Tools**: The system provides vector_search, graph_search, hybrid_search, document retrieval, and entity relationship tools. Tool selection is controlled by prompts in `agent/prompts.py`.

**Provider System**: Flexible LLM support for OpenAI, Ollama, OpenRouter, and Gemini via `agent/providers.py`. Uses separate models for chat vs ingestion (configurable via `LLM_CHOICE` and `INGESTION_LLM_CHOICE`).

**Database Architecture**:
- PostgreSQL stores documents, chunks with embeddings, sessions, and messages
- Neo4j (via Graphiti) stores temporal knowledge graph with entities and relationships
- Both use OpenAI-compatible client configuration for consistent API interfaces
- **Docker Setup**: Automated with `./scripts/docker-setup.sh` - includes health checks and connection verification

**Multi-Tenant Workspace Isolation** (✨ NEW):
- Complete workspace isolation via Graphiti `group_id` parameter
- Each workspace has dedicated knowledge graph client with workspace-specific group_id
- Workspace-aware dynamic system prompts constrain agent to workspace data only
- Vector search filtered by `workspace_id` in PostgreSQL
- Graph search isolated via workspace-specific Graphiti clients
- No data leakage between workspaces - see `MULTI_TENANT_README.md` for details

## 📁 Key File Locations

- **Agent configuration**: `agent/prompts.py` controls tool selection behavior
- **Database utilities**: `agent/db_utils.py` (PostgreSQL) and `agent/graph_utils.py` (Neo4j/Graphiti)
- **Data models**: `agent/models.py` with Pydantic validation and ToolCall tracking
- **Security layer**: `agent/security.py` with API key validation and rate limiting
- **Environment config**: `.env` (created from `.env.example`) with Docker database URLs pre-configured
- **Database schema**: `sql/schema.sql` with pgvector setup (copied to `docker/postgres/init.sql`)
- **Docker configuration**: `docker-compose.yml` and `scripts/docker-setup.sh` for containerized databases
- **n8n integration**: `N8N_INTEGRATION.md` documents webhook endpoints for workflow automation

## 🔒 Security Features

- **API Authentication**: Configurable API key requirement via `API_KEY_REQUIRED` env var
- **Rate limiting**: Built-in rate limiting (60 requests/minute default)
- **CORS configuration**: Controlled via `ALLOWED_ORIGINS` environment variable
- **Session management**: Automatic timeout and message limits per session
- **Input validation**: Pydantic models validate all inputs
- **Security middleware**: See `agent/security.py` for implementation details

## 💬 Chat Widget Features (✨ NEW)

**Conversation Persistence**:
- Sessions automatically saved to browser localStorage
- Conversations restore on widget reopen (60-minute session timeout)
- "New Chat" button for starting fresh conversations
- Separate conversation history per workspace/agent combination
- Endpoint: `GET /sessions/{session_id}/messages` for history retrieval

**Multilingual Support**:
- English (en) and German (de) translations
- Configurable via `language` URL parameter
- Translates: Send button, New Chat button, placeholders, loading messages
- See `CHAT_WIDGET_INTEGRATION.md` for embedding instructions

**Widget Endpoints**:
- `/widget/chat` - Embeddable chat widget HTML
- `/static/chat-widget-secure.js` - Secure widget with API key auth
- `/v1/widget/validate` - API key validation and workspace config

## 🔄 Workflow Integration

The system provides n8n webhook endpoints for workflow automation:
- `/n8n/chat` - Full chat with session management and tool tracking
- `/n8n/simple` - Simple Q&A without session management
- See `N8N_INTEGRATION.md` for detailed setup instructions

## 📊 Monitoring and Debugging

- **API logs**: Set `LOG_LEVEL=DEBUG` in `.env` for verbose logging
- **Tool usage tracking**: All agent tool calls are logged with `ToolCall` models
- **Session history**: Stored in PostgreSQL with full message/tool tracking
- **Performance profiling**: Enable with `ENABLE_PROFILING=true`
- **Test authentication**: Use `test_api_auth.py` to verify API key setup
- **Test n8n integration**: Use `test_n8n_integration.py` to verify webhook endpoints

## 🚀 Deployment Notes

- **Production config**: Use `docker-compose.prod.yml` with proper resource limits
- **Environment separation**: Maintain separate `.env.production` for production
- **Cloudflare tunnel**: Script available for secure external access
- **Database backups**: Automated scripts for both PostgreSQL and Neo4j
- **Security checklist**: Review `SECURITY.md` before production deployment
- **Deployment guide**: Full instructions in `PRODUCTION_DEPLOYMENT.md`

## 📝 Important Configuration Notes

- **Embedding dimensions**: Must match your model (1536 for OpenAI text-embedding-3-small, 768 for nomic-embed-text)
- **Chunk sizes**: Optimized for Graphiti token limits (800 default, 1500 max)
- **Session limits**: Configurable timeout (60 min) and message limits (100 max)
- **File processing**: Supports `.md` and `.txt` files up to 10MB
- **Vector search**: Returns up to 10 results by default (configurable)