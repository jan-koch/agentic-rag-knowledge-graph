#!/bin/bash

# Install Multi-Tenant RAG Dashboard as systemd service
# This script installs the dashboard to auto-start on server restart

set -e

echo "Installing RAG Dashboard systemd service..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo ./scripts/install-dashboard-service.sh"
    exit 1
fi

# Copy service file to systemd directory
cp rag-dashboard.service /etc/systemd/system/

# Create log file with proper permissions
touch /var/log/rag-dashboard.log
chown jan:jan /var/log/rag-dashboard.log

# Reload systemd daemon
systemctl daemon-reload

# Enable service to start on boot
systemctl enable rag-dashboard.service

# Start the service
systemctl start rag-dashboard.service

# Show status
systemctl status rag-dashboard.service

echo ""
echo "✅ Dashboard service installed successfully!"
echo ""
echo "Service commands:"
echo "  sudo systemctl start rag-dashboard    # Start the dashboard"
echo "  sudo systemctl stop rag-dashboard     # Stop the dashboard"
echo "  sudo systemctl restart rag-dashboard  # Restart the dashboard"
echo "  sudo systemctl status rag-dashboard   # Check status"
echo "  sudo journalctl -u rag-dashboard -f   # View logs"
echo ""
echo "Dashboard running at: http://127.0.0.1:8501"
echo "Mapped to: https://bot.kobra-dataworks.de (via Cloudflare tunnel)"
