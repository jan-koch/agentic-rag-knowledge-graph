#!/bin/bash

# Riddly Chat Service Manager
# Manages the Riddly AI Chat Streamlit service

SERVICE_NAME="riddly-chat"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOCAL_SERVICE_FILE="$(dirname "$0")/${SERVICE_NAME}.service"
APP_DIR="/var/www/agentic-rag-knowledge-graph/frontend/streamlit"
VENV_DIR="/var/www/agentic-rag-knowledge-graph/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}🚀 Riddly Chat Service Manager${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_dependencies() {
    echo "📋 Checking dependencies..."
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found at $VENV_DIR"
        echo "Please create virtual environment first:"
        echo "  cd /var/www/agentic-rag-knowledge-graph"
        echo "  python3 -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
    
    # Check if streamlit is installed
    if [ ! -f "$VENV_DIR/bin/streamlit" ]; then
        print_error "Streamlit not found in virtual environment"
        echo "Please install dependencies:"
        echo "  source $VENV_DIR/bin/activate"
        echo "  pip install streamlit requests"
        exit 1
    fi
    
    # Check if app.py exists
    if [ ! -f "$APP_DIR/app.py" ]; then
        print_error "app.py not found at $APP_DIR"
        exit 1
    fi
    
    print_status "All dependencies found"
}

setup_permissions() {
    echo "🔐 Setting up permissions..."
    
    # Create www-data user if it doesn't exist
    if ! id "www-data" &>/dev/null; then
        useradd -r -s /bin/false www-data
        print_status "Created www-data user"
    fi
    
    # Set ownership and permissions
    chown -R www-data:www-data /var/www/agentic-rag-knowledge-graph
    chmod -R 755 /var/www/agentic-rag-knowledge-graph
    chmod +x "$APP_DIR/app.py"
    
    print_status "Permissions configured"
}

install_service() {
    echo "📦 Installing service..."
    
    # Copy service file
    if [ -f "$LOCAL_SERVICE_FILE" ]; then
        cp "$LOCAL_SERVICE_FILE" "$SERVICE_FILE"
        print_status "Service file copied to $SERVICE_FILE"
    else
        print_error "Service file not found: $LOCAL_SERVICE_FILE"
        exit 1
    fi
    
    # Reload systemd
    systemctl daemon-reload
    print_status "Systemd daemon reloaded"
    
    # Enable service
    systemctl enable "$SERVICE_NAME"
    print_status "Service enabled for auto-start"
}

uninstall_service() {
    echo "🗑️ Uninstalling service..."
    
    # Stop service if running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        print_status "Service stopped"
    fi
    
    # Disable service
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        systemctl disable "$SERVICE_NAME"
        print_status "Service disabled"
    fi
    
    # Remove service file
    if [ -f "$SERVICE_FILE" ]; then
        rm "$SERVICE_FILE"
        print_status "Service file removed"
    fi
    
    # Reload systemd
    systemctl daemon-reload
    print_status "Systemd daemon reloaded"
}

start_service() {
    echo "▶️ Starting service..."
    systemctl start "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service started successfully"
        show_status
    else
        print_error "Failed to start service"
        echo "Check logs with: journalctl -u $SERVICE_NAME -f"
        exit 1
    fi
}

stop_service() {
    echo "⏹️ Stopping service..."
    systemctl stop "$SERVICE_NAME"
    
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service stopped successfully"
    else
        print_error "Failed to stop service"
        exit 1
    fi
}

restart_service() {
    echo "🔄 Restarting service..."
    systemctl restart "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service restarted successfully"
        show_status
    else
        print_error "Failed to restart service"
        echo "Check logs with: journalctl -u $SERVICE_NAME -f"
        exit 1
    fi
}

show_status() {
    echo "📊 Service Status:"
    echo "=================="
    
    # Service status
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Status: RUNNING"
    else
        print_error "Status: STOPPED"
    fi
    
    # Auto-start status
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        print_status "Auto-start: ENABLED"
    else
        print_warning "Auto-start: DISABLED"
    fi
    
    echo
    echo "📱 Application Access:"
    echo "  Local:  http://localhost:8501"
    echo "  (Service now runs on localhost only for security)"
    echo
    echo "📋 Useful Commands:"
    echo "  View logs:     journalctl -u $SERVICE_NAME -f"
    echo "  Service info:  systemctl status $SERVICE_NAME"
    echo "  Stop service:  sudo $0 stop"
    echo "  Start service: sudo $0 start"
}

show_logs() {
    echo "📋 Service Logs (last 50 lines):"
    echo "================================"
    journalctl -u "$SERVICE_NAME" -n 50 --no-pager
    echo
    echo "To follow logs in real-time: journalctl -u $SERVICE_NAME -f"
}

show_help() {
    echo "Usage: $0 {install|uninstall|start|stop|restart|status|logs|help}"
    echo
    echo "Commands:"
    echo "  install     - Install and enable the service"
    echo "  uninstall   - Stop, disable and remove the service"
    echo "  start       - Start the service"
    echo "  stop        - Stop the service"
    echo "  restart     - Restart the service"
    echo "  status      - Show service status and access info"
    echo "  logs        - Show service logs"
    echo "  help        - Show this help message"
    echo
    echo "Examples:"
    echo "  sudo $0 install    # Install service"
    echo "  sudo $0 start      # Start service"
    echo "  $0 status          # Check status (no sudo needed)"
    echo "  $0 logs            # View logs (no sudo needed)"
}

# Main script logic
case "$1" in
    install)
        print_header
        check_root
        check_dependencies
        setup_permissions
        install_service
        echo
        print_status "Service installed successfully!"
        echo
        echo "Next steps:"
        echo "1. Start the service: sudo $0 start"
        echo "2. Check status: $0 status"
        echo "3. View logs: $0 logs"
        ;;
    uninstall)
        print_header
        check_root
        uninstall_service
        echo
        print_status "Service uninstalled successfully!"
        ;;
    start)
        print_header
        check_root
        start_service
        ;;
    stop)
        print_header
        check_root
        stop_service
        ;;
    restart)
        print_header
        check_root
        restart_service
        ;;
    status)
        print_header
        show_status
        ;;
    logs)
        print_header
        show_logs
        ;;
    help|--help|-h)
        print_header
        show_help
        ;;
    *)
        print_header
        print_error "Invalid command: $1"
        echo
        show_help
        exit 1
        ;;
esac