# Ihnen Support Bot - Laravel Integration

## Your Configuration

**Workspace ID:** `518341a0-ae02-4e28-b161-11ea84a392c1`
**Agent ID:** `40ab91a7-a111-48ea-b4cd-f831efeaeff2`
**Agent Name:** `Ihnen Support Bot`
**API URL (production):** `https://botapi.kobra-dataworks.de`
**API URL (local):** `http://localhost:8058`

## Quick Setup for Laravel

### 1. Add to `.env`

**For Production:**
```env
RAG_API_URL=https://botapi.kobra-dataworks.de
RAG_WORKSPACE_ID=518341a0-ae02-4e28-b161-11ea84a392c1
RAG_AGENT_ID=40ab91a7-a111-48ea-b4cd-f831efeaeff2
RAG_AGENT_NAME="Ihnen Support Bot"
```

**For Local Development:**
```env
RAG_API_URL=http://localhost:8058
RAG_WORKSPACE_ID=518341a0-ae02-4e28-b161-11ea84a392c1
RAG_AGENT_ID=40ab91a7-a111-48ea-b4cd-f831efeaeff2
RAG_AGENT_NAME="Ihnen Support Bot"
```

### 2. Update `config/services.php`

Add this to your services configuration:

```php
<?php

return [
    // ... existing services ...

    'rag' => [
        'api_url' => env('RAG_API_URL', 'http://localhost:8058'),
        'workspace_id' => env('RAG_WORKSPACE_ID'),
        'agent_id' => env('RAG_AGENT_ID'),
        'agent_name' => env('RAG_AGENT_NAME', 'Support Bot'),
    ],
];
```

### 3. Create Blade Component

Create file: `resources/views/components/ihnen-chat.blade.php`

```blade
@props([
    'width' => '400px',
    'height' => '600px'
])

<iframe
    src="{{ config('services.rag.api_url') }}/widget/chat?workspace_id={{ config('services.rag.workspace_id') }}&agent_id={{ config('services.rag.agent_id') }}&agent_name={{ urlencode(config('services.rag.agent_name')) }}&api_url={{ urlencode(config('services.rag.api_url')) }}"
    width="{{ $width }}"
    height="{{ $height }}"
    frameborder="0"
    style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"
    {{ $attributes }}>
</iframe>
```

### 4. Use in Your Views

#### Simple Inline Chat

```blade
<div class="container">
    <h2>Need Help?</h2>
    <x-ihnen-chat />
</div>
```

#### Floating Chat Button

Add to your layout (e.g., `resources/views/layouts/app.blade.php`):

```blade
<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <!-- ... your head content ... -->
</head>
<body>
    <!-- ... your body content ... -->

    <!-- Floating Chat Widget -->
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
            display: flex;
            align-items: center;
            justify-content: center;
        ">
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
            <x-ihnen-chat width="100%" height="100%" />
        </div>
    </div>

    <script>
        const toggleBtn = document.getElementById('chat-toggle-btn');
        const chatFrame = document.getElementById('chat-widget-frame');
        let isOpen = false;

        toggleBtn.addEventListener('click', () => {
            isOpen = !isOpen;
            chatFrame.style.display = isOpen ? 'block' : 'none';
            toggleBtn.innerHTML = isOpen ? '✕' : '💬';
            toggleBtn.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)';
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isOpen) {
                isOpen = false;
                chatFrame.style.display = 'none';
                toggleBtn.innerHTML = '💬';
                toggleBtn.style.transform = 'rotate(0deg)';
            }
        });
    </script>
</body>
</html>
```

#### Support Page Example

Create `resources/views/support.blade.php`:

```blade
@extends('layouts.app')

@section('content')
<div class="container py-5">
    <div class="row">
        <div class="col-lg-8">
            <h1>Plattform Support</h1>
            <p>Benötigen Sie Hilfe mit unserer KI-Plattform? Chatten Sie mit unserem Support-Bot oder durchsuchen Sie die FAQ unten.</p>

            <div class="card mt-4">
                <div class="card-header">
                    <h3>Häufig gestellte Fragen</h3>
                </div>
                <div class="card-body">
                    <!-- Your FAQ content -->
                </div>
            </div>
        </div>

        <div class="col-lg-4">
            <div class="sticky-top" style="top: 20px;">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h4 class="mb-0">💬 Chat Support</h4>
                    </div>
                    <div class="card-body p-0">
                        <x-ihnen-chat width="100%" height="700px" />
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
@endsection
```

