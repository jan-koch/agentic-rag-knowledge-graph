# Systemd Service Setup for Dashboard

This guide explains how to set up the Multi-Tenant RAG Dashboard to automatically start on server restart.

## Quick Install

```bash
# Install the service
sudo ./scripts/install-dashboard-service.sh
```

That's it! The dashboard will now:
- Start automatically on server boot
- Restart automatically if it crashes
- Run on 127.0.0.1:8501 (accessible via Cloudflare tunnel at bot.kobra-dataworks.de)

## Manual Installation

If you prefer to install manually:

```bash
# 1. Copy service file
sudo cp rag-dashboard.service /etc/systemd/system/

# 2. Create log file
sudo touch /var/log/rag-dashboard.log
sudo chown jan:jan /var/log/rag-dashboard.log

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Enable service (start on boot)
sudo systemctl enable rag-dashboard.service

# 5. Start the service
sudo systemctl start rag-dashboard.service

# 6. Check status
sudo systemctl status rag-dashboard.service
```

## Service Management

### Start/Stop/Restart

```bash
# Start the dashboard
sudo systemctl start rag-dashboard

# Stop the dashboard
sudo systemctl stop rag-dashboard

# Restart the dashboard
sudo systemctl restart rag-dashboard

# Check if running
sudo systemctl status rag-dashboard
```

### Enable/Disable Auto-Start

```bash
# Enable auto-start on boot (already done by install script)
sudo systemctl enable rag-dashboard

# Disable auto-start on boot
sudo systemctl disable rag-dashboard
```

### View Logs

```bash
# View logs (real-time)
sudo journalctl -u rag-dashboard -f

# View recent logs
sudo journalctl -u rag-dashboard -n 100

# View logs since last boot
sudo journalctl -u rag-dashboard -b

# View log file directly
tail -f /var/log/rag-dashboard.log
```

## Configuration

### Service File: `/etc/systemd/system/rag-dashboard.service`

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
ExecStart=/var/www/agentic-rag-knowledge-graph/venv/bin/streamlit run webui.py --server.port 8501 --server.address 127.0.0.1
Restart=always
RestartSec=10
StandardOutput=append:/var/log/rag-dashboard.log
StandardError=append:/var/log/rag-dashboard.log

[Install]
WantedBy=multi-user.target
```

### Streamlit Config: `.streamlit/config.toml`

```toml
[server]
port = 8501
address = "127.0.0.1"
headless = true

[browser]
gatherUsageStats = false
```

## Updating the Dashboard

After making changes to `webui.py`:

```bash
# 1. Restart the service to pick up changes
sudo systemctl restart rag-dashboard

# 2. Check it's running
sudo systemctl status rag-dashboard
```

If you update dependencies in `requirements.txt`:

```bash
# 1. Stop the service
sudo systemctl stop rag-dashboard

# 2. Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 3. Start the service
sudo systemctl start rag-dashboard
```

## Troubleshooting

### Service won't start

```bash
# Check logs for errors
sudo journalctl -u rag-dashboard -n 50

# Common issues:
# 1. Virtual environment not activated
#    Fix: Check ExecStart path in service file

# 2. Port already in use
#    Fix: Check what's using port 8501
lsof -i :8501

# 3. Permission issues
#    Fix: Check User/Group in service file match file owner
ls -la /var/www/agentic-rag-knowledge-graph
```

### Dashboard accessible but shows errors

```bash
# Check API is running
curl http://localhost:8058/v1/health

# If not, you may need to create a service for the API too
# See api.service.example in this directory
```

### Logs not appearing

```bash
# Check log file permissions
ls -la /var/log/rag-dashboard.log

# Fix permissions if needed
sudo chown jan:jan /var/log/rag-dashboard.log
```

### After system reboot, dashboard doesn't start

```bash
# Check if service is enabled
sudo systemctl is-enabled rag-dashboard

# Should return: enabled
# If not, enable it:
sudo systemctl enable rag-dashboard
```

## Uninstall

To remove the service:

```bash
# 1. Stop and disable
sudo systemctl stop rag-dashboard
sudo systemctl disable rag-dashboard

# 2. Remove service file
sudo rm /etc/systemd/system/rag-dashboard.service

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Optionally remove log file
sudo rm /var/log/rag-dashboard.log
```

## API Service (Optional)

If you want the API to also auto-start, create a similar service for it:

```bash
# Copy the example
cp rag-dashboard.service rag-api.service

# Edit the file to run the API instead
# Change ExecStart to:
# ExecStart=/var/www/agentic-rag-knowledge-graph/venv/bin/python -m agent.api_multi_tenant

# Install it
sudo cp rag-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rag-api.service
sudo systemctl start rag-api.service
```

## Monitoring

### Check if dashboard is running

```bash
# Via systemd
sudo systemctl is-active rag-dashboard

# Via curl
curl http://127.0.0.1:8501/_stcore/health

# Via process list
ps aux | grep streamlit
```

### Resource usage

```bash
# Check memory/CPU usage
sudo systemctl status rag-dashboard

# More detailed stats
top -p $(pgrep -f "streamlit run webui.py")
```

## Access

Once the service is running:
- **Local**: http://127.0.0.1:8501
- **Public** (via Cloudflare tunnel): https://bot.kobra-dataworks.de

The Cloudflare tunnel configuration (set up separately) maps the public domain to localhost:8501.
