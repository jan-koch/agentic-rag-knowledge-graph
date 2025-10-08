# Quick Start Guide

## 🚀 Running the Multi-Tenant RAG System

### Option 1: Local Development

```bash
# 1. Start databases
docker compose up -d

# 2. Start API server
python -m agent.api_multi_tenant

# 3. Start dashboard (in new terminal)
streamlit run webui.py
```

Access:
- **API**: http://localhost:8058
- **Dashboard**: http://localhost:8501

### Option 2: Production with Docker

```bash
# 1. Start databases
docker compose up -d

# 2. Start API server
python -m agent.api_multi_tenant

# 3. Start dashboard in Docker
docker compose -f docker-compose.dashboard.yml up -d --build
```

Access:
- **API**: http://localhost:8058 (internal only)
- **Dashboard**: https://bot.kobra-dataworks.de (public)
- **Dashboard (local)**: http://localhost:8501

## 📋 First Time Setup

### 1. Create Organization

Dashboard → Organizations → Create New Organization
- Name: Your Company
- Slug: your-company
- Email: admin@example.com
- Plan: Choose tier (free/starter/pro/enterprise)

### 2. Create Workspace

Dashboard → Workspaces → Create New Workspace
- Select organization
- Name: Customer Support
- Slug: support
- Description: Support knowledge base

### 3. Ingest Documents

```bash
# Ingest documents into workspace
python ingest_workspace.py \
  --workspace-id <workspace-id> \
  --path /path/to/documents
```

### 4. Create Agent

Dashboard → Agents → Create New Agent
- Select workspace
- Name: Support Bot
- Model: gpt-4 or claude-3
- Enable tools: vector_search, hybrid_search

### 5. Start Chatting

Dashboard → Chat
- Select workspace and agent from sidebar
- Start asking questions!

## 🐳 Docker Commands

```bash
# Build dashboard
docker compose -f docker-compose.dashboard.yml build

# Start dashboard
docker compose -f docker-compose.dashboard.yml up -d

# View logs
docker compose -f docker-compose.dashboard.yml logs -f dashboard

# Stop dashboard
docker compose -f docker-compose.dashboard.yml down

# Restart dashboard
docker compose -f docker-compose.dashboard.yml restart

# Rebuild and restart
docker compose -f docker-compose.dashboard.yml up -d --build
```

## 🔍 Health Checks

```bash
# API health
curl http://localhost:8058/v1/health

# Dashboard health (Streamlit)
curl http://localhost:8501/_stcore/health

# Check running containers
docker ps
```

## 📊 Monitoring

### Dashboard Sidebar
- ✅ Status: Shows API connectivity
- Multi-Tenant: Enabled/Disabled
- Version: Current version

### System Overview (Dashboard Page)
- Total organizations
- Total workspaces
- Total documents
- Active agents
- Monthly requests

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (API keys, DB URLs) |
| `webui.py` | Dashboard configuration (API URL: localhost:8058) |
| `.streamlit/config.toml` | Streamlit settings |
| `docker-compose.dashboard.yml` | Docker configuration |

## 🌐 Network Architecture

```
Internet
    ↓
bot.kobra-dataworks.de (HTTPS)
    ↓
Reverse Proxy / Tunnel
    ↓
localhost:8501 (Dashboard) → localhost:8058 (API)
```

**Important**: Dashboard and API communicate via localhost. Your reverse proxy maps the public domain to localhost:8501.

## 📚 Documentation

- **RUN_DASHBOARD.md**: Basic dashboard usage
- **DASHBOARD_DEPLOYMENT.md**: Detailed deployment guide
- **WEBUI_GUIDE.md**: Dashboard features guide
- **DATA_SAFETY.md**: Database safety practices
- **N8N_INTEGRATION.md**: n8n workflow integration

## 🆘 Troubleshooting

### Dashboard shows "API Unavailable"
```bash
# Check API is running
curl http://localhost:8058/v1/health

# Restart API
python -m agent.api_multi_tenant
```

### Can't access bot.kobra-dataworks.de
```bash
# Check dashboard is running
curl http://localhost:8501/_stcore/health

# Check reverse proxy/tunnel configuration
```

### Docker container won't start
```bash
# Check logs
docker compose -f docker-compose.dashboard.yml logs dashboard

# Rebuild image
docker compose -f docker-compose.dashboard.yml build --no-cache

# Check port not in use
sudo lsof -i :8501
```

## 🔐 Security Notes

- Dashboard runs on localhost (not exposed directly)
- API runs on localhost (not exposed directly)
- Reverse proxy provides SSL/TLS
- Use strong passwords in `.env`
- Keep API keys secure
- Enable `API_KEY_REQUIRED=true` in production

## 🚦 Status Indicators

### Workspace Sync Status
- 🟢 **Active**: Updated < 1 hour ago
- 🟡 **Recent**: Updated < 24 hours ago
- ⚪ **Idle**: Updated > 24 hours ago

### Capacity Warnings
- ✅ **< 80%**: Normal
- ⚠️ **> 80%**: Approaching limit

## 📞 Support

For issues or questions:
1. Check this guide
2. Review [DASHBOARD_DEPLOYMENT.md](DASHBOARD_DEPLOYMENT.md)
3. Check logs: `docker logs rag-dashboard`
4. Verify configuration files
