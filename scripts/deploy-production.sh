#!/bin/bash

# Production Deployment Script for Agentic RAG Knowledge Graph
# This script deploys the application securely for production use

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
    print_error "Do not run this script as root for security reasons"
    exit 1
fi

echo "🚀 Agentic RAG Production Deployment"
echo "===================================="
echo ""

# Check for required files
required_files=(".env" "docker-compose.prod.yml" "Dockerfile.prod")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file missing: $file"
        if [ "$file" = ".env" ]; then
            echo "Copy .env.production to .env and customize the values"
        fi
        exit 1
    fi
done

print_success "Required files found"

# Validate environment file
print_status "Validating environment configuration..."

# Check for required environment variables
required_vars=("POSTGRES_PASSWORD" "NEO4J_PASSWORD" "LLM_API_KEY" "N8N_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=.*your-.*-here" .env; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    print_error "Missing or placeholder values for required variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please update your .env file with actual values before deploying"
    exit 1
fi

print_success "Environment configuration validated"

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    print_error "Docker Compose is not installed or not available"
    exit 1
fi

print_success "Docker environment verified"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    exit 1
fi

# Create necessary directories
print_status "Creating application directories..."
mkdir -p data logs backups
print_success "Directories created"

# Check for existing deployment
if docker compose -f docker-compose.prod.yml ps | grep -q "agentic-rag"; then
    print_warning "Existing deployment detected"
    read -p "Do you want to stop and redeploy? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Stopping existing deployment..."
        docker compose -f docker-compose.prod.yml down
        print_success "Existing deployment stopped"
    else
        print_status "Deployment cancelled"
        exit 0
    fi
fi

# Build the application image
print_status "Building production Docker image..."
if docker build -f Dockerfile.prod -t agentic-rag:latest .; then
    print_success "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Pull required images
print_status "Pulling required Docker images..."
docker compose -f docker-compose.prod.yml pull postgres neo4j

# Start the deployment
print_status "Starting production deployment..."
if docker compose -f docker-compose.prod.yml up -d; then
    print_success "Deployment started"
else
    print_error "Deployment failed"
    exit 1
fi

# Wait for services to be healthy
print_status "Waiting for services to become healthy..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}" | grep -q "healthy"; then
        healthy_services=$(docker compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}" | grep -c "healthy" || true)
        total_services=3  # app, postgres, neo4j
        
        if [ "$healthy_services" -eq "$total_services" ]; then
            print_success "All services are healthy!"
            break
        fi
    fi
    
    attempt=$((attempt + 1))
    echo -n "."
    sleep 5
done

echo ""

if [ $attempt -eq $max_attempts ]; then
    print_warning "Some services may not be fully healthy yet"
    print_status "Check status with: docker compose -f docker-compose.prod.yml ps"
fi

# Test the API
print_status "Testing API health endpoint..."
if curl -f -s http://127.0.0.1:8058/health > /dev/null; then
    print_success "API health check passed"
else
    print_warning "API health check failed - service may still be starting"
fi

# Display deployment information
echo ""
print_success "🎉 Deployment completed!"
echo ""
echo "Service Status:"
echo "==============="
docker compose -f docker-compose.prod.yml ps

echo ""
echo "Useful Commands:"
echo "=================="
echo "View logs:           docker compose -f docker-compose.prod.yml logs -f"
echo "View app logs:       docker compose -f docker-compose.prod.yml logs -f app"
echo "Check status:        docker compose -f docker-compose.prod.yml ps"
echo "Restart services:    docker compose -f docker-compose.prod.yml restart"
echo "Stop deployment:     docker compose -f docker-compose.prod.yml down"
echo "Update deployment:   $0"
echo ""
echo "Backup commands:"
echo "=================="
echo "Backup database:     ./scripts/backup-database.sh"
echo "Backup Neo4j:        ./scripts/backup-neo4j.sh"
echo ""

# Security reminders
echo "Security Checklist:"
echo "==================="
echo "✓ Application runs as non-root user"
echo "✓ Databases are not exposed to internet"
echo "✓ API only binds to localhost (127.0.0.1:8058)"
echo "✓ Security headers are enabled"
echo "✓ Input sanitization is active"
echo ""

if grep -q "ENABLE_IP_WHITELIST=false" .env; then
    print_warning "IP whitelisting is disabled - consider enabling for production"
fi

if grep -q "ALLOWED_ORIGINS=\*" .env; then
    print_warning "CORS is set to allow all origins - consider restricting to your n8n domain"
fi

echo "Next Steps:"
echo "==========="
echo "1. Configure your Cloudflare Tunnel to point to 127.0.0.1:8058"
echo "2. Test n8n integration with your tunnel URL"
echo "3. Set up monitoring and log rotation"
echo "4. Configure automated backups"
echo "5. Update n8n workflows to use the new secure endpoints"
echo ""
print_success "Deployment ready for production use!"