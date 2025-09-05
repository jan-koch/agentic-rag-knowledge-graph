# Security Guide

This document outlines the comprehensive security measures implemented in the Agentic RAG Knowledge Graph system for production deployment.

## 🛡️ Security Architecture

### Defense in Depth Strategy

```
Internet → Cloudflare → Tunnel → Localhost → Application → Internal Network → Databases
    ↓         ↓         ↓         ↓            ↓             ↓               ↓
  DDoS    SSL/TLS   Access    Rate Limit   Authentication  Network      Encryption
  WAF     Protection Control  Input Valid  Authorization   Isolation    Access Control
```

## 🔒 Authentication & Authorization

### API Key Authentication

**Implementation:**
- Bearer token authentication for all n8n endpoints
- HMAC-based API key validation
- Constant-time comparison to prevent timing attacks

**Configuration:**
```bash
# Generate secure API key (32+ characters)
N8N_API_KEY=your-cryptographically-secure-api-key-here

# Optional webhook signature verification
N8N_WEBHOOK_SECRET=your-webhook-signature-secret
```

**Usage in n8n:**
```json
{
  "headers": {
    "Authorization": "Bearer YOUR-N8N-API-KEY",
    "Content-Type": "application/json"
  }
}
```

### Webhook Signature Verification (Optional)

Verify webhook authenticity using HMAC-SHA256 signatures:

```python
# Automatic verification in security middleware
def verify_n8n_webhook_signature(payload, signature, secret):
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## 🌐 Network Security

### Localhost-Only Binding

**Application Security:**
- API server binds only to `127.0.0.1:8058`
- No direct internet access to application
- All external access through Cloudflare Tunnel

**Docker Network Isolation:**
```yaml
# Production configuration
services:
  app:
    ports:
      - "127.0.0.1:8058:8058"  # Localhost only
  postgres:
    # No exposed ports - internal network only
  neo4j:
    # No exposed ports - internal network only
networks:
  internal:
    driver: bridge
    internal: false  # Set to true for complete isolation
```

### IP Whitelisting

**Configuration:**
```bash
ENABLE_IP_WHITELIST=true
ALLOWED_N8N_IPS=192.168.1.100,10.0.0.5,172.16.0.10
```

**Features:**
- Source IP validation from headers (X-Forwarded-For, X-Real-IP, CF-Connecting-IP)
- Configurable IP address whitelist
- Automatic blocking of unauthorized IPs

### CORS Protection

**Strict CORS Policy:**
```bash
# Restrict to specific n8n domains
ALLOWED_ORIGINS=https://your-n8n-instance.com,https://backup-n8n.com

# Default (less secure)
ALLOWED_ORIGINS=*
```

**Implementation:**
- Configurable allowed origins
- Restricted HTTP methods (GET, POST, OPTIONS only)
- Limited allowed headers

## 🔐 Input Security

### Input Sanitization

**Automatic Sanitization:**
```python
def sanitize_input(data):
    # Remove dangerous patterns
    dangerous_patterns = [
        "<script", "</script>", "javascript:", "vbscript:",
        "onload=", "onerror=", "onclick=", "onmouseover=",
        "<iframe", "</iframe>", "<object", "</object>"
    ]
    # Length limiting, XSS prevention, injection protection
```

**Features:**
- XSS prevention
- Script tag removal
- Length limiting (configurable)
- Nested object sanitization
- SQL injection prevention

### Rate Limiting

**Configuration:**
```bash
RATE_LIMIT_REQUESTS=60        # Requests per window
RATE_LIMIT_WINDOW_SECONDS=60  # Window duration
```

**Implementation:**
- Per-IP rate limiting
- Sliding window algorithm
- Configurable limits
- Automatic cleanup of expired entries

### Request Validation

**Security Headers:**
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'none'
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## 🐳 Container Security

### Non-Root Execution

**Security Configuration:**
```dockerfile
# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser
USER appuser
```

**Docker Compose Security:**
```yaml
services:
  app:
    user: "1000:1000"
    read_only: true
    security_opt:
      - no-new-privileges:true
    tmpfs:
      - /tmp:size=100M,noexec,nosuid,nodev
```

### Container Hardening

**Features:**
- Read-only root filesystem
- Temporary filesystem for /tmp
- No new privileges flag
- Minimal attack surface
- Security-optimized base image

### Resource Limits

**Configuration:**
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

## 🗄️ Data Security

### Database Security

**PostgreSQL Security:**
```yaml
services:
  postgres:
    environment:
      POSTGRES_INITDB_ARGS: "--auth-host=md5 --auth-local=md5"
    command: |
      postgres
      -c ssl=on
      -c log_statement=error
      -c log_min_duration_statement=1000
```

**Neo4j Security:**
```yaml
services:
  neo4j:
    environment:
      NEO4J_dbms_security_auth_minimum_password_length: "8"
      NEO4J_dbms_logs_security_level: "INFO"
      NEO4J_metrics_enabled: "false"
