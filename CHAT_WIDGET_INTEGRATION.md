# Chat Widget Integration Guide

## Overview

The chat widget allows you to embed the AI chat agent into any web application using a simple iframe. It's designed to be lightweight, responsive, and easy to integrate.

## Quick Start

### 1. Get Your Configuration

You need three pieces of information:
- **Workspace ID**: The UUID of your workspace
- **Agent ID**: The UUID of your agent
- **API URL**: The URL where your API is hosted

You can find these in the Streamlit dashboard at `http://localhost:8012`

### 2. Basic HTML Integration

Add this iframe to any HTML page:

```html
<iframe
    src="http://localhost:8058/widget/chat?workspace_id=YOUR_WORKSPACE_ID&agent_id=YOUR_AGENT_ID&agent_name=Support%20Bot"
    width="400px"
    height="600px"
    frameborder="0"
    style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
</iframe>
```

### 3. Laravel Integration

#### Option A: Blade Component (Recommended)

Create a Blade component file: `resources/views/components/chat-widget.blade.php`

```php
@props([
    'workspaceId' => config('services.rag.workspace_id'),
    'agentId' => config('services.rag.agent_id'),
    'agentName' => config('services.rag.agent_name', 'Support Bot'),
    'apiUrl' => config('services.rag.api_url', 'http://localhost:8058'),
    'width' => '400px',
    'height' => '600px'
])

<iframe
    src="{{ $apiUrl }}/widget/chat?workspace_id={{ $workspaceId }}&agent_id={{ $agentId }}&agent_name={{ urlencode($agentName) }}&api_url={{ urlencode($apiUrl) }}"
    width="{{ $width }}"
    height="{{ $height }}"
    frameborder="0"
    style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"
    {{ $attributes }}>
</iframe>
```

Add configuration to `config/services.php`:

```php
'rag' => [
    'api_url' => env('RAG_API_URL', 'http://localhost:8058'),
    'workspace_id' => env('RAG_WORKSPACE_ID'),
    'agent_id' => env('RAG_AGENT_ID'),
    'agent_name' => env('RAG_AGENT_NAME', 'Support Bot'),
],
```

Add to your `.env`:

```env
RAG_API_URL=http://localhost:8058
RAG_WORKSPACE_ID=your-workspace-uuid-here
RAG_AGENT_ID=your-agent-uuid-here
RAG_AGENT_NAME="Support Bot"
```

Use in any Blade template:

```blade
<x-chat-widget />

<!-- Or with custom dimensions -->
<x-chat-widget width="500px" height="700px" />

<!-- Or override specific settings -->
<x-chat-widget
    :workspace-id="$customWorkspaceId"
    :agent-id="$customAgentId"
    agent-name="Custom Support"
/>
```

#### Option B: Include Partial

Create `resources/views/partials/chat-widget.blade.php`:

```blade
<iframe
    src="{{ config('services.rag.api_url') }}/widget/chat?workspace_id={{ config('services.rag.workspace_id') }}&agent_id={{ config('services.rag.agent_id') }}&agent_name={{ urlencode(config('services.rag.agent_name')) }}"
    width="400px"
    height="600px"
    frameborder="0"
    style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
</iframe>
```

Include in any view:

```blade
@include('partials.chat-widget')
```

### 4. Floating Chat Button (Advanced)

For a floating chat button in the corner of your page:

```blade
<!-- Add to your layout -->
<div id="chat-widget-container" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
    <button id="chat-toggle-btn" style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.2s;
    " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
        💬
    </button>

    <div id="chat-widget-frame" style="
        display: none;
        position: absolute;
        bottom: 80px;
        right: 0;
        width: 400px;
        height: 600px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        border-radius: 12px;
        overflow: hidden;
    ">
        <iframe
            src="{{ config('services.rag.api_url') }}/widget/chat?workspace_id={{ config('services.rag.workspace_id') }}&agent_id={{ config('services.rag.agent_id') }}&agent_name={{ urlencode(config('services.rag.agent_name')) }}"
            width="100%"
            height="100%"
            frameborder="0">
        </iframe>
    </div>
</div>

<script>
    const toggleBtn = document.getElementById('chat-toggle-btn');
    const chatFrame = document.getElementById('chat-widget-frame');
    let isOpen = false;

    toggleBtn.addEventListener('click', () => {
        isOpen = !isOpen;
        chatFrame.style.display = isOpen ? 'block' : 'none';
        toggleBtn.textContent = isOpen ? '✕' : '💬';
    });
</script>
```

## URL Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `workspace_id` | Yes | UUID of the workspace | `550e8400-e29b-41d4-a716-446655440000` |
| `agent_id` | Yes | UUID of the agent | `6ba7b810-9dad-11d1-80b4-00c04fd430c8` |
| `agent_name` | No | Display name for the agent | `Support Bot` |
| `api_url` | No | Override API URL (defaults to localhost:8058) | `https://api.example.com` |
| `language` | No | UI language (en or de) | `de` for German, `en` for English (default) |
| `greeting` | No | Custom greeting message | `Hello! How can I help?` |

