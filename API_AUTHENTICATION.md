# API Authentication Guide

## Overview

The Agentic RAG API uses Bearer token authentication to secure all endpoints (except health check). This ensures only authorized clients can access the API.

## Configuration

### 1. Generate a Secure API Key

Generate a cryptographically secure API key:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Set Environment Variables

Add the following to your `.env` file:

```env
# API Security
API_KEY=your-generated-api-key-here
API_KEY_REQUIRED=true  # Set to false to disable authentication (development only)
```

### 3. Security Settings

The API is configured to:
- Listen only on localhost (127.0.0.1) by default
- Require API key authentication for all endpoints except `/health`
- Use secure header validation
- Implement rate limiting

## Usage

### Making Authenticated Requests

Include the API key in the `Authorization` header as a Bearer token:

```bash
# Example with curl
curl -X POST http://127.0.0.1:8058/chat \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is RAG?"}'
```

### Python Example

```python
import requests

API_KEY = "your-api-key-here"
API_URL = "http://127.0.0.1:8058"

# Make authenticated request
response = requests.post(
    f"{API_URL}/chat",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"message": "Explain knowledge graphs"}
)

if response.status_code == 200:
    data = response.json()
    print(data["message"])
else:
    print(f"Error: {response.status_code}")
```

### JavaScript/TypeScript Example

```javascript
const API_KEY = 'your-api-key-here';
const API_URL = 'http://127.0.0.1:8058';

// Make authenticated request
fetch(`${API_URL}/chat`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'What are vector embeddings?'
  })
})
.then(response => response.json())
.then(data => console.log(data.message))
.catch(error => console.error('Error:', error));
```

## Protected Endpoints

The following endpoints require API key authentication:

- `POST /chat` - Main chat endpoint
- `POST /chat/stream` - Streaming chat endpoint
- `POST /search/vector` - Vector search
- `POST /search/graph` - Graph search
- `POST /search/hybrid` - Hybrid search
- `GET /documents` - List documents
- `GET /sessions/{session_id}` - Get session info

### Unprotected Endpoints

- `GET /health` - Health check (no authentication required)

## n8n Integration

For n8n workflows, you can use either:

1. **Main API Key**: Use the same `API_KEY` for n8n requests
2. **Separate n8n Key**: Configure `N8N_API_KEY` in `.env` for dedicated n8n endpoints

n8n-specific endpoints:
- `POST /n8n/chat` - n8n chat webhook
- `POST /n8n/simple` - Simple n8n webhook

## Testing Authentication

Run the included test script to verify authentication is working:

```bash
python test_api_auth.py
```

This will test:
- ✓ Unauthenticated requests are rejected (401)
- ✓ Invalid API keys are rejected (401)
- ✓ Valid API keys are accepted (200)
- ✓ All protected endpoints require authentication

## Security Best Practices

1. **Keep API Keys Secret**: Never commit API keys to version control
2. **Use HTTPS in Production**: Always use TLS/SSL in production environments
3. **Rotate Keys Regularly**: Change API keys periodically
4. **Use Environment Variables**: Store keys in `.env` files, not in code
5. **Monitor Access**: Log and monitor API key usage
6. **Limit Scope**: Create separate keys for different services when possible

## Cloudflare Tunnel Integration

When using Cloudflare Tunnel:

1. The API listens on `127.0.0.1:8058` (localhost only)
2. Cloudflare Tunnel connects to the local API
3. External requests go through Cloudflare's network
4. API key authentication is still required

Example Cloudflare Tunnel configuration:

```yaml
tunnel: your-tunnel-id
credentials-file: /path/to/credentials.json

ingress:
  - hostname: api.yourdomain.com
    service: http://127.0.0.1:8058
  - service: http_status:404
```

## Troubleshooting

### 401 Unauthorized

- Check that the API key is correct
- Ensure the `Authorization` header format is: `Bearer YOUR_API_KEY`
- Verify `API_KEY_REQUIRED=true` in `.env`

### 500 Server Error

- Check that `API_KEY` is set in `.env` file
- Restart the API server after changing `.env`

### Connection Refused

- Verify the API is running: `python -m agent.api`
- Check the port number (default: 8058)
- Ensure `APP_HOST=127.0.0.1` in `.env`

## Development Mode

To disable API key requirement for local development:

```env
API_KEY_REQUIRED=false
```

⚠️ **Warning**: Never disable authentication in production!