```

### Encryption at Rest

**Database Volumes:**
- Encrypted filesystem recommended
- Secure volume mounting
- Backup encryption with GPG

**Backup Security:**
```bash
# Encrypted backup creation
gpg --symmetric --cipher-algo AES256 backup.sql
```

### Session Security

**Session Management:**
```python
# Secure session metadata
metadata = {
    "source": "n8n",
    "client_ip": security_info["client_ip"],
    "user_agent": security_info["user_agent"],
    "timestamp": datetime.now().isoformat(),
    "api_key_used": True
}
```

## 🌍 External Security (Cloudflare)

### Tunnel Configuration

**Security Benefits:**
- No exposed server ports
- Automatic SSL/TLS termination
- DDoS protection
- Geographic access control
- Web Application Firewall (WAF)

**Recommended Settings:**
```yaml
ingress:
  # Only expose n8n endpoints
  - hostname: rag-api.yourdomain.com
    path: /n8n/*
    service: http://127.0.0.1:8058
  
  # Health monitoring
  - hostname: rag-api.yourdomain.com
    path: /health
    service: http://127.0.0.1:8058
  
  # Block everything else
  - service: http_status:404
```

### Cloudflare Security Features

**Enable These Features:**
- [ ] Always Use HTTPS
- [ ] Automatic HTTPS Rewrites  
- [ ] HTTP Strict Transport Security (HSTS)
- [ ] Minimum TLS Version (1.2+)
- [ ] TLS 1.3 Support
- [ ] Bot Fight Mode
- [ ] Security Level: High
- [ ] Challenge Passage: 30 minutes

## 🔍 Monitoring & Logging

### Security Logging

**Logged Events:**
- All API requests with metadata
- Authentication attempts
- Rate limit violations
- Input sanitization triggers
- Security policy violations
- Database access patterns

**Log Format:**
```json
{
  "timestamp": "2025-09-05T02:40:00.000Z",
  "level": "INFO",
  "event": "n8n_request",
  "client_ip": "192.168.1.100",
  "user_agent": "n8n-webhook",
  "endpoint": "/n8n/chat",
  "user_id": "n8n-user",
  "session_id": "session-123",
  "tools_used": 1,
  "response_time_ms": 250
}
```

### Security Monitoring

**Alerting Triggers:**
- High rate limit violations
- Authentication failures
- Suspicious user agents
- Unusual access patterns
- Database connection failures
- Container health issues

## 🚨 Incident Response

### Security Incident Procedures

**Immediate Response:**
1. **Isolate**: Stop affected containers
2. **Assess**: Check logs for extent of breach
3. **Contain**: Update firewall rules if needed
4. **Investigate**: Analyze attack vectors
5. **Recover**: Restore from clean backups
6. **Learn**: Update security measures

**Emergency Commands:**
```bash
# Stop all services immediately
docker compose -f docker-compose.prod.yml down

# Check recent logs for suspicious activity
docker compose -f docker-compose.prod.yml logs --since=1h | grep -E "(ERROR|WARN|suspicious)"

# Rotate API keys
# 1. Update .env with new N8N_API_KEY
# 2. Restart services
# 3. Update n8n workflows with new key
```

## 🔧 Security Maintenance

### Regular Security Tasks

**Weekly:**
- [ ] Review access logs
- [ ] Check for failed authentication attempts
- [ ] Verify backup integrity
- [ ] Monitor resource usage

**Monthly:**
- [ ] Update Docker images
- [ ] Review and rotate API keys
- [ ] Test disaster recovery procedures
- [ ] Security vulnerability scan

**Quarterly:**
- [ ] Full security audit
- [ ] Penetration testing
- [ ] Review access controls
- [ ] Update security policies

### Security Updates

**Container Updates:**
```bash
# Pull latest secure base images
docker compose -f docker-compose.prod.yml pull

# Rebuild application with updates
docker build -f Dockerfile.prod -t agentic-rag:latest .

# Deploy with zero downtime
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

**Security Patching:**
```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Docker updates
sudo apt update && sudo apt install docker-ce docker-compose-plugin

# Application dependencies
pip install --upgrade -r requirements.txt
```

## 🔐 Compliance & Best Practices

### Security Standards

**Implemented Standards:**
- OWASP API Security Top 10
- Container Security Best Practices
- Zero Trust Network Architecture
- Defense in Depth Strategy
- Principle of Least Privilege

### Data Protection

**Privacy Features:**
- No sensitive data logging
- Session data encryption
- User data anonymization options
- GDPR-compliant data handling
- Configurable data retention

### Audit Trail

**Compliance Logging:**
- All API access logged
- Authentication events tracked
- Configuration changes recorded
- Data access patterns monitored
- Backup and restore activities logged

## ⚠️ Security Warnings

### Critical Security Notes

1. **Never expose databases directly** to the internet
2. **Always use strong API keys** (32+ characters, cryptographically secure)
3. **Enable IP whitelisting** in production environments  
4. **Regularly rotate credentials** (API keys, database passwords)
5. **Monitor logs actively** for suspicious activity
6. **Keep containers updated** with latest security patches
7. **Test backups regularly** to ensure recovery capability
8. **Use HTTPS everywhere** (handled by Cloudflare)

### Common Security Mistakes

❌ **Don't:**
- Use default passwords
- Expose database ports
- Allow all CORS origins in production
- Skip input validation
- Ignore security logs
- Use root user in containers

✅ **Do:**
- Generate strong, unique credentials
- Use localhost-only binding
- Implement strict CORS policies
- Sanitize all input
- Monitor and alert on security events
- Run as non-root user

---

**🔒 Security is a continuous process.** Regular reviews, updates, and monitoring are essential for maintaining a secure production deployment.