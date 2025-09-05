#!/bin/bash

# Cloudflare Tunnel Setup Script for Agentic RAG API
# This script helps set up a secure Cloudflare tunnel to expose only n8n endpoints

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. Consider creating a dedicated user for cloudflared."
fi

# Configuration
TUNNEL_NAME="agentic-rag-tunnel"
DOMAIN=""
CLOUDFLARED_DIR="/etc/cloudflared"
CONFIG_FILE="$CLOUDFLARED_DIR/config.yml"

echo "🌐 Cloudflare Tunnel Setup for Agentic RAG API"
echo "=============================================="
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    print_error "cloudflared is not installed. Please install it first:"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb"
    echo "  sudo dpkg -i cloudflared.deb"
    echo ""
    echo "CentOS/RHEL/Fedora:"
    echo "  sudo yum install cloudflared"
    echo ""
    echo "macOS:"
    echo "  brew install cloudflared"
    echo ""
    exit 1
fi

print_success "cloudflared is installed"

# Get domain from user
while [ -z "$DOMAIN" ]; do
    read -p "Enter your domain name (e.g., rag-api.yourdomain.com): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        print_error "Domain name is required"
    fi
done

print_status "Using domain: $DOMAIN"

# Check if user is logged in to Cloudflare
if ! cloudflared tunnel list &> /dev/null; then
    print_status "You need to authenticate with Cloudflare first"
    echo "Run: cloudflared tunnel login"
    echo "This will open a browser to authenticate with your Cloudflare account"
    exit 1
fi

print_success "Cloudflare authentication verified"

# Create tunnel if it doesn't exist
if ! cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    print_status "Creating new tunnel: $TUNNEL_NAME"
    cloudflared tunnel create "$TUNNEL_NAME"
    print_success "Tunnel created"
else
    print_warning "Tunnel $TUNNEL_NAME already exists"
fi

# Get tunnel UUID
TUNNEL_UUID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
print_status "Tunnel UUID: $TUNNEL_UUID"

# Create cloudflared directory
if [ ! -d "$CLOUDFLARED_DIR" ]; then
    print_status "Creating $CLOUDFLARED_DIR directory"
    sudo mkdir -p "$CLOUDFLARED_DIR"
fi

# Generate configuration file
print_status "Generating tunnel configuration"
sudo tee "$CONFIG_FILE" > /dev/null <<EOF
# Cloudflare Tunnel Configuration for Agentic RAG API
# Generated on $(date)

tunnel: $TUNNEL_UUID
credentials-file: $CLOUDFLARED_DIR/$TUNNEL_UUID.json

# Ingress rules - ONLY expose n8n endpoints for security
ingress:
  # n8n integration endpoints
  - hostname: $DOMAIN
    path: /n8n/*
    service: http://127.0.0.1:8058
    originRequest:
      httpHostHeader: $DOMAIN
      connectTimeout: 30s
      tlsTimeout: 10s
      tcpKeepAlive: 30s
      keepAliveConnections: 10
      keepAliveTimeout: 90s

  # Health check endpoint (for monitoring)
  - hostname: $DOMAIN
    path: /health
    service: http://127.0.0.1:8058
    originRequest:
      httpHostHeader: $DOMAIN

  # Block all other endpoints for security
  - service: http_status:404

# Security and performance settings
warp-routing:
  enabled: false

logLevel: info
retries: 3
grace-period: 30s
EOF

print_success "Configuration file created at $CONFIG_FILE"

# Copy credentials file if it exists in home directory
CREDS_FILE="$HOME/.cloudflared/$TUNNEL_UUID.json"
if [ -f "$CREDS_FILE" ]; then
    print_status "Copying credentials file"
    sudo cp "$CREDS_FILE" "$CLOUDFLARED_DIR/$TUNNEL_UUID.json"
    sudo chmod 600 "$CLOUDFLARED_DIR/$TUNNEL_UUID.json"
    print_success "Credentials file copied"
else
    print_warning "Credentials file not found at $CREDS_FILE"
    print_warning "You may need to manually copy the credentials file to $CLOUDFLARED_DIR/$TUNNEL_UUID.json"
fi

# Create DNS record
print_status "Creating DNS record for $DOMAIN"
if cloudflared tunnel route dns "$TUNNEL_NAME" "$DOMAIN"; then
    print_success "DNS record created"
else
    print_warning "DNS record creation failed or already exists"
fi

# Validate configuration
print_status "Validating tunnel configuration"
if sudo cloudflared tunnel --config "$CONFIG_FILE" ingress validate; then
    print_success "Configuration is valid"
else
    print_error "Configuration validation failed"
    exit 1
fi

# Create systemd service
SERVICE_FILE="/etc/systemd/system/cloudflared-$TUNNEL_NAME.service"
print_status "Creating systemd service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Cloudflare Tunnel for Agentic RAG API
After=network.target
Wants=network.target

[Service]
Type=simple
User=cloudflared
Group=cloudflared
ExecStart=/usr/bin/cloudflared tunnel --config $CONFIG_FILE run
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$CLOUDFLARED_DIR
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

# Create cloudflared user if it doesn't exist
if ! id "cloudflared" &>/dev/null; then
    print_status "Creating cloudflared user"
    sudo useradd -r -s /bin/false cloudflared
fi

# Set proper permissions
sudo chown -R cloudflared:cloudflared "$CLOUDFLARED_DIR"
sudo chmod 700 "$CLOUDFLARED_DIR"

print_success "Systemd service created"

# Enable and start service
print_status "Enabling and starting cloudflared service"
sudo systemctl daemon-reload
sudo systemctl enable "cloudflared-$TUNNEL_NAME.service"
sudo systemctl start "cloudflared-$TUNNEL_NAME.service"

# Check service status
if sudo systemctl is-active --quiet "cloudflared-$TUNNEL_NAME.service"; then
    print_success "Cloudflared service is running"
else
    print_error "Failed to start cloudflared service"
    print_status "Check logs with: sudo journalctl -u cloudflared-$TUNNEL_NAME.service -f"
    exit 1
fi

echo ""
print_success "🎉 Cloudflare tunnel setup complete!"
echo ""
echo "Configuration Summary:"
echo "====================="
echo "Tunnel Name: $TUNNEL_NAME"
echo "Tunnel UUID: $TUNNEL_UUID"
echo "Domain: $DOMAIN"
echo "Configuration: $CONFIG_FILE"
echo ""
echo "Exposed Endpoints:"
echo "- https://$DOMAIN/n8n/chat (main n8n integration)"
echo "- https://$DOMAIN/n8n/simple (simple n8n integration)"
echo "- https://$DOMAIN/health (health check)"
echo ""
echo "Service Management:"
echo "- Status: sudo systemctl status cloudflared-$TUNNEL_NAME"
echo "- Logs: sudo journalctl -u cloudflared-$TUNNEL_NAME -f"
echo "- Restart: sudo systemctl restart cloudflared-$TUNNEL_NAME"
echo "- Stop: sudo systemctl stop cloudflared-$TUNNEL_NAME"
echo ""
echo "Security Notes:"
echo "- Only n8n and health endpoints are exposed"
echo "- All other endpoints return 404"
echo "- Make sure to set N8N_API_KEY in your .env file"
echo "- Consider enabling IP whitelisting in production"
echo ""
print_warning "Test the tunnel: curl https://$DOMAIN/health"