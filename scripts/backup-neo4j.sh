#!/bin/bash

# Neo4j Backup Script for Agentic RAG Knowledge Graph
# Creates backups of Neo4j graph database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
NEO4J_BACKUP_DIR="neo4j_backup_$TIMESTAMP"
COMPRESSED_FILE="$NEO4J_BACKUP_DIR.tar.gz"
ENCRYPTED_FILE="$COMPRESSED_FILE.gpg"

# Load environment variables
if [ -f .env ]; then
    source .env
else
    print_error ".env file not found"
    exit 1
fi

echo "📊 Neo4j Backup for Agentic RAG"
echo "==============================="
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if Neo4j container is running
if ! docker compose -f docker-compose.prod.yml ps neo4j | grep -q "healthy\|running"; then
    print_error "Neo4j container is not running"
    exit 1
fi

print_status "Creating Neo4j backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR/$NEO4J_BACKUP_DIR"

# Method 1: Export using cypher-shell (works for community edition)
print_status "Exporting graph data using cypher-shell..."

# Export nodes
if docker compose -f docker-compose.prod.yml exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "CALL apoc.export.cypher.all('/tmp/nodes_export.cypher', {format: 'cypher-shell'})" > /dev/null 2>&1; then
    # Copy exported file from container
    docker compose -f docker-compose.prod.yml exec -T neo4j cat /tmp/nodes_export.cypher > "$BACKUP_DIR/$NEO4J_BACKUP_DIR/graph_export.cypher"
    print_success "Graph data exported"
else
    print_warning "Failed to export using apoc.export, trying alternative method..."
    
    # Alternative: Manual export of nodes and relationships
    docker compose -f docker-compose.prod.yml exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "MATCH (n) RETURN n" > "$BACKUP_DIR/$NEO4J_BACKUP_DIR/nodes.txt" 2>/dev/null || true
    docker compose -f docker-compose.prod.yml exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "MATCH ()-[r]->() RETURN r" > "$BACKUP_DIR/$NEO4J_BACKUP_DIR/relationships.txt" 2>/dev/null || true
    print_success "Basic graph data exported"
fi

# Export database statistics
print_status "Exporting database statistics..."
docker compose -f docker-compose.prod.yml exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "CALL db.stats.retrieve('GRAPH COUNTS')" > "$BACKUP_DIR/$NEO4J_BACKUP_DIR/stats.txt" 2>/dev/null || true

# Export schema information
docker compose -f docker-compose.prod.yml exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "CALL db.labels()" > "$BACKUP_DIR/$NEO4J_BACKUP_DIR/labels.txt" 2>/dev/null || true
docker compose -f docker-compose.prod.yml exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "CALL db.relationshipTypes()" > "$BACKUP_DIR/$NEO4J_BACKUP_DIR/relationships_types.txt" 2>/dev/null || true

# Create metadata file
cat > "$BACKUP_DIR/$NEO4J_BACKUP_DIR/backup_info.txt" << EOF
Neo4j Backup Information
========================
Backup Date: $(date)
Backup Method: cypher-shell export
Neo4j Version: $(docker compose -f docker-compose.prod.yml exec -T neo4j neo4j version 2>/dev/null || echo "Unknown")
Database: agentic_rag knowledge graph
EOF

print_success "Metadata exported"

# Compress the backup
print_status "Compressing Neo4j backup..."
if tar -czf "$BACKUP_DIR/$COMPRESSED_FILE" -C "$BACKUP_DIR" "$NEO4J_BACKUP_DIR"; then
    print_success "Backup compressed: $COMPRESSED_FILE"
    # Remove uncompressed directory
    rm -rf "$BACKUP_DIR/$NEO4J_BACKUP_DIR"
else
    print_error "Failed to compress backup"
    exit 1
fi

# Encrypt the backup (optional but recommended)
if command -v gpg &> /dev/null; then
    read -p "Enter encryption passphrase (or press Enter to skip): " -s PASSPHRASE
    echo ""
    
    if [ -n "$PASSPHRASE" ]; then
        print_status "Encrypting backup..."
        if echo "$PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 --symmetric --cipher-algo AES256 --compress-algo 1 --output "$BACKUP_DIR/$ENCRYPTED_FILE" "$BACKUP_DIR/$COMPRESSED_FILE"; then
            print_success "Backup encrypted: $ENCRYPTED_FILE"
            # Remove unencrypted version
            rm "$BACKUP_DIR/$COMPRESSED_FILE"
            FINAL_FILE="$ENCRYPTED_FILE"
        else
            print_error "Failed to encrypt backup"
            FINAL_FILE="$COMPRESSED_FILE"
        fi
    else
        print_warning "Backup not encrypted"
        FINAL_FILE="$COMPRESSED_FILE"
    fi
else
    print_warning "GPG not available - backup not encrypted"
    FINAL_FILE="$COMPRESSED_FILE"
fi

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$FINAL_FILE" | cut -f1)

# Cleanup old backups (keep last 7 days)
print_status "Cleaning up old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -name "neo4j_backup_*.tar.gz*" -mtime +7 -delete
REMAINING_BACKUPS=$(find "$BACKUP_DIR" -name "neo4j_backup_*.tar.gz*" | wc -l)

echo ""
print_success "✅ Neo4j backup completed!"
echo ""
echo "Backup Details:"
echo "==============="
echo "File: $BACKUP_DIR/$FINAL_FILE"
echo "Size: $BACKUP_SIZE"
echo "Timestamp: $TIMESTAMP"
echo "Remaining backups: $REMAINING_BACKUPS"
echo ""

if [[ "$FINAL_FILE" == *".gpg" ]]; then
    echo "Restore Instructions (encrypted):"
    echo "1. Decrypt and extract: gpg --decrypt $BACKUP_DIR/$FINAL_FILE | tar -xz -C $BACKUP_DIR"
    echo "2. Copy cypher file to Neo4j container and import"
else
    echo "Restore Instructions:"
    echo "1. Extract: tar -xzf $BACKUP_DIR/$FINAL_FILE -C $BACKUP_DIR"
    echo "2. Copy cypher file to Neo4j container and import"
fi

echo ""
print_warning "Note: Neo4j Community Edition has limited backup options."
print_warning "For production, consider Neo4j Enterprise with proper backup tools."
echo ""

print_status "Consider setting up automated backups with cron:"
echo "15 2 * * * /path/to/this/script/backup-neo4j.sh >> /var/log/agentic-rag-backup.log 2>&1"