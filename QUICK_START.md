# Quick Start Guide

## 🚀 Running the Multi-Tenant RAG System

### Development Mode

```bash
# 1. Start databases
docker compose up -d

# 2. Start API server
python -m agent.api_multi_tenant

# 3. Start dashboard
streamlit run webui.py
```

Access:
- **API**: http://localhost:8058
- **Dashboard**: http://127.0.0.1:8501
- **Public**: https://bot.kobra-dataworks.de (via Cloudflare tunnel)

### Production Mode (Auto-Start on Boot)

```bash
# Install systemd service (one-time setup)
sudo ./scripts/install-dashboard-service.sh
```

The dashboard will now:
- Start automatically on server boot
- Restart automatically if it crashes
- Log to `/var/log/rag-dashboard.log`

Service management:
```bash
sudo systemctl start rag-dashboard    # Start
sudo systemctl stop rag-dashboard     # Stop
sudo systemctl restart rag-dashboard  # Restart
sudo systemctl status rag-dashboard   # Check status
sudo journalctl -u rag-dashboard -f   # View logs
```

See [SYSTEMD_SERVICE.md](SYSTEMD_SERVICE.md) for details.

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

## 🔧 Service Management

```bash
# Start dashboard service
sudo systemctl start rag-dashboard

# Stop dashboard service
sudo systemctl stop rag-dashboard

# Restart dashboard service
sudo systemctl restart rag-dashboard

# Check service status
sudo systemctl status rag-dashboard

# View real-time logs
sudo journalctl -u rag-dashboard -f

# View recent logs
sudo journalctl -u rag-dashboard -n 100
```

## 🔍 Health Checks

```bash
# API health
curl http://localhost:8058/v1/health

# Dashboard health (Streamlit)
curl http://127.0.0.1:8501/_stcore/health

# Check dashboard service
sudo systemctl is-active rag-dashboard

# Check running processes
ps aux | grep -E "(streamlit|api_multi_tenant)"
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
Cloudflare Tunnel
    ↓
127.0.0.1:8501 (Dashboard) → localhost:8058 (API)
```

**Important**: Dashboard and API communicate via localhost. Cloudflare tunnel maps the public domain to 127.0.0.1:8501.

## 📚 Documentation

- **SYSTEMD_SERVICE.md**: Systemd service setup and management
- **RUN_DASHBOARD.md**: Basic dashboard usage
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
curl http://127.0.0.1:8501/_stcore/health

# Check dashboard service
sudo systemctl status rag-dashboard

# Check Cloudflare tunnel configuration
```

### Dashboard service won't start
```bash
# Check logs
sudo journalctl -u rag-dashboard -n 50

# Check port not in use
sudo lsof -i :8501

# Check virtual environment
ls -la /var/www/agentic-rag-knowledge-graph/venv/bin/streamlit

# Reinstall service
sudo ./scripts/install-dashboard-service.sh
```

## 🔐 Security Notes

- Dashboard runs on 127.0.0.1 (not exposed directly to internet)
- API runs on localhost:8058 (not exposed directly)
- Cloudflare tunnel provides SSL/TLS encryption
- Use strong passwords in `.env`
- Keep API keys secure
- Enable `API_KEY_REQUIRED=true` in production
- Service runs as user `jan` (not root)

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
