# Dashboard Deployment Guide

This guide covers deploying the Streamlit dashboard to be accessible at `bot.kobra-dataworks.de` using Docker.

## Architecture

The dashboard runs in a Docker container using `network_mode: host`, allowing it to access the API running on `localhost:8058`. Your reverse proxy/tunnel maps `localhost:8501` to the public domain `bot.kobra-dataworks.de`.

```
Internet → bot.kobra-dataworks.de → localhost:8501 (Dashboard) → localhost:8058 (API)
```

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# Build and start the dashboard
docker compose -f docker-compose.dashboard.yml up -d --build

# Check logs
docker compose -f docker-compose.dashboard.yml logs -f dashboard

# Stop the dashboard
docker compose -f docker-compose.dashboard.yml down
```

### 2. Verify Dashboard is Running

```bash
# Check container status
docker ps | grep rag-dashboard

# Test locally
curl http://localhost:8501/_stcore/health

# Test health endpoint
curl http://localhost:8501
```

## Configuration

### API Connection

The dashboard connects to the API at `http://localhost:8058/v1` (configured in `webui.py`).

**Important**: Ensure the API server is running on the same host:
```bash
# Run API server
python -m agent.api_multi_tenant
```

### Streamlit Configuration

Configuration is in `.streamlit/config.toml`:
- **Server Port**: 8501
- **Server Address**: 0.0.0.0 (listens on all interfaces)
- **Public URL**: bot.kobra-dataworks.de
- **CORS**: Disabled (controlled by reverse proxy)

## Reverse Proxy / Tunnel Setup

Your reverse proxy should map `bot.kobra-dataworks.de` to `localhost:8501`.

### Example: Nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name bot.kobra-dataworks.de;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    location /_stcore/stream {
        proxy_pass http://localhost:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### Example: Cloudflare Tunnel

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Create tunnel
cloudflared tunnel create rag-dashboard

# Configure tunnel (in ~/.cloudflared/config.yml)
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: bot.kobra-dataworks.de
    service: http://localhost:8501
  - service: http_status:404

# Run tunnel
cloudflared tunnel run rag-dashboard
```

### Example: Docker with Traefik

If using Traefik, the `docker-compose.dashboard.yml` already includes labels:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.dashboard.rule=Host(`bot.kobra-dataworks.de`)"
  - "traefik.http.services.dashboard.loadbalancer.server.port=8501"
```

## Production Deployment

### 1. Full Stack with Docker Compose

Create a complete deployment file:

```bash
# Copy the production template
cat > docker-compose.full.yml <<EOF
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: pgvector/pgvector:pg16
    container_name: rag-postgres
    environment:
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
      POSTGRES_DB: rag_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Neo4j Database
  neo4j:
    image: neo4j:5.13
    container_name: rag-neo4j
    environment:
      NEO4J_AUTH: neo4j/\${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
    ports:
      - "7474:7474"
      - "7687:7687"
    restart: unless-stopped

  # API Server
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: rag-api
    environment:
      - DATABASE_URL=postgresql://rag_user:\${POSTGRES_PASSWORD}@localhost:5432/rag_db
      - NEO4J_URI=bolt://localhost:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=\${NEO4J_PASSWORD}
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
    network_mode: host
    depends_on:
      - postgres
      - neo4j
    restart: unless-stopped

  # Dashboard
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    container_name: rag-dashboard
    network_mode: host
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  neo4j_data:
EOF

# Deploy full stack
docker compose -f docker-compose.full.yml up -d
```

### 2. Environment Variables

Create `.env.production`:

```bash
# Database
POSTGRES_PASSWORD=your_secure_password_here
NEO4J_PASSWORD=your_secure_password_here

# API Keys
OPENAI_API_KEY=sk-...

# API Configuration
API_KEY_REQUIRED=true
LOG_LEVEL=INFO

# Database URLs
DATABASE_URL=postgresql://rag_user:password@localhost:5432/rag_db
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### 3. SSL/TLS Setup

Ensure your reverse proxy handles SSL/TLS termination. The dashboard itself runs on HTTP internally.

### 4. Security Considerations

- ✅ Dashboard runs on `localhost:8501` (not exposed directly)
- ✅ API runs on `localhost:8058` (not exposed directly)
- ✅ Reverse proxy provides SSL/TLS encryption
- ✅ Use `network_mode: host` for localhost communication
- ⚠️ Ensure firewall only allows necessary ports (443 for HTTPS)

## Monitoring

### Check Dashboard Health

```bash
# Container logs
docker logs rag-dashboard -f

# Health check
curl http://localhost:8501/_stcore/health

# Container status
docker ps | grep rag-dashboard
```

### Dashboard Metrics

Access Streamlit metrics at `http://localhost:8501/_stcore/metrics` (internal only)

## Troubleshooting

### Dashboard can't connect to API

**Symptom**: Dashboard shows "API Unavailable" in sidebar

**Solutions**:
```bash
# Check API is running
curl http://localhost:8058/v1/health

# Check API logs
python -m agent.api_multi_tenant

# Verify network mode
docker inspect rag-dashboard | grep NetworkMode
# Should show: "NetworkMode": "host"
```

### Dashboard not accessible from public domain

**Symptom**: `bot.kobra-dataworks.de` times out or shows error

**Solutions**:
```bash
# Check dashboard is listening
netstat -tlnp | grep 8501

# Check reverse proxy/tunnel is running
# (depends on your setup: nginx, cloudflared, traefik, etc.)

# Check firewall
sudo ufw status
sudo ufw allow 8501/tcp  # If needed for reverse proxy
```

### WebSocket connection issues

**Symptom**: Chat doesn't stream, dashboard disconnects

**Solution**: Ensure reverse proxy forwards WebSocket connections:

```nginx
# Nginx: Add these headers
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### Container keeps restarting

```bash
# Check logs
docker logs rag-dashboard

# Common issues:
# 1. Missing dependencies (rebuild image)
docker compose -f docker-compose.dashboard.yml build --no-cache dashboard

# 2. Port already in use
sudo lsof -i :8501
# Kill conflicting process or change port

# 3. API not available
# Start API first: python -m agent.api_multi_tenant
```

## Updates and Maintenance

### Update Dashboard

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.dashboard.yml up -d --build

# Check it's running
docker ps | grep rag-dashboard
```

### Backup Data

The dashboard itself is stateless. Backup the API databases:

```bash
# PostgreSQL backup
./scripts/backup-database.sh

# Neo4j backup
./scripts/backup-neo4j.sh
```

## Performance Tuning

### Resource Limits

Add resource limits in `docker-compose.dashboard.yml`:

```yaml
services:
  dashboard:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Streamlit Configuration

Edit `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 200  # MB
maxMessageSize = 200  # MB

[browser]
gatherUsageStats = false
```

## Multi-Instance Setup

For high availability, run multiple dashboard instances behind a load balancer:

```yaml
services:
  dashboard-1:
    # ... config ...
    ports:
      - "8501:8501"

  dashboard-2:
    # ... config ...
    ports:
      - "8502:8501"

  # Load balancer (nginx, haproxy, etc.)
  lb:
    image: nginx:alpine
    # ... config to balance between 8501 and 8502 ...
```

## Support

For issues:
1. Check logs: `docker logs rag-dashboard`
2. Verify API connectivity: `curl http://localhost:8058/v1/health`
3. Check reverse proxy configuration
4. Review this guide's troubleshooting section