## ✨ New Features

### Conversation Persistence

The chat widget now **automatically saves conversation history** to the browser's localStorage:

**How it Works**:
- Session ID stored per workspace/agent combination
- Conversations automatically restore on widget reopen
- 60-minute session timeout (configurable on backend)
- "New Chat" button in header to start fresh conversations

**User Experience**:
1. User chats with widget → Session ID saved to localStorage
2. User closes widget/tab/browser → Session persists
3. User returns later → Full conversation history restored
4. After 60 minutes → Session expires, fresh greeting shown

**Technical Details**:
- Storage key format: `rag_chat_session_{workspace_id}_{agent_id}`
- Separate histories for different workspaces/agents
- Graceful fallback if localStorage unavailable
- Backend endpoint: `GET /sessions/{session_id}/messages`

**Privacy & Security**:
- Only session UUID stored (not message content)
- Shared devices: Use "New Chat" button to clear
- Private browsing: Graceful degradation (no persistence)
- Workspace isolation maintained

### Multilingual Support

The widget supports **multiple languages** via the `language` parameter:

**Supported Languages**:
- `en` - English (default)
- `de` - German (Deutsch)

**Translated Elements**:
- Send button: "Send" / "Senden"
- New Chat button: "New Chat" / "Neuer Chat"
- Input placeholder: "Type your message..." / "Geben Sie Ihre Nachricht ein..."
- Loading messages: "Restoring conversation..." / "Konversation wird wiederhergestellt..."
- Confirmation dialogs

**Example (German Widget)**:
```html
<iframe
    src="http://localhost:8058/widget/chat?workspace_id=YOUR_ID&agent_id=YOUR_ID&language=de"
    width="400px"
    height="600px">
</iframe>
```

**Laravel Integration with Language**:
```blade
<x-chat-widget
    :workspace-id="$workspaceId"
    :agent-id="$agentId"
    language="de"
    agent-name="Kundensupport" />
```

## Production Deployment

### 1. Update API URL

For production, update your `.env`:

```env
RAG_API_URL=https://your-production-api.com
```

### 2. CORS Configuration

Ensure your API allows requests from your Laravel app domain. Update `.env` on the API server:

```env
ALLOWED_ORIGINS=https://your-laravel-app.com,https://www.your-laravel-app.com
```

### 3. Security Considerations

- **HTTPS**: Always use HTTPS in production
- **CSP Headers**: Add iframe-src directive if using Content Security Policy
- **API Keys**: Consider implementing API key authentication for production

### 4. CSP Configuration (if needed)

Add to your Laravel middleware or meta tag:

```php
// In your layout
<meta http-equiv="Content-Security-Policy" content="frame-src 'self' https://your-production-api.com;">
```

## Styling Options

### Responsive Design

```blade
<div style="max-width: 100%; overflow: hidden;">
    <x-chat-widget
        width="100%"
        height="600px"
        style="max-width: 400px; margin: 0 auto;" />
</div>
```

### Mobile Optimization

```blade
<x-chat-widget
    :width="request()->userAgent()->isMobile() ? '100%' : '400px'"
    :height="request()->userAgent()->isMobile() ? '500px' : '600px'" />
```

## Example: Customer Support Page

```blade
@extends('layouts.app')

@section('content')
<div class="container py-5">
    <div class="row">
        <div class="col-lg-8">
            <h1>Customer Support</h1>
            <p>Need help? Chat with our AI assistant or browse our FAQ below.</p>

            <!-- FAQ content here -->
        </div>

        <div class="col-lg-4">
            <div class="sticky-top" style="top: 20px;">
                <h3 class="mb-3">Chat Support</h3>
                <x-chat-widget width="100%" height="700px" />
            </div>
        </div>
    </div>
</div>
@endsection
```

## Troubleshooting

### Widget not loading
- Check that workspace_id and agent_id are valid UUIDs
- Verify API is running and accessible
- Check browser console for CORS errors

### No responses
- Ensure workspace has documents ingested
- Verify agent is active in the database
- Check API logs for errors

### Styling issues
- Widget inherits no styles from parent page
- Use iframe parameters to control size
- Consider using CSS transform for positioning

## Getting IDs from Dashboard

1. Go to http://localhost:8012
2. Select "Workspaces" from sidebar
3. Click on your workspace (e.g., "Ihnen")
4. Copy the Workspace ID from the URL or page
5. Note the Agent ID from the agents list

## For Support Bot

Based on your setup, use these parameters:

```env
RAG_WORKSPACE_ID=<your-ihnen-workspace-id>
RAG_AGENT_ID=<your-ihnen-support-bot-agent-id>
RAG_AGENT_NAME="Support Bot"
```

Replace the UUIDs with actual values from your dashboard.
