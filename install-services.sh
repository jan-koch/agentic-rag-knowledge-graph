#!/bin/bash
# Installation script for RAG API and Dashboard systemd services

set -e

echo "======================================"
echo "RAG Services Installation"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "1. Stopping any running instances..."
# Kill existing processes
pkill -f "python -m agent.api" || true
pkill -f "streamlit run webui.py" || true
sleep 2

echo "2. Installing service files..."
# Copy service files
cp "$SCRIPT_DIR/rag-api.service" /etc/systemd/system/
cp "$SCRIPT_DIR/rag-dashboard.service" /etc/systemd/system/

echo "3. Setting correct permissions..."
chmod 644 /etc/systemd/system/rag-api.service
chmod 644 /etc/systemd/system/rag-dashboard.service

echo "4. Creating log files..."
touch /var/log/rag-api.log
touch /var/log/rag-dashboard.log
chown jan:jan /var/log/rag-api.log
chown jan:jan /var/log/rag-dashboard.log

echo "5. Reloading systemd..."
systemctl daemon-reload

echo "6. Enabling services..."
systemctl enable rag-api.service
systemctl enable rag-dashboard.service

echo "7. Starting services..."
systemctl start rag-api.service
sleep 3
systemctl start rag-dashboard.service
sleep 3

echo ""
echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo ""

echo "Service Status:"
systemctl status rag-api.service --no-pager -l
echo ""
systemctl status rag-dashboard.service --no-pager -l
echo ""

echo "Useful commands:"
echo "  sudo systemctl status rag-api        # Check API status"
echo "  sudo systemctl status rag-dashboard  # Check dashboard status"
echo "  sudo systemctl restart rag-api       # Restart API"
echo "  sudo systemctl restart rag-dashboard # Restart dashboard"
echo "  sudo journalctl -u rag-api -f        # View API logs"
echo "  sudo journalctl -u rag-dashboard -f  # View dashboard logs"
echo ""
echo "Services will now start automatically on system boot!"
