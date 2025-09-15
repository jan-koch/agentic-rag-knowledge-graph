#!/bin/bash

# Database Backup Script for Agentic RAG Knowledge Graph
# Creates encrypted backups of PostgreSQL database

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
BACKUP_FILE="agentic_rag_backup_$TIMESTAMP.sql"
COMPRESSED_FILE="$BACKUP_FILE.gz"
ENCRYPTED_FILE="$COMPRESSED_FILE.gpg"

# Load environment variables
if [ -f .env ]; then
    source .env
else
    print_error ".env file not found"
    exit 1
fi

echo "🗃️  Database Backup for Agentic RAG"
echo "=================================="
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if PostgreSQL container is running
if ! docker compose -f docker-compose.prod.yml ps postgres | grep -q "healthy\|running"; then
    print_error "PostgreSQL container is not running"
    exit 1
fi

print_status "Starting database backup..."

# Create database dump
if docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U raguser -d agentic_rag > "$BACKUP_DIR/$BACKUP_FILE"; then
    print_success "Database dump created: $BACKUP_FILE"
else
    print_error "Failed to create database dump"
    exit 1
fi

# Compress the backup
print_status "Compressing backup..."
if gzip "$BACKUP_DIR/$BACKUP_FILE"; then
    print_success "Backup compressed: $COMPRESSED_FILE"
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
find "$BACKUP_DIR" -name "agentic_rag_backup_*.sql.gz*" -mtime +7 -delete
REMAINING_BACKUPS=$(find "$BACKUP_DIR" -name "agentic_rag_backup_*.sql.gz*" | wc -l)

echo ""
print_success "✅ Backup completed!"
echo ""
echo "Backup Details:"
echo "==============="
echo "File: $BACKUP_DIR/$FINAL_FILE"
echo "Size: $BACKUP_SIZE"
echo "Timestamp: $TIMESTAMP"
echo "Remaining backups: $REMAINING_BACKUPS"
echo ""

if [[ "$FINAL_FILE" == *".gpg" ]]; then
    echo "Restore Command (encrypted):"
    echo "gpg --decrypt $BACKUP_DIR/$FINAL_FILE | gunzip | docker compose -f docker-compose.prod.yml exec -T postgres psql -U raguser -d agentic_rag"
else
    echo "Restore Command:"
    echo "gunzip -c $BACKUP_DIR/$FINAL_FILE | docker compose -f docker-compose.prod.yml exec -T postgres psql -U raguser -d agentic_rag"
fi
echo ""

print_status "Consider setting up automated backups with cron:"
echo "0 2 * * * /path/to/this/script/backup-database.sh >> /var/log/agentic-rag-backup.log 2>&1"