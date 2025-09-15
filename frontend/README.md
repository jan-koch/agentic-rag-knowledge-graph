# Frontend Applications

This directory contains two frontend implementations for the Agentic RAG system:

## 📱 Standalone Chat Application (`/app/`)

A full-featured web application with:

- **Modern UI**: Clean, responsive design with light/dark themes
- **Real-time streaming**: Server-sent events for live responses
- **Session management**: Persistent chat history and sessions
- **Search modes**: Hybrid, vector, and knowledge graph search
- **Settings panel**: Configurable API endpoint, authentication, and preferences
- **Export functionality**: Download chat conversations as JSON
- **Mobile responsive**: Works on all screen sizes

### Files:
- `index.html` - Main application markup
- `styles.css` - Comprehensive styling with CSS custom properties
- `app.js` - Full application logic and API integration

## 🔗 Embeddable Chat Widget (`/widget/`)

A lightweight widget that can be embedded on any website:

- **Easy integration**: Single JavaScript file inclusion
- **Customizable**: Themes, positioning, messaging
- **Minimal footprint**: Optimized for embedding
- **No dependencies**: Pure vanilla JavaScript
- **Responsive design**: Adapts to container or viewport

### Files:
- `chat-widget.js` - Complete widget implementation
- `example.html` - Demonstration and integration guide

## 🚀 Quick Start

### 1. Start the API Server

```bash
# From the project root
python -m agent.api
```

The API will start on `http://localhost:8058` by default.

### 2. Serve the Frontend

```bash
# From the frontend directory
python3 serve.py
```

This will start a local server and open your browser to the chat application.

### 3. Configure API Access

Make sure to set your API key in the settings or widget configuration:

```javascript
// For the widget
new ChatWidget({
    apiUrl: 'http://localhost:8058',
    apiKey: 'your-secure-api-key-here'
});
```

## 🛠 Integration Guide

### Standalone Application

Deploy the `/app/` directory to any web server. Users can:

1. Configure the API endpoint in settings
2. Enter their API key
3. Choose search type (hybrid/vector/graph)
4. Start chatting with the AI assistant

### Embeddable Widget

Add to any HTML page:

```html
<script src="https://your-domain.com/path/to/chat-widget.js"></script>
<script>
  new ChatWidget({
    apiUrl: 'https://your-api-domain.com',
    apiKey: 'your-api-key',
    theme: 'light', // or 'dark'
    position: 'bottom-right',
    title: 'AI Assistant',
    welcomeMessage: 'How can I help you today?'
  });
</script>
```

### Configuration Options

Both implementations support:

- **API URL**: Your Agentic RAG server endpoint
- **API Key**: Authentication token
- **Theme**: Light/dark/auto modes
- **Search Type**: hybrid (recommended), vector, or graph
- **Streaming**: Real-time response streaming (recommended)

## 🔧 Development

### Local Development

1. Install dependencies (none required - pure HTML/CSS/JS)
2. Run `python3 serve.py` to start development server
3. Edit files and refresh browser

### Customization

Both applications use CSS custom properties for easy theming:

```css
:root {
  --primary-color: #667eea;
  --secondary-color: #764ba2;
  --bg-primary: #ffffff;
  --text-primary: #212529;
  /* ... */
}
```

### API Integration

The frontends use these API endpoints:

- `POST /chat` - Non-streaming chat
- `POST /chat/stream` - Streaming chat (recommended)
- `GET /health` - Server health check
- `GET /sessions/{id}` - Load conversation history

## 📋 Features Comparison

| Feature | Standalone App | Embeddable Widget |
|---------|---------------|-------------------|
| Full UI | ✅ | ❌ (popup only) |
| Chat history | ✅ | ❌ |
| Settings panel | ✅ | ❌ (config only) |
| Export chats | ✅ | ❌ |
| Themes | ✅ | ✅ |
| Streaming | ✅ | ✅ |
| Mobile responsive | ✅ | ✅ |
| Easy embedding | ❌ | ✅ |
| File size | ~15KB | ~8KB |

## 🛡 Security Considerations

- Always use HTTPS in production
- Restrict CORS origins to your domains
- Keep API keys secure (use environment variables)
- Validate and sanitize user inputs
- Implement rate limiting on the API server

## 🎨 Customization Examples

### Custom Widget Theme

```javascript
new ChatWidget({
    apiUrl: 'https://api.example.com',
    apiKey: 'your-key',
    theme: 'dark',
    width: '350px',
    height: '500px',
    title: 'Support Assistant',
    welcomeMessage: 'Hello! How can I assist you today?',
    placeholder: 'Type your question here...'
});
```

### Custom CSS Variables

```css
:root {
    --primary-gradient: linear-gradient(135deg, #ff6b6b, #ee5a24);
    --primary-color: #ff6b6b;
    --radius: 12px;
}
```

## 📱 Browser Support

- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+

Features requiring modern browsers:
- CSS Custom Properties
- Fetch API
- Server-Sent Events (streaming)
- CSS Grid/Flexbox

## 🐛 Troubleshooting

### Common Issues

1. **CORS errors**: Ensure `ALLOWED_ORIGINS` includes your domain
2. **API key errors**: Check API key in settings/configuration
3. **Connection issues**: Verify API server is running and accessible
4. **Streaming not working**: Check if Server-Sent Events are supported

### Debug Mode

Enable browser developer tools and check console for detailed error messages.

## 📚 Further Reading

- [Main Project Documentation](../README.md)
- [API Documentation](../agent/api.py)
- [Security Guide](../SECURITY.md)
- [Production Deployment](../PRODUCTION_DEPLOYMENT.md)