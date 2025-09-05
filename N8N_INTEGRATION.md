# n8n Integration Guide

This document explains how to integrate your Agentic RAG Knowledge Graph system with n8n workflows.

## Overview

Two new webhook endpoints have been added to enable seamless integration with n8n:

- **`/n8n/chat`** - Full-featured endpoint with session management and tool tracking
- **`/n8n/simple`** - Simplified endpoint that returns just the answer

## Quick Setup

### Method 1: Using n8n Chat Trigger Node (Recommended)

1. Add a **Chat Trigger** node to your workflow
2. Add an **HTTP Request** node
3. Configure the HTTP Request:
   - **Method**: POST  
   - **URL**: `http://your-rag-server:8058/n8n/chat`
   - **Body**: JSON with `{{ {"chatInput": $json.chatInput, "sessionId": $json.sessionId} }}`

### Method 2: Using n8n Webhook Node

1. Add a **Webhook** node to your workflow
2. Set **HTTP Method** to POST
3. Add an **HTTP Request** node pointing to your RAG system
4. Use the webhook URL as your n8n chat interface

## Endpoint Details

### `/n8n/chat` - Full Integration

**Input Format:**
```json
{
  "chatInput": "Your question here",     // Primary field (from Chat Trigger)
  "message": "Alternative field",        // Alternative message field  
  "question": "Another alternative",     // Another alternative
  "sessionId": "optional-session-id",    // For conversation continuity
  "userId": "user-identifier"            // Optional user tracking
}
```

**Response Format:**
```json
{
  "response": "AI agent response",
  "sessionId": "session-id-for-continuity", 
  "userId": "user-id",
  "toolsUsed": 1,
  "tools": [
    {
      "name": "vector_search_tool",
      "args": {"query": "search terms"}
    }
  ],
  "timestamp": "2025-09-05T02:40:00.000Z"
}
```

### `/n8n/simple` - Basic Integration

**Input Format:**
```json
{
  "message": "Your question here"
}
```

**Response Format:**
```json
{
  "answer": "AI agent response"
}
```

## n8n Workflow Examples

### Example 1: Chat Trigger + HTTP Request

```json
{
  "nodes": [
    {
      "name": "Chat Trigger",
      "type": "@n8n/n8n-nodes-langchain.chatTrigger",
      "parameters": {
        "public": true,
        "mode": "webhook"
      }
    },
    {
      "name": "RAG Query",  
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://localhost:8058/n8n/chat",
        "sendBody": true,
        "contentType": "json",
        "jsonParameters": "{\\"chatInput\\": \\"{{ $json.chatInput }}\\", \\"sessionId\\": \\"{{ $json.sessionId }}\\", \\"userId\\": \\"{{ $json.userId || 'anonymous' }}\\"}"
      }
    }
  ],
  "connections": {
    "Chat Trigger": {
      "main": [[{"node": "RAG Query", "type": "main", "index": 0}]]
    }
  }
}
```

### Example 2: Simple Webhook Integration

```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook", 
      "parameters": {
        "httpMethod": "POST",
        "path": "chat",
        "responseMode": "lastNode"
      }
    },
    {
      "name": "RAG Query",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST", 
        "url": "http://localhost:8058/n8n/simple",
        "sendBody": true,
        "contentType": "json",
        "jsonParameters": "{\\"message\\": \\"{{ $json.message }}\\"}"
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{"node": "RAG Query", "type": "main", "index": 0}]]
    }
  }
}
```

## Advanced Usage

### Session Management

Use the `/n8n/chat` endpoint with consistent `sessionId` values to maintain conversation context:

```json
{
  "chatInput": "Follow-up question",
  "sessionId": "user-123-session",
  "userId": "user-123"  
}
```

### Tool Usage Tracking

The response includes information about which RAG tools were used:

- `vector_search_tool` - Semantic document search
- `graph_search_tool` - Knowledge graph queries  
- `hybrid_search_tool` - Combined vector + graph search
- `list_documents_tool` - Document listing

### Error Handling

Both endpoints return error information in case of failures:

```json
{
  "error": "Error description",
  "timestamp": "2025-09-05T02:40:00.000Z"
}
```

## Testing

Use the provided test script to verify integration:

```bash
python test_n8n_integration.py
```

## Security Considerations

- The RAG system includes CORS middleware allowing all origins
- Consider restricting origins in production environments
- Add authentication/authorization as needed for your use case
- Session data is stored in PostgreSQL database

## Troubleshooting

**Connection Errors:**
- Verify the RAG API server is running on port 8058
- Check network connectivity between n8n and RAG server
- Ensure databases (PostgreSQL + Neo4j) are running

**Missing Responses:**
- Check that required fields (`chatInput`, `message`, or `question`) are provided
- Verify JSON format is correct
- Check server logs for detailed error messages

**Session Issues:**
- Sessions are created automatically if not provided
- Use consistent `sessionId` values for conversation continuity
- Sessions are stored persistently in PostgreSQL