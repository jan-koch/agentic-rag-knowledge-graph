# 🔒 Secure Chat Widget Setup (API Key Authentication)

## Simple Installation

Add these **TWO LINES** to your HTML, right before the closing `</body>` tag:

```html
<script>
  window.IHNEN_CHAT_CONFIG = {
    apiKey: 'apikey_live_576CiGGwTDtycRirommpqag_TSfmneopzY2opPqOw-8'
  };
</script>
<script src="https://botapi.kobra-dataworks.de/static/chat-widget-secure.js"></script>
```

## ✅ What This Does

- **Validates subscription** - Checks if your organization has an active subscription
- **Auto-loads correct agent** - Automatically uses the right chat agent for your workspace
- **Secure** - API key validates workspace access
- **Rate limited** - 120 requests/minute
- **Works anywhere** - Laravel, WordPress, plain HTML

## Your Configuration

**API Key:** `apikey_live_576CiGGwTDtycRirommpqag_TSfmneopzY2opPqOw-8`
**Workspace ID:** `518341a0-ae02-4e28-b161-11ea84a392c1`
**Agent:** Automatically loaded (Ihnen Support Bot)
**Rate Limit:** 120 requests/minute

> ⚠️ **Keep your API key secret!** Don't commit it to public repositories.

## Installation Examples

### Laravel Blade Template

```blade
<!DOCTYPE html>
<html>
<head>
    <title>{{ config('app.name') }}</title>
</head>
<body>
    @yield('content')

    <!-- Secure Chat Widget -->
    <script>
      window.IHNEN_CHAT_CONFIG = {
        apiKey: '{{ env("IHNEN_CHAT_API_KEY") }}'
      };
    </script>
    <script src="https://botapi.kobra-dataworks.de/static/chat-widget-secure.js"></script>
</body>
</html>
```

**In your `.env`:**
```env
IHNEN_CHAT_API_KEY=apikey_live_576CiGGwTDtycRirommpqag_TSfmneopzY2opPqOw-8
```

### Plain HTML

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Website</title>
</head>
<body>
    <h1>Welcome</h1>

    <!-- Secure Chat Widget -->
    <script>
      window.IHNEN_CHAT_CONFIG = {
        apiKey: 'apikey_live_576CiGGwTDtycRirommpqag_TSfmneopzY2opPqOw-8'
      };
    </script>
    <script src="https://botapi.kobra-dataworks.de/static/chat-widget-secure.js"></script>
</body>
</html>
```

### WordPress (footer.php)

```php
<!-- Add before </body> in your theme's footer.php -->
<script>
  window.IHNEN_CHAT_CONFIG = {
    apiKey: '<?php echo get_option('ihnen_chat_api_key'); ?>'
  };
</script>
<script src="https://botapi.kobra-dataworks.de/static/chat-widget-secure.js"></script>
```

## Customization Options

You can customize the widget appearance:

```html
<script>
  window.IHNEN_CHAT_CONFIG = {
    apiKey: 'apikey_live_576CiGGwTDtycRirommpqag_TSfmneopzY2opPqOw-8',
    primaryColor: '#667eea',  // Chat button color
    position: 'bottom-right'   // bottom-right, bottom-left, top-right, top-left
  };
</script>
<script src="https://botapi.kobra-dataworks.de/static/chat-widget-secure.js"></script>
```

## How It Works

1. **Widget loads** → Validates API key with backend
2. **Backend checks:**
   - API key is valid and not expired
   - Organization has active subscription
   - Workspace exists and has active agent
3. **Widget displays** → If all checks pass
4. **Auto-configured** → Uses correct workspace and agent

## JavaScript API

Control the widget programmatically:

```javascript
// Open chat
IhnenChatWidget.open();

// Close chat
IhnenChatWidget.close();

// Toggle chat
IhnenChatWidget.toggle();

// Check if open
if (IhnenChatWidget.isOpen()) {
    console.log('Chat is open');
}

// Reload widget (re-validate and refresh)
IhnenChatWidget.reload();
```

## Error Handling

The widget shows user-friendly errors for:

- ❌ **Missing API key** - "API key is required"
- ❌ **Invalid API key** - "Invalid API key"
- ❌ **Expired API key** - "Invalid or expired API key"
- ❌ **Inactive subscription** - "Subscription is not active"
- ❌ **No active agent** - "No active agent found for workspace"

Errors appear as red notification for 5 seconds.

## Managing API Keys

### Create New API Key

```bash
curl -X POST https://botapi.kobra-dataworks.de/v1/workspaces/518341a0-ae02-4e28-b161-11ea84a392c1/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My New Widget Key",
    "scopes": ["chat", "search"],
    "rate_limit_per_minute": 120
  }'
```

### List API Keys

```bash
curl https://botapi.kobra-dataworks.de/v1/workspaces/518341a0-ae02-4e28-b161-11ea84a392c1/api-keys
```

### Revoke API Key

```bash
curl -X DELETE https://botapi.kobra-dataworks.de/v1/workspaces/518341a0-ae02-4e28-b161-11ea84a392c1/api-keys/KEY_ID
```

> 📝 You can also manage API keys from the Streamlit dashboard at http://localhost:8012

## Security Best Practices

✅ **DO:**
- Store API key in environment variables
- Use different keys for dev/staging/production
- Revoke unused keys
- Monitor API key usage in dashboard

❌ **DON'T:**
- Commit API keys to Git
- Share API keys publicly
- Use same key across multiple environments
- Hard-code API keys in source code

## Rate Limiting

- **Default limit:** 120 requests/minute per API key
- **Custom limits:** Can be set when creating API key
- **429 error:** Returned when rate limit exceeded
- **Resets:** Every minute

## Troubleshooting

### Widget Not Showing

**Check:**
1. API key is correct in `IHNEN_CHAT_CONFIG`
2. Script tags are before `</body>`
3. Browser console for errors (F12)
4. Network tab shows successful validation request

### "Invalid API key" Error

**Solutions:**
- Verify API key is exactly: `apikey_live_576CiGGwTDtycRirommpqag_TSfmneopzY2opPqOw-8`
- Check for extra spaces or quotes
- Ensure key is not revoked
- Generate new key if needed

### "Subscription is not active" Error

**Solutions:**
- Contact admin to activate subscription
- Check organization plan tier
- Verify organization ID is correct

### CORS Errors

**Solutions:**
- Ensure `botapi.kobra-dataworks.de` allows your domain
- Check browser console for specific CORS error
- Contact API administrator

## Switching to Secure Widget

If you're using the basic widget, switch to secure:

**Before (basic):**
```html
<script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
```

**After (secure):**
```html
<script>
  window.IHNEN_CHAT_CONFIG = {
    apiKey: 'apikey_live_576CiGGwTDtycRirommpqag_TSfmneopzY2opPqOw-8'
  };
</script>
<script src="https://botapi.kobra-dataworks.de/static/chat-widget-secure.js"></script>
```

## Support

For help or issues:
- Check API logs: `sudo journalctl -u rag-api -f`
- View dashboard: http://localhost:8012
- Documentation: See other guides in repository
