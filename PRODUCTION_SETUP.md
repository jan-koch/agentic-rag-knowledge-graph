# Production Setup - botapi.kobra-dataworks.de

## Server Architecture

- **API Server**: botapi.kobra-dataworks.de (this server)
- **Laravel App**: Separate server
- **Communication**: Cross-origin requests via HTTPS

## API Server Setup (botapi.kobra-dataworks.de)

### 1. Update Environment Variables

Edit `.env`:

```env
# Application
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8058
LOG_LEVEL=INFO

# CORS - Allow Laravel app domain
ALLOWED_ORIGINS=https://your-laravel-domain.com,https://www.your-laravel-domain.com

# Database (existing settings)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agentic_rag
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM Configuration (existing settings)
LLM_PROVIDER=openai
LLM_API_KEY=your-key-here
# ... rest of your LLM config
```

### 2. Set Up Systemd Service

Create `/etc/systemd/system/rag-api.service`:

```ini
[Unit]
Description=RAG API Service
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/agentic-rag-knowledge-graph
Environment="PATH=/var/www/agentic-rag-knowledge-graph/venv/bin"
ExecStart=/var/www/agentic-rag-knowledge-graph/venv/bin/python -m agent.api
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable rag-api
sudo systemctl start rag-api
sudo systemctl status rag-api
```

### 3. Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/botapi.kobra-dataworks.de`:

```nginx
server {
    listen 80;
    server_name botapi.kobra-dataworks.de;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name botapi.kobra-dataworks.de;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/botapi.kobra-dataworks.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/botapi.kobra-dataworks.de/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # CORS headers (alternative to app-level CORS)
    add_header Access-Control-Allow-Origin "https://your-laravel-domain.com" always;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    add_header Access-Control-Allow-Credentials "true" always;

    # Handle preflight requests
    if ($request_method = OPTIONS) {
        return 204;
    }

    location / {
        proxy_pass http://127.0.0.1:8058;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeout settings for long responses
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Serve static widget
    location /widget/ {
        proxy_pass http://127.0.0.1:8058;
    }

    # API endpoints
    location /chat {
        proxy_pass http://127.0.0.1:8058;
    }

    location /v1/ {
        proxy_pass http://127.0.0.1:8058;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8058;
        access_log off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/botapi.kobra-dataworks.de /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Set Up SSL Certificate

```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d botapi.kobra-dataworks.de

# Auto-renewal (certbot sets this up automatically)
sudo certbot renew --dry-run
```

### 5. Firewall Configuration

```bash
# Allow HTTPS
sudo ufw allow 443/tcp

# Allow HTTP (for redirect)
sudo ufw allow 80/tcp

# Enable firewall if not already enabled
sudo ufw enable
sudo ufw status
```

## Laravel App Configuration

### Update `.env` on Laravel Server

```env
RAG_API_URL=https://botapi.kobra-dataworks.de
RAG_WORKSPACE_ID=518341a0-ae02-4e28-b161-11ea84a392c1
RAG_AGENT_ID=40ab91a7-a111-48ea-b4cd-f831efeaeff2
RAG_AGENT_NAME="Support Bot"
```

### Test the Integration

Create a test route in `routes/web.php`:

```php
Route::get('/test-chat-widget', function () {
    return view('test-chat');
});
```

Create `resources/views/test-chat.blade.php`:

```blade
<!DOCTYPE html>
<html>
<head>
    <title>Chat Widget Test</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="padding: 20px;">
    <h1>Chat Widget Test</h1>

    <iframe
        src="https://botapi.kobra-dataworks.de/widget/chat?workspace_id=518341a0-ae02-4e28-b161-11ea84a392c1&agent_id=40ab91a7-a111-48ea-b4cd-f831efeaeff2&agent_name=Ihnen%20Support%20Bot&api_url=https://botapi.kobra-dataworks.de"
        width="400px"
        height="600px"
        frameborder="0"
        style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    </iframe>
</body>
</html>
```

## Verification Checklist

### API Server (botapi.kobra-dataworks.de)

- [ ] Service running: `sudo systemctl status rag-api`
- [ ] Nginx configured and running: `sudo nginx -t && sudo systemctl status nginx`
- [ ] SSL certificate valid: `https://botapi.kobra-dataworks.de/health`
- [ ] CORS headers present: Check browser DevTools Network tab
- [ ] Database connected: Check API logs
- [ ] Neo4j connected: Check API logs

### Laravel Server

- [ ] `.env` updated with production URL
- [ ] Test route accessible: `/test-chat-widget`
- [ ] Widget loads in iframe
- [ ] No CORS errors in browser console
- [ ] Chat messages send successfully
- [ ] Responses received from API

