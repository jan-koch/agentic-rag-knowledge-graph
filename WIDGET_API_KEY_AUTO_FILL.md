# Widget Embed API Key Auto-Fill Feature

## Overview

The Widget Embed page now automatically populates the API key in the embed code when you navigate from the API Keys page after creating a new key. This eliminates manual copy-paste steps and reduces errors.

## How It Works

### User Workflow

1. **Create API Key** (🔑 API Keys page)
   - Fill out the API key creation form
   - Click "Create API Key"
   - The full API key is displayed (only shown once!)

2. **Quick Action Button**
   - After creation, click the new "🔌 Use in Widget Embed" button
   - This navigates to the Widget Embed page with `?api_key=YOUR_KEY` parameter

3. **Auto-Filled Embed Code** (🔌 Widget Embed page)
   - The page detects the API key from the URL
   - Shows green success message: "✅ API key pre-filled!"
   - The embed code contains the actual API key (not a placeholder)
   - Ready to copy and paste into your website

### Technical Implementation

#### Widget Embed Page (webui.py lines 1101-1145)

```python
# Check for API key passed via URL parameter
query_params = st.query_params
prefilled_api_key = query_params.get("api_key", None)

if prefilled_api_key:
    # Use the prefilled key
    api_key_value = prefilled_api_key
    st.success("✅ API key pre-filled! You can copy the complete embed code below.")
else:
    # Fall back to placeholder
    api_key_value = 'YOUR_API_KEY_HERE'
    st.warning("⚠️ Floating widget requires an API key. Generate one in the API Keys page first.")
```

#### API Keys Page (webui.py lines 957-972)

```python
# After successful API key creation
st.markdown("### ⚡ Quick Actions")
widget_url = f"?api_key={key_data['key']}"
st.link_button(
    "🔌 Use in Widget Embed",
    url=widget_url,
    help="Navigate to Widget Embed page with this API key pre-filled",
    use_container_width=True,
    type="primary"
)
```

## Generated Embed Code Examples

### With Auto-Filled API Key

```html
<!-- Support Bot Floating Chat Widget -->
<script>
  window.RAG_CHAT_CONFIG = {
    apiKey: 'sk_live_abc123def456ghi789jkl', // ✅ Pre-filled
    workspaceId: '550e8400-e29b-41d4-a716-446655440000',
    agentId: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    agentName: 'Support Bot',
    greeting: 'Hi! I\'m Support Bot. How can I help?',
    position: 'bottom-right',
    theme: 'light'
  };
</script>
<script src="https://botapi.kobra-dataworks.de/static/chat-widget-secure.js"></script>
```

### Without Auto-Fill (Manual Entry)

```html
<!-- Support Bot Floating Chat Widget -->
<script>
  window.RAG_CHAT_CONFIG = {
    apiKey: 'YOUR_API_KEY_HERE', // Replace with actual API key
    workspaceId: '550e8400-e29b-41d4-a716-446655440000',
    agentId: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    agentName: 'Support Bot',
    greeting: 'Hi! I\'m Support Bot. How can I help?',
    position: 'bottom-right',
    theme: 'light'
  };
</script>
<script src="https://botapi.kobra-dataworks.de/static/chat-widget-secure.js"></script>
```

## UI/UX Indicators

### API Keys Page
- **After creation**: Shows "⚡ Quick Actions" section
- **Button**: "🔌 Use in Widget Embed" (primary button, full width)
- **Caption**: "💡 The API key will be automatically filled in the widget embed code"

### Widget Embed Page

#### With Pre-Filled Key
- **Success banner**: "✅ API key pre-filled! You can copy the complete embed code below."
- **Info message**: "🔒 Note: Your API key is embedded in the code below. Keep it secure!"
- **Code comment**: `// ✅ Pre-filled` next to apiKey field

#### Without Pre-Filled Key
- **Warning banner**: "⚠️ Floating widget requires an API key. Generate one in the API Keys page first."
- **Info message**: "🔒 Note: Replace 'YOUR_API_KEY_HERE' with your actual API key. The key is only shown once at creation time."
- **Code comment**: `// Replace with actual API key` next to apiKey field

## Security Considerations

1. **One-Time Display**: API keys are still only shown once at creation (unchanged)
2. **URL Parameter**: The key is passed via URL parameter only within the same Streamlit session
3. **No Storage**: The key is not stored anywhere after navigation
4. **User Responsibility**: Users must still copy and secure their keys
5. **HTTPS**: Ensure production deployment uses HTTPS to protect keys in transit

## Testing

### Unit Tests (test_widget_api_key.py)

```bash
python3 test_widget_api_key.py
```

Tests cover:
- ✅ With prefilled API key
- ✅ Without prefilled API key (None)
- ✅ Without prefilled API key (empty string)

### Manual Testing Steps

1. Start the Streamlit app:
   ```bash
   streamlit run webui.py --server.port 8012
   ```

2. Navigate to: http://localhost:8012

3. Test the workflow:
   - Go to "🔑 API Keys" page
   - Create a new API key
   - Click "🔌 Use in Widget Embed" button
   - Verify:
     * URL contains `?api_key=sk_...`
     * Green success message appears
     * Embed code shows actual key (not placeholder)
     * Comment shows "// ✅ Pre-filled"

4. Test fallback behavior:
   - Navigate directly to "🔌 Widget Embed" (without api_key parameter)
   - Verify:
     * Warning message appears
     * Embed code shows "YOUR_API_KEY_HERE"
     * Comment shows "// Replace with actual API key"

## Backward Compatibility

- ✅ Existing workflow (manual copy-paste) still works
- ✅ No breaking changes to API or data models
- ✅ Gracefully degrades when no API key provided
- ✅ All existing functionality preserved

## Future Enhancements

Potential improvements for future versions:

1. **Clipboard API**: Auto-copy embed code to clipboard when key is pre-filled
2. **Key Masking**: Show partial key in dropdown (e.g., `sk_****7890`)
3. **Multiple Keys**: Support selecting from multiple workspace keys
4. **Expiration Warning**: Show warning if navigating with an expired key
5. **Domain Restrictions**: Add UI for restricting keys to specific domains

## Files Modified

1. **webui.py** (2 sections updated)
   - Lines 1101-1145: Widget Embed page URL parameter handling
   - Lines 957-972: API Keys page quick action button

2. **test_widget_api_key.py** (new file)
   - Unit tests for auto-fill logic

3. **WIDGET_API_KEY_AUTO_FILL.md** (this file)
   - Documentation and usage guide

## Support

For issues or questions:
- Check session log: `.claude-sessions/session_*.log`
- Review test output: `python3 test_widget_api_key.py`
- See main documentation: `WEBUI_GUIDE.md`
