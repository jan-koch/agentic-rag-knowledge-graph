# Riddly AI Chat Service

Modern ChatGPT-style interface built with Streamlit and Tailwind CSS.

## Quick Start

### 1. Install as System Service

```bash
cd /var/www/agentic-rag-knowledge-graph/frontend/streamlit
sudo ./service-manager.sh install
sudo ./service-manager.sh start
```

### 2. Check Status

```bash
./service-manager.sh status
```

### 3. Access the Application

- **Local**: http://localhost:8501
- **Network**: http://YOUR_SERVER_IP:8501

## Service Management

### Available Commands

```bash
# Install and enable service
sudo ./service-manager.sh install

# Start service
sudo ./service-manager.sh start

# Stop service  
sudo ./service-manager.sh stop

# Restart service
sudo ./service-manager.sh restart

# Check status
./service-manager.sh status

# View logs
./service-manager.sh logs

# Uninstall service
sudo ./service-manager.sh uninstall
```

### Manual Development Run

```bash
# Run directly without service
python run.py

# Or with streamlit directly
streamlit run app.py --server.port 8501
```

## Features

- 🎨 **Tailwind CSS Design** - Clean, modern interface
- 🌙 **Dark/Light Mode** - Toggle in sidebar settings
- 📱 **Fully Responsive** - Works on all devices
- 💬 **ChatGPT-style Interface** - Familiar chat experience
- 📚 **Session Management** - Save and restore chat history
- ⚡ **Real-time Streaming** - Live response updates
- 🔐 **API Configuration** - Easy setup in sidebar
- 🚀 **System Service** - Runs automatically on boot

## Troubleshooting

### Neo4j Vector Similarity Error

If you see the error: `Unknown function 'vector.similarity.cosine'`

```bash
# Restart Neo4j with updated plugins
cd /var/www/agentic-rag-knowledge-graph
docker compose down neo4j
docker compose up -d neo4j

# Wait for Neo4j to start, then check
docker compose logs neo4j
```

### Service Issues

```bash
# Check service status
systemctl status riddly-chat

# View detailed logs
journalctl -u riddly-chat -f

# Restart if needed
sudo systemctl restart riddly-chat
```