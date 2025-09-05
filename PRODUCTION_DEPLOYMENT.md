# Production Deployment Guide

This guide covers how to securely deploy the Agentic RAG Knowledge Graph system to production with Cloudflare Tunnel integration and n8n-only access.

## 🏗️ Architecture Overview

```
Internet → Cloudflare Tunnel → Docker Container (127.0.0.1:8058) → Internal Network
                                    ↓
                            [PostgreSQL + Neo4j]
                              (Internal Only)
```

### Security Model

- **Application**: Binds only to `127.0.0.1:8058` (localhost)
- **Databases**: No external ports, internal Docker network only
- **External Access**: Only through Cloudflare Tunnel
- **Endpoints**: Only `/n8n/*` and `/health` exposed externally
- **Authentication**: API key required for n8n endpoints

## 📋 Pre-Deployment Checklist

### System Requirements
- [ ] Linux server (Ubuntu 20.04+ recommended)
- [ ] Docker Engine 24.0+
- [ ] Docker Compose v2.0+
- [ ] 4GB+ RAM, 20GB+ storage
- [ ] Cloudflare account with domain

### Security Requirements
- [ ] Non-root user account
- [ ] Firewall configured (only SSH + HTTP/HTTPS if needed)
- [ ] SSL certificates (handled by Cloudflare)
- [ ] Strong passwords and API keys generated

## 🚀 Deployment Steps

### Step 1: Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Create application directory
mkdir -p ~/agentic-rag && cd ~/agentic-rag
```

### Step 2: Configure Environment

```bash
# Copy production environment template
cp .env.production .env

# Edit environment variables
nano .env
```

**Critical Variables to Set:**

```bash
# Database passwords (generate strong passwords)
POSTGRES_PASSWORD=your-secure-postgres-password
NEO4J_PASSWORD=your-secure-neo4j-password

# LLM API keys
LLM_API_KEY=sk-your-openai-api-key-here
EMBEDDING_API_KEY=sk-your-openai-api-key-here

# n8n Security (REQUIRED)
N8N_API_KEY=your-secure-n8n-api-key-here
N8N_WEBHOOK_SECRET=your-webhook-secret-here