Add route in `routes/web.php`:

```php
Route::get('/support', function () {
    return view('support');
})->name('support');
```

## Testing Locally

1. Make sure your RAG API is running:
   ```bash
   cd /var/www/agentic-rag-knowledge-graph
   source venv/bin/activate
   python -m agent.api
   ```

2. Visit your Laravel app and you should see the chat widget!

## Production Deployment

### 1. Update `.env` for Production

Your production API is at: **botapi.kobra-dataworks.de**

```env
RAG_API_URL=https://botapi.kobra-dataworks.de
RAG_WORKSPACE_ID=518341a0-ae02-4e28-b161-11ea84a392c1
RAG_AGENT_ID=40ab91a7-a111-48ea-b4cd-f831efeaeff2
RAG_AGENT_NAME="Ihnen Support Bot"
```

### 2. Configure CORS on API Server

On the API server (botapi.kobra-dataworks.de), update `.env`:

```env
ALLOWED_ORIGINS=https://your-laravel-domain.com,https://www.your-laravel-domain.com
```

**Note:** Replace `your-laravel-domain.com` with your actual Laravel application domain.

### 3. Use HTTPS

Ensure both your Laravel app and RAG API use HTTPS in production.

### 4. Optional: Add CSP Headers

In your Laravel app, if using Content Security Policy, add:

```php
// In App\Http\Middleware\SetSecurityHeaders or similar
$response->headers->set('Content-Security-Policy',
    "frame-src 'self' https://botapi.kobra-dataworks.de;"
);
```

## Direct HTML (No Laravel)

If you want to test without Laravel components:

**Production:**
```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ihnen Support</title>
</head>
<body>
    <h1>Plattform Support</h1>

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

**Local Development:**
```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ihnen Support</title>
</head>
<body>
    <h1>Plattform Support</h1>

    <iframe
        src="http://localhost:8058/widget/chat?workspace_id=518341a0-ae02-4e28-b161-11ea84a392c1&agent_id=40ab91a7-a111-48ea-b4cd-f831efeaeff2&agent_name=Ihnen%20Support%20Bot&api_url=http://localhost:8058"
        width="400px"
        height="600px"
        frameborder="0"
        style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    </iframe>
</body>
</html>
```

## Troubleshooting

### Widget shows "Missing workspace_id or agent_id"
- Double-check your `.env` values match exactly
- Run `php artisan config:clear` after changing .env
- Verify the IDs are valid UUIDs (no spaces or quotes)

### CORS Errors in Console
- Update `ALLOWED_ORIGINS` on API server
- Include both `http://` and `https://` versions if needed
- Clear browser cache

### No Response from Bot
- Check API is running: `curl http://localhost:8058/health`
- Verify documents are ingested in workspace
- Check API logs for errors

### iframe Not Loading
- Ensure API URL is accessible from Laravel app
- Check network tab in browser DevTools
- Verify firewall rules allow connection

## Widget URL Parameters Reference

**Production URL:**
```
https://botapi.kobra-dataworks.de/widget/chat?workspace_id=518341a0-ae02-4e28-b161-11ea84a392c1&agent_id=40ab91a7-a111-48ea-b4cd-f831efeaeff2&agent_name=Ihnen%20Support%20Bot&api_url=https://botapi.kobra-dataworks.de
```

**Local Development URL:**
```
http://localhost:8058/widget/chat?workspace_id=518341a0-ae02-4e28-b161-11ea84a392c1&agent_id=40ab91a7-a111-48ea-b4cd-f831efeaeff2&agent_name=Ihnen%20Support%20Bot&api_url=http://localhost:8058
```

**Parameters:**
- `workspace_id` (required): `518341a0-ae02-4e28-b161-11ea84a392c1`
- `agent_id` (required): `40ab91a7-a111-48ea-b4cd-f831efeaeff2`
- `agent_name` (optional): URL-encoded agent display name
- `api_url` (optional): Override API URL if different from widget host
