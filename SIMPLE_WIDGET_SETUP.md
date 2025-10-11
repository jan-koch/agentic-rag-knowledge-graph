# 🚀 Simple Chat Widget Setup (One-Line Install)

## Installation - Just Copy & Paste!

Add this **ONE LINE** to your HTML, right before the closing `</body>` tag:

```html
<script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
```

That's it! A chat bubble will appear in the bottom-right corner of your page.

## Examples

### Laravel Blade Template

```blade
<!DOCTYPE html>
<html>
<head>
    <title>My Laravel App</title>
</head>
<body>
    <!-- Your content here -->

    <!-- Add widget - one line! -->
    <script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
</body>
</html>
```

### Plain HTML

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Website</title>
</head>
<body>
    <h1>Welcome to my site</h1>

    <!-- Add widget - one line! -->
    <script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
</body>
</html>
```

### WordPress (in footer.php)

```php
<!-- Add before </body> in your theme's footer.php -->
<script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
```

### Anywhere Else

Just paste this before `</body>`:
```html
<script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
```

## What You Get

✅ Chat bubble in bottom-right corner
✅ Opens full chat window on click
✅ Closes with X button or ESC key
✅ Mobile responsive
✅ Session continuity (conversations persist)
✅ Works on any website/app

## JavaScript API (Optional)

If you want to control the widget programmatically:

```javascript
// Open the chat
RagChatWidget.open();

// Close the chat
RagChatWidget.close();

// Toggle the chat
RagChatWidget.toggle();

// Check if open
if (RagChatWidget.isOpen()) {
    console.log('Chat is open!');
}
```

## Examples of Programmatic Control

### Open chat when user clicks a button

```html
<button onclick="RagChatWidget.open()">Need Help?</button>
<script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
```

### Auto-open chat after 5 seconds

```html
<script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
<script>
    setTimeout(() => {
        RagChatWidget.open();
    }, 5000);
</script>
```

### Open chat from a link

```html
<a href="#" onclick="RagChatWidget.open(); return false;">
    Chat with Support
</a>
<script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
```

## Testing

### Local Testing (Before Production)

For local development, create a test HTML file:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chat Widget Test</title>
</head>
<body>
    <h1>Chat Widget Test</h1>
    <p>Look for the chat bubble in the bottom-right corner!</p>

    <script src="http://localhost:8058/static/chat-widget.js"></script>
</body>
</html>
```

Save as `test.html` and open in your browser.

### Production Testing

Once deployed to botapi.kobra-dataworks.de, use:

```html
<script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
```

## Customization (Advanced)

The default widget is configured for Support Bot. If you need to customize:

1. Download the widget: `curl https://botapi.kobra-dataworks.de/static/chat-widget.js > custom-widget.js`
2. Edit the `config` object at the top
3. Host on your own server
4. Use your custom version instead

## Troubleshooting

### Widget Not Showing Up

**Check:**
- Script tag is before `</body>`
- No JavaScript errors in browser console (F12)
- URL is correct: `https://botapi.kobra-dataworks.de/static/chat-widget.js`
- Not blocked by ad blocker

### CORS Errors

**Solution:**
- Make sure botapi.kobra-dataworks.de has CORS enabled
- Add your domain to `ALLOWED_ORIGINS` in API `.env`

### Widget Appears But No Response

**Check:**
- API is running: `curl https://botapi.kobra-dataworks.de/health`
- Workspace has documents
- Agent is active

## Support

Need help? Contact your developer or check the full documentation in:
- `CHAT_WIDGET_INTEGRATION.md` - Detailed integration guide
- `PRODUCTION_SETUP.md` - Server setup and deployment
- `LARAVEL_INTEGRATION.md` - Laravel-specific guide
