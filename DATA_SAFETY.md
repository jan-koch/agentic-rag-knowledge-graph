# Data Safety & Persistence Guide

## ✅ Current Safety Status

**Last Updated:** October 7, 2025
**Data Status:** SAFE & PERSISTENT
**Container Uptime:** 7+ days (stable)
**Volume Status:** Properly configured, created Sept 30, 2025

---

## 🔒 Safety Measures Implemented

### 1. Removed Dangerous Cron Job
- ❌ **Removed:** `0 3 * * * recreate-database.sh` (would delete data nightly)
- ✅ **Status:** No automated deletion jobs exist
- 📁 **Backup:** `/tmp/crontab_backup.txt`

### 2. Disabled init.sql Script
- ❌ **File:** `docker/postgres/init.sql.BACKUP_DANGEROUS` (renamed)
- ❌ **Mount:** Removed from docker-compose.yml
- ⚠️ **Why:** Contains `DROP TABLE` statements that would delete all data

### 3. Persistent Volumes Configured
```yaml
volumes:
  postgres_data:  # Survives container restarts
  neo4j_data:     # Survives container restarts
```

### 4. Safe Restart Policy
```yaml
restart: unless-stopped  # Containers auto-restart but preserve data
```

---

## ⚠️ Commands That DESTROY Data

### NEVER RUN THESE:

```bash
# ❌ DESTROYS ALL DATA
docker compose down -v

# ❌ DESTROYS ALL DATA
docker volume rm agentic-rag-knowledge-graph_postgres_data

# ❌ DESTROYS ALL DATA (if container recreated with empty volume)
docker volume rm agentic-rag-knowledge-graph_postgres_data && docker compose up -d

# ❌ DESTROYS ALL DATA
docker exec agentic-rag-postgres psql -U postgres -d agentic_rag -c "DROP TABLE documents CASCADE;"
```

---

## ✅ Safe Commands

### Restart Containers (Data Preserved)
```bash
# Safe: Just restart
docker compose restart

# Safe: Stop and start
docker compose down
docker compose up -d

# Safe: Restart single container
docker restart agentic-rag-postgres
```

### Update Container Images (Data Preserved)
```bash
# Pull new images
docker compose pull

# Recreate containers (volumes persist)
docker compose down
docker compose up -d
```

### Run Migrations Safely
```bash
# Always use the safe migration script
./scripts/safe-schema-migration.sh migrations/your-migration.sql

# This script:
# - Creates automatic backup
# - Checks for dangerous commands
# - Allows rollback if something fails
```

---

## 🛡️ Data Protection Checklist

### Before Any Maintenance:
- [ ] Create backup: `./scripts/backup-database.sh`
- [ ] Verify backup exists: `ls -lh /var/backups/agentic-rag/`
- [ ] Check disk space: `df -h /var/lib/docker/volumes/`
- [ ] Verify no destructive flags: NO `-v` flag with `docker compose down`

### Daily Checks:
- [ ] Verify containers are running: `docker ps | grep agentic-rag`
- [ ] Check data exists: `docker exec agentic-rag-postgres psql -U postgres -d agentic_rag -c "SELECT COUNT(*) FROM documents;"`

### Weekly Checks:
- [ ] Verify backups are recent: `ls -lht /var/backups/agentic-rag/ | head -5`
- [ ] Check volume size: `docker system df -v | grep postgres_data`
- [ ] Review logs for errors: `docker logs agentic-rag-postgres --tail 100`

---

## 📦 Backup Strategy

### Automated Backups
Setup daily backups with cron:
```bash
# Add to crontab (safe, creates backups only)
crontab -e

# Add this line for 3 AM daily backups:
0 3 * * * /var/www/agentic-rag-knowledge-graph/scripts/backup-database.sh
```

### Manual Backup
```bash
# PostgreSQL
./scripts/backup-database.sh

# Neo4j
./scripts/backup-neo4j.sh

# Both
./scripts/backup-database.sh && ./scripts/backup-neo4j.sh
```

### Restore from Backup
```bash
# Find latest backup
ls -lht /var/backups/agentic-rag/ | head -5

# Restore PostgreSQL
docker exec -i agentic-rag-postgres psql -U postgres -d agentic_rag < /var/backups/agentic-rag/backup-YYYYMMDD.sql

# Restore Neo4j
docker exec agentic-rag-neo4j neo4j-admin database load neo4j --from-path=/backups/
```

---

## 🔍 How to Verify Data Persistence

### Check Volume Exists
```bash
docker volume inspect agentic-rag-knowledge-graph_postgres_data
# Should show: Created date, Mountpoint, Driver: local
```

### Check Data Exists
```bash
# Count documents
docker exec agentic-rag-postgres psql -U postgres -d agentic_rag -c "SELECT COUNT(*) as documents FROM documents;"

# Count chunks
docker exec agentic-rag-postgres psql -U postgres -d agentic_rag -c "SELECT COUNT(*) as chunks FROM chunks;"

# List workspaces
docker exec agentic-rag-postgres psql -U postgres -d agentic_rag -c "SELECT name, slug FROM workspaces;"
```

### Check Container Uptime
```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | grep agentic-rag
# Should show: "Up X days (healthy)"
```

---

## 🚨 What to Do If Data is Lost

### Step 1: Don't Panic
Data loss is recoverable if you have backups.

### Step 2: Check What Happened
```bash
# Check if containers are running
docker ps -a | grep agentic-rag

# Check if volumes exist
docker volume ls | grep agentic-rag

# Check system logs
journalctl -u docker --since "24 hours ago" | grep -i "error\|fail"
```

### Step 3: Restore from Backup
```bash
# Find most recent backup
LATEST_BACKUP=$(ls -t /var/backups/agentic-rag/postgres_backup_*.sql | head -1)

# Restore
docker exec -i agentic-rag-postgres psql -U postgres -d agentic_rag < "$LATEST_BACKUP"

# Verify
docker exec agentic-rag-postgres psql -U postgres -d agentic_rag -c "SELECT COUNT(*) FROM documents;"
```

### Step 4: Re-ingest if Necessary
```bash
# Only if backups are not available
# Re-ingest documents for each workspace
python ingest_workspace.py --workspace-id <WORKSPACE_ID> --directory documents/
```

---

## 📊 Current Data Status

```
Documents: 4 documents
Chunks: 39 chunks with embeddings
Workspaces: 1 (518341a0-ae02-4e28-b161-11ea84a392c1)
Volume Created: September 30, 2025
Last Verified: October 7, 2025
Status: ✅ SAFE & PERSISTENT
```

---

## 🆘 Emergency Contacts

**If data is lost:**
1. Check `/var/backups/agentic-rag/` for recent backups
2. Check `/tmp/postgres_backup_*.sql` for manual backups
3. Review this document for restore procedures
4. Contact system administrator if issue persists

**Backup Locations:**
- PostgreSQL: `/var/backups/agentic-rag/postgres_backup_*.sql`
- Neo4j: `/var/backups/agentic-rag/neo4j-backup-*/`
- Crontab: `/tmp/crontab_backup.txt`

---

## ✅ Safety Checklist Summary

- [x] Dangerous cron job removed
- [x] init.sql disabled and renamed
- [x] Persistent volumes configured
- [x] Safe restart policy set
- [x] Safe migration script created
- [x] Backup procedures documented
- [ ] **TODO:** Setup automated daily backups (recommended)
- [ ] **TODO:** Test restore procedure (recommended)

---

**Remember:** The only way to lose data now is through manual intervention. Always double-check commands before running them!