# Security Configuration
ALLOWED_ORIGINS=https://your-n8n-instance.com
ENABLE_IP_WHITELIST=true
ALLOWED_N8N_IPS=your-n8n-server-ip
```

### Step 3: Deploy Application

```bash
# Run deployment script
./scripts/deploy-production.sh
```

The script will:
- ✅ Validate environment configuration
- ✅ Build production Docker image
- ✅ Start all services with health checks
- ✅ Verify API functionality
- ✅ Display service status

### Step 4: Configure Cloudflare Tunnel

You'll handle this step with Docker Compose. The provided `cloudflare-tunnel-config.yml` shows the recommended configuration:

**Key Security Settings:**
- Only `/n8n/*` endpoints exposed
- `/health` endpoint for monitoring
- All other paths return 404
- Proper timeout and connection settings

### Step 5: Test Deployment

```bash
# Test health endpoint
curl http://127.0.0.1:8058/health

# Test n8n endpoint (should require API key)
curl -X POST http://127.0.0.1:8058/n8n/simple \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR-N8N-API-KEY" \
  -d '{"message": "Hello from production!"}'
```

## 🛡️ Security Features

### Application Security
- **Non-root execution**: Container runs as user 1000:1000
- **Read-only filesystem**: Application files are read-only
- **Input sanitization**: All input is sanitized before processing
- **Rate limiting**: 60 requests/minute by default
- **Security headers**: HSTS, CSP, etc. automatically added

### Network Security
- **Localhost binding**: API only accessible from localhost
- **Internal networks**: Databases on isolated Docker network
- **No exposed ports**: Only Cloudflare Tunnel can reach the app
- **IP whitelisting**: Optional restriction to specific IPs

### Authentication & Authorization
- **API key authentication**: Required for all n8n endpoints
- **Webhook signatures**: Optional signature verification
- **CORS restrictions**: Configurable allowed origins
- **Session management**: Secure session handling with metadata

### Data Security
- **Environment isolation**: Production environment variables
- **Encrypted backups**: GPG encryption for database backups
- **Audit logging**: All requests logged with metadata
- **Secure defaults**: Security-first configuration

## 📊 Monitoring & Maintenance

### Service Management

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# View app logs only
docker compose -f docker-compose.prod.yml logs -f app

# Restart services
docker compose -f docker-compose.prod.yml restart

# Update deployment
./scripts/deploy-production.sh
```

### Health Monitoring

The `/health` endpoint provides comprehensive status:

```json
{
  "status": "healthy",
  "database": true,
  "graph_database": true,  
  "llm_connection": true,
  "version": "0.1.0",
  "timestamp": "2025-09-05T02:40:00.000Z"
}
```

### Log Monitoring

```bash
# Application logs
docker compose -f docker-compose.prod.yml logs app | tail -100

# Database logs
docker compose -f docker-compose.prod.yml logs postgres | tail -100

# Neo4j logs
docker compose -f docker-compose.prod.yml logs neo4j | tail -100
```

## 💾 Backup Strategy

### Automated Backups

Set up daily backups with cron:

```bash
# Edit crontab
crontab -e

# Add backup jobs
0 2 * * * /path/to/agentic-rag/scripts/backup-database.sh >> /var/log/rag-backup.log 2>&1
15 2 * * * /path/to/agentic-rag/scripts/backup-neo4j.sh >> /var/log/rag-backup.log 2>&1
```

### Manual Backup

```bash
# Backup PostgreSQL
./scripts/backup-database.sh

# Backup Neo4j
./scripts/backup-neo4j.sh
```

### Backup Security
- **Encryption**: Backups encrypted with GPG
- **Retention**: 7-day retention policy
- **Storage**: Store encrypted backups off-site
- **Testing**: Regularly test restore procedures

## 🔧 Configuration Management

### Environment Updates

```bash
# Update environment variables
nano .env

# Restart to apply changes
docker compose -f docker-compose.prod.yml restart app
```

### Application Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and redeploy
./scripts/deploy-production.sh
```

### Security Updates

```bash
# Update base images
docker compose -f docker-compose.prod.yml pull

# Rebuild application image
docker build -f Dockerfile.prod -t agentic-rag:latest .

# Restart with new images
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

## 🚨 Troubleshooting

### Common Issues

**Service Won't Start**
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check disk space
df -h

# Check memory usage
free -h
```

**Database Connection Issues**
```bash
# Check database health
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U raguser

# Test Neo4j connection
docker compose -f docker-compose.prod.yml exec neo4j cypher-shell -u neo4j -p password
```

**API Authentication Issues**
```bash
# Verify API key in environment
grep N8N_API_KEY .env

# Check API key in n8n configuration
curl -X POST https://your-domain.com/n8n/simple \
  -H "Authorization: Bearer YOUR-API-KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### Performance Optimization

**Database Tuning**
- PostgreSQL configured with optimized settings
- Neo4j memory allocation tuned for workload
- Connection pooling enabled

**Application Tuning**
```bash
# Increase worker processes if needed
# Edit docker-compose.prod.yml
services:
  app:
    command: ["python", "-m", "agent.api", "--workers", "4"]
```

## 🔐 Security Hardening

### System Hardening
- [ ] Configure firewall (ufw/iptables)
- [ ] Disable unused services
- [ ] Set up fail2ban
- [ ] Enable automatic security updates
- [ ] Configure log rotation

### Container Security
- [ ] Regular image updates
- [ ] Vulnerability scanning
- [ ] Resource limits enforced
- [ ] Security policies applied

### Network Security
- [ ] VPN access for management
- [ ] Network segmentation
- [ ] DNS filtering
- [ ] DDoS protection via Cloudflare

## 📚 Integration with n8n

### n8n Workflow Setup

1. **HTTP Request Node Configuration:**
   ```
   Method: POST
   URL: https://your-domain.com/n8n/chat
   Headers: 
     Authorization: Bearer YOUR-N8N-API-KEY
     Content-Type: application/json
   Body:
     {
       "chatInput": "{{ $json.chatInput }}",
       "sessionId": "{{ $json.sessionId }}",
       "userId": "{{ $json.userId }}"
     }
   ```

2. **Response Handling:**
   - Success: Process `response` field
   - Session: Use `sessionId` for continuity
   - Tools: Monitor `toolsUsed` for debugging

### Security Best Practices

1. **Store API keys securely** in n8n credentials
2. **Use specific user IDs** for tracking
3. **Implement retry logic** for failed requests
4. **Monitor rate limits** in n8n workflows
5. **Log requests** for audit purposes

## 🎯 Production Readiness Checklist

### Before Go-Live
- [ ] All passwords changed from defaults
- [ ] API keys configured and tested
- [ ] Backups tested and verified
- [ ] Monitoring configured
- [ ] Cloudflare Tunnel tested
- [ ] n8n integration tested
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Documentation updated
- [ ] Team trained on operations

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Verify backup automation
- [ ] Test disaster recovery
- [ ] Update monitoring alerts
- [ ] Schedule security reviews

---

**⚠️ Important**: This deployment is designed for security-conscious production use. All external access is controlled through Cloudflare Tunnel, and only n8n integration endpoints are exposed. Regular security updates and monitoring are essential for maintaining security posture.