## Testing Commands

### Test API Health

```bash
# From any machine
curl https://botapi.kobra-dataworks.de/health

# Expected response
{"status":"healthy","database":true,"graph_database":true,"llm_connection":true,"version":"0.1.0","timestamp":"..."}
```

### Test CORS

```bash
# From Laravel server or local machine
curl -I -X OPTIONS https://botapi.kobra-dataworks.de/chat \
  -H "Origin: https://your-laravel-domain.com" \
  -H "Access-Control-Request-Method: POST"

# Should see Access-Control-Allow-Origin header
```

### Test Widget Endpoint

```bash
curl https://botapi.kobra-dataworks.de/widget/chat
# Should return HTML content
```

### Test Chat Endpoint

```bash
curl -X POST https://botapi.kobra-dataworks.de/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "workspace_id": "518341a0-ae02-4e28-b161-11ea84a392c1",
    "agent_id": "40ab91a7-a111-48ea-b4cd-f831efeaeff2"
  }'
```

## Monitoring & Logs

### View API Logs

```bash
# Service logs
sudo journalctl -u rag-api -f

# Application logs (if configured)
tail -f /var/www/agentic-rag-knowledge-graph/logs/app.log
```

### View Nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

### Monitor Service

```bash
# Service status
sudo systemctl status rag-api

# Restart if needed
sudo systemctl restart rag-api
```

## Troubleshooting

### CORS Errors

**Symptom**: Browser console shows CORS errors

**Solutions**:
1. Update `ALLOWED_ORIGINS` in API `.env`
2. Include both www and non-www versions of your domain
3. Clear browser cache
4. Check Nginx CORS headers configuration

### Widget Not Loading

**Symptom**: Blank iframe or 404 error

**Solutions**:
1. Check `/widget/chat` endpoint: `curl https://botapi.kobra-dataworks.de/widget/chat`
2. Verify static file exists: `/var/www/agentic-rag-knowledge-graph/static/chat-widget.html`
3. Check Nginx configuration includes `/widget/` location
4. Review Nginx error logs

### SSL Certificate Issues

**Symptom**: "Not Secure" or certificate errors

**Solutions**:
1. Check certificate: `sudo certbot certificates`
2. Renew if needed: `sudo certbot renew`
3. Verify Nginx SSL paths
4. Check certificate expiration date

### API Not Responding

**Symptom**: 502 Bad Gateway or timeout

**Solutions**:
1. Check service: `sudo systemctl status rag-api`
2. Check if API is listening: `ss -tlnp | grep 8058`
3. Review API logs: `sudo journalctl -u rag-api -n 50`
4. Restart service: `sudo systemctl restart rag-api`

### Database Connection Errors

**Symptom**: API fails to start or returns 500 errors

**Solutions**:
1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Check database credentials in `.env`
3. Test connection: `psql -U postgres -d agentic_rag`
4. Check Neo4j: `sudo systemctl status neo4j`

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL backup
sudo -u postgres pg_dump agentic_rag > backup_$(date +%Y%m%d).sql

# Neo4j backup
sudo neo4j-admin dump --database=neo4j --to=/tmp/neo4j-backup-$(date +%Y%m%d).dump
```

### Restore

```bash
# PostgreSQL restore
sudo -u postgres psql agentic_rag < backup_20250108.sql

# Neo4j restore
sudo neo4j-admin load --from=/tmp/neo4j-backup-20250108.dump --database=neo4j --force
```

## Performance Tuning

### Gunicorn for Production (Optional)

Install gunicorn:

```bash
source venv/bin/activate
pip install gunicorn
```

Update systemd service to use gunicorn:

```ini
ExecStart=/var/www/agentic-rag-knowledge-graph/venv/bin/gunicorn agent.api:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8058 \
    --timeout 300 \
    --access-logfile /var/log/rag-api/access.log \
    --error-logfile /var/log/rag-api/error.log
```

## Security Hardening

### Rate Limiting (Nginx)

Add to Nginx config:

```nginx
# Define rate limit zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    # ... existing config ...

    location /chat {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:8058;
    }
}
```

### API Key Authentication

Update `.env` on API server:

```env
API_KEY_REQUIRED=true
API_KEY=your-secret-api-key-here
```

Update Laravel `.env`:

```env
RAG_API_KEY=your-secret-api-key-here
```

Update widget to include API key (if implementing authentication).

## Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "Deploying RAG API to production..."

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl restart rag-api

# Check status
sudo systemctl status rag-api

echo "Deployment complete!"
```

Make executable:

```bash
chmod +x deploy.sh
```
