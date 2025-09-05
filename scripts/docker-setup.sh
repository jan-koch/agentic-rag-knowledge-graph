#!/bin/bash

# Docker Setup Script for Agentic RAG with Knowledge Graph
# This script sets up PostgreSQL and Neo4j containers for development

set -e

echo "🚀 Setting up Docker containers for Agentic RAG system..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_status "Docker is running ✓"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please ensure you're in the project root directory."
    exit 1
fi

print_status "Found docker-compose.yml ✓"

# Stop any existing containers
print_status "Stopping existing containers..."
docker compose down --remove-orphans || true

# Pull latest images
print_status "Pulling Docker images..."
docker compose pull

# Start containers
print_status "Starting containers..."
docker compose up -d

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker compose exec postgres pg_isready -U postgres -d agentic_rag > /dev/null 2>&1; then
        print_success "PostgreSQL is ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_error "PostgreSQL failed to start within expected time"
    docker compose logs postgres
    exit 1
fi

# Wait for Neo4j to be ready
print_status "Waiting for Neo4j to be ready..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker compose exec neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; then
        print_success "Neo4j is ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_error "Neo4j failed to start within expected time"
    docker compose logs neo4j
    exit 1
fi

# Verify database connections
print_status "Verifying database connections..."

# Test PostgreSQL connection
if docker compose exec postgres psql -U postgres -d agentic_rag -c "SELECT 1;" > /dev/null 2>&1; then
    print_success "PostgreSQL connection verified ✓"
else
    print_error "Failed to connect to PostgreSQL"
    exit 1
fi

# Test Neo4j connection
if docker compose exec neo4j cypher-shell -u neo4j -p password "MATCH () RETURN count(*) as node_count;" > /dev/null 2>&1; then
    print_success "Neo4j connection verified ✓"
else
    print_error "Failed to connect to Neo4j"
    exit 1
fi

# Check if extensions are installed in PostgreSQL
print_status "Checking PostgreSQL extensions..."
extensions_check=$(docker compose exec postgres psql -U postgres -d agentic_rag -t -c "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
if echo "$extensions_check" | grep -q "t"; then
    print_success "pgvector extension is installed ✓"
else
    print_warning "pgvector extension not found - this may be normal on first run"
fi

# Display connection information
echo ""
print_success "🎉 Docker setup complete!"
echo ""
echo "Database Connection Information:"
echo "================================"
echo "PostgreSQL:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: agentic_rag"
echo "  Username: postgres"
echo "  Password: postgres"
echo "  URL: postgresql://postgres:postgres@localhost:5432/agentic_rag"
echo ""
echo "Neo4j:"
echo "  Bolt URI: bolt://localhost:7687"
echo "  HTTP URI: http://localhost:7474"
echo "  Username: neo4j"
echo "  Password: password"
echo ""
echo "Next steps:"
echo "1. Update your .env file with the database URLs (already done if using provided .env)"
echo "2. Run document ingestion: python -m ingestion.ingest"
echo "3. Start the API server: python -m agent.api"
echo ""
echo "Container management:"
echo "  View logs: docker compose logs -f"
echo "  Stop containers: docker compose down"
echo "  Restart containers: docker compose restart"
echo ""