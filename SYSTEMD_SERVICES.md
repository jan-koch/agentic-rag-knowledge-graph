# Systemd Services Setup

## Overview

This guide explains how to set up the RAG API and Dashboard as systemd services that start automatically on system boot.

## Services

### 1. `rag-api.service`
- **Description**: Multi-Tenant RAG API Server
- **Port**: 8058
- **Command**: `python -m agent.api`
- **Log**: `/var/log/rag-api.log`

### 2. `rag-dashboard.service`
- **Description**: Multi-Tenant RAG Admin Dashboard (Streamlit)
- **Port**: 8012 (mapped via Cloudflare tunnel to bot.kobra-dataworks.de)
- **Command**: `streamlit run webui.py`
- **Log**: `/var/log/rag-dashboard.log`

## Installation

### Quick Install

```bash
sudo ./install-services.sh
```

This script will:
1. Stop any running instances
2. Install service files to `/etc/systemd/system/`
3. Create log files
4. Reload systemd
5. Enable services (auto-start on boot)
6. Start both services

### Manual Installation

If you prefer manual installation:

```bash
# Copy service files
sudo cp rag-api.service /etc/systemd/system/
sudo cp rag-dashboard.service /etc/systemd/system/

# Set permissions
sudo chmod 644 /etc/systemd/system/rag-api.service
sudo chmod 644 /etc/systemd/system/rag-dashboard.service

# Create log files
sudo touch /var/log/rag-api.log
sudo touch /var/log/rag-dashboard.log
sudo chown jan:jan /var/log/rag-api.log
sudo chown jan:jan /var/log/rag-dashboard.log

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable rag-api
sudo systemctl enable rag-dashboard

# Start services
sudo systemctl start rag-api
sudo systemctl start rag-dashboard
```

## Service Management

### Check Status

```bash
# Check API status
sudo systemctl status rag-api

# Check Dashboard status
sudo systemctl status rag-dashboard
```

### Start/Stop/Restart

```bash
# Start
sudo systemctl start rag-api
sudo systemctl start rag-dashboard

# Stop
sudo systemctl stop rag-api
sudo systemctl stop rag-dashboard

# Restart
sudo systemctl restart rag-api
sudo systemctl restart rag-dashboard
```

### View Logs

```bash
# View API logs (real-time)
sudo journalctl -u rag-api -f

# View Dashboard logs (real-time)
sudo journalctl -u rag-dashboard -f

# View last 100 lines
sudo journalctl -u rag-api -n 100
sudo journalctl -u rag-dashboard -n 100

# View logs since today
sudo journalctl -u rag-api --since today
sudo journalctl -u rag-dashboard --since today
```

### Enable/Disable Auto-Start

```bash
# Enable auto-start on boot
sudo systemctl enable rag-api
sudo systemctl enable rag-dashboard

# Disable auto-start
sudo systemctl disable rag-api
sudo systemctl disable rag-dashboard
```

## Service Configuration

### API Service (`rag-api.service`)

```ini
[Unit]
Description=Multi-Tenant RAG API Server
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=jan
Group=jan
WorkingDirectory=/var/www/agentic-rag-knowledge-graph
Environment="PATH=/var/www/agentic-rag-knowledge-graph/venv/bin"
ExecStart=/var/www/agentic-rag-knowledge-graph/venv/bin/python -m agent.api
Restart=always
RestartSec=10
StandardOutput=append:/var/log/rag-api.log
StandardError=append:/var/log/rag-api.log

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/var/www/agentic-rag-knowledge-graph

[Install]
WantedBy=multi-user.target
```

### Dashboard Service (`rag-dashboard.service`)

```ini
[Unit]
Description=Multi-Tenant RAG Admin Dashboard (Streamlit)
After=network.target
Wants=rag-api.service

[Service]
Type=simple
User=jan
Group=jan
WorkingDirectory=/var/www/agentic-rag-knowledge-graph
Environment="PATH=/var/www/agentic-rag-knowledge-graph/venv/bin"
ExecStart=/var/www/agentic-rag-knowledge-graph/venv/bin/streamlit run webui.py --server.port 8012 --server.address 127.0.0.1
Restart=always
RestartSec=10
StandardOutput=append:/var/log/rag-dashboard.log
StandardError=append:/var/log/rag-dashboard.log

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/var/www/agentic-rag-knowledge-graph

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Services Won't Start

1. **Check logs**:
   ```bash
   sudo journalctl -u rag-api -n 50
   sudo journalctl -u rag-dashboard -n 50
   ```

2. **Check file permissions**:
   ```bash
   ls -la /etc/systemd/system/rag-*.service
   ```

3. **Test manually**:
   ```bash
   cd /var/www/agentic-rag-knowledge-graph
   source venv/bin/activate
   python -m agent.api  # Test API
   streamlit run webui.py --server.port 8012  # Test Dashboard
   ```

### Port Already in Use

Check what's using the port:
```bash
sudo netstat -tulnp | grep 8058  # API
sudo netstat -tulnp | grep 8012  # Dashboard
```

Kill the process if needed:
```bash
sudo kill <PID>
```

### Database Connection Issues

Ensure PostgreSQL and Neo4j are running:
```bash
docker compose ps
docker compose up -d  # If not running
```

### Service Fails After Code Changes

After updating code:
```bash
sudo systemctl restart rag-api
sudo systemctl restart rag-dashboard
```

### Check Service Dependencies

```bash
systemctl list-dependencies rag-api
systemctl list-dependencies rag-dashboard
```

## Updating Services

If you modify the service files:

```bash
# After editing rag-api.service or rag-dashboard.service
sudo cp rag-api.service /etc/systemd/system/
sudo cp rag-dashboard.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Restart services
sudo systemctl restart rag-api
sudo systemctl restart rag-dashboard
```

## Uninstallation

To remove the services:

```bash
# Stop services
sudo systemctl stop rag-api rag-dashboard

# Disable auto-start
sudo systemctl disable rag-api rag-dashboard

# Remove service files
sudo rm /etc/systemd/system/rag-api.service
sudo rm /etc/systemd/system/rag-dashboard.service

# Reload systemd
sudo systemctl daemon-reload

# Optional: Remove logs
sudo rm /var/log/rag-api.log
sudo rm /var/log/rag-dashboard.log
```

## Security Features

Both services include security hardening:
- **NoNewPrivileges**: Prevents privilege escalation
- **PrivateTmp**: Isolated /tmp directory
- **ProtectSystem**: Read-only system directories
- **ProtectHome**: Read-only home directories
- **ReadWritePaths**: Only project directory is writable

## Auto-Restart

Both services are configured with:
- `Restart=always`: Automatically restart on failure
- `RestartSec=10`: Wait 10 seconds before restarting

This ensures high availability even if the services crash.

## Monitoring

### Check if services are running

```bash
systemctl is-active rag-api
systemctl is-active rag-dashboard
```

### Check if services are enabled

```bash
systemctl is-enabled rag-api
systemctl is-enabled rag-dashboard
```

### View resource usage

```bash
systemctl status rag-api
systemctl status rag-dashboard
```

## Related Documentation

- `CLAUDE.md` - General system documentation
- `MULTI_TENANT_README.md` - Multi-tenant architecture
- `STREAMLIT_INGESTION_GUIDE.md` - Document ingestion via Streamlit
- `PRODUCTION_DEPLOYMENT.md` - Production deployment guide

---

**Last Updated**: 2025-01-09
**Status**: Production Ready
