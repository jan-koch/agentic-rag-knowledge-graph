"""
Modern ChatGPT-style Streamlit Chat Application for Agentic RAG System
Complete redesign with light/dark theme, session management, and responsive design
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import os
from pathlib import Path
import hashlib

# Page Configuration
st.set_page_config(
    page_title="Riddly AI Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/riddly-chat',
        'Report a bug': "https://github.com/your-repo/riddly-chat/issues",
        'About': "Riddly AI - Intelligent Assistant with Hybrid Search"
    }
)

# Initialize Session State
def init_session_state():
    """Initialize session state with default values."""
    defaults = {
        'messages': [],
        'session_id': None,
        'api_url': "https://riddly.kobra-dataworks.de",
        'api_key': "J_qfzc5WsTZ5GgyyOhFGplfI7zoDSFrY0XqTitDadmE",
        'search_type': "hybrid",
        'streaming': True,
        'dark_mode': False,
        'sessions': {},
        'current_session': None,
        'input_key': 0,
        'regenerate_last': False,
        'show_tokens': False,
        'auto_scroll': True,
        'language': 'en'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Custom CSS for ChatGPT-like Interface
def load_custom_css():
    """Load custom CSS for ChatGPT-like styling."""
    
    # Determine theme colors
    if st.session_state.dark_mode:
        theme = {
            'bg': '#212121',
            'sidebar_bg': '#171717',
            'header_bg': '#212121',
            'chat_bg': '#212121',
            'user_msg_bg': '#303030',
            'assistant_msg_bg': '#262626',
            'input_bg': '#303030',
            'input_border': '#404040',
            'text': '#ffffff',
            'text_secondary': '#a0a0a0',
            'border': '#404040',
            'hover': '#404040',
            'accent': '#10a37f',
            'user_avatar': '#6366f1',
            'assistant_avatar': '#10a37f',
            'shadow': 'rgba(0, 0, 0, 0.3)',
            'code_bg': '#1a1a1a',
            'message_hover': '#2a2a2a'
        }
    else:
        theme = {
            'bg': '#ffffff',
            'sidebar_bg': '#f7f7f8',
            'header_bg': '#ffffff',
            'chat_bg': '#ffffff',
            'user_msg_bg': '#f7f7f8',
            'assistant_msg_bg': '#ffffff',
            'input_bg': '#ffffff',
            'input_border': '#d9d9e3',
            'text': '#202123',
            'text_secondary': '#6e6e80',
            'border': '#e5e5e5',
            'hover': '#f0f0f0',
            'accent': '#10a37f',
            'user_avatar': '#6366f1',
            'assistant_avatar': '#10a37f',
            'shadow': 'rgba(0, 0, 0, 0.05)',
            'code_bg': '#f6f6f6',
            'message_hover': '#fafafa'
        }
    
    css = f"""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* CSS Variables */
    :root {{
        --bg: {theme['bg']};
        --sidebar-bg: {theme['sidebar_bg']};
        --header-bg: {theme['header_bg']};
        --chat-bg: {theme['chat_bg']};
        --user-msg-bg: {theme['user_msg_bg']};
        --assistant-msg-bg: {theme['assistant_msg_bg']};
        --input-bg: {theme['input_bg']};
        --input-border: {theme['input_border']};
        --text: {theme['text']};
        --text-secondary: {theme['text_secondary']};
        --border: {theme['border']};
        --hover: {theme['hover']};
        --accent: {theme['accent']};
        --user-avatar: {theme['user_avatar']};
        --assistant-avatar: {theme['assistant_avatar']};
        --shadow: {theme['shadow']};
        --code-bg: {theme['code_bg']};
        --message-hover: {theme['message_hover']};
    }}
    
    /* Global Styles */
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        box-sizing: border-box;
    }}
    
    .stApp {{
        background-color: var(--bg);
        color: var(--text);
        transition: all 0.3s ease;
    }}
    
    /* Hide Streamlit Elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Remove default Streamlit padding and margins */
    .main > div {{
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }}
    
    .block-container {{
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }}
    
    /* Hide empty Streamlit containers */
    .element-container:empty {{
        display: none !important;
    }}
    
    .stMarkdown:empty {{
        display: none !important;
    }}
    
    /* Remove Streamlit's default top spacing */
    [data-testid="stAppViewContainer"] > .main {{
        padding-top: 0 !important;
    }}
    
    [data-testid="stVerticalBlock"] > [style*="flex-direction"] {{
        gap: 0 !important;
    }}
    
    /* First element after header should have no margin */
    .chat-container:first-of-type {{
        margin-top: 50px !important;
    }}
    
    /* Main Container */
    .main {{
        background-color: var(--chat-bg);
        padding: 0;
    }}
    
    .main .block-container {{
        max-width: 100%;
        padding: 0;
        background-color: var(--chat-bg);
    }}
    
    /* Custom Header - Minimal Design */
    .chat-header {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 50px;
        background: var(--header-bg);
        border-bottom: 1px solid var(--border);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 24px;
        z-index: 100;
        backdrop-filter: blur(10px);
        background: rgba(255, 255, 255, 0.95);
    }}
    
    .chat-header.dark {{
        background: rgba(33, 33, 33, 0.95);
    }}
    
    .header-title {{
        font-size: 16px;
        font-weight: 500;
        color: var(--text);
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: -0.3px;
    }}
    
    .header-controls {{
        display: flex;
        gap: 12px;
        align-items: center;
    }}
    
    /* Sidebar Styles */
    .css-1d391kg, [data-testid="stSidebar"] {{
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border);
        padding-top: 50px;
    }}
    
    .sidebar-content {{
        padding: 20px;
    }}
    
    .session-item {{
        padding: 12px 16px;
        margin: 4px 0;
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    
    .session-item:hover {{
        background: var(--hover);
        transform: translateX(2px);
        box-shadow: 0 2px 4px var(--shadow);
    }}
    
    .session-item.active {{
        background: var(--accent);
        color: white;
        border-color: var(--accent);
    }}
    
    .new-chat-btn {{
        width: 100%;
        padding: 12px;
        background: var(--accent);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-bottom: 16px;
    }}
    
    .new-chat-btn:hover {{
        background: #0d8b6b;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(16, 163, 127, 0.3);
    }}
    
    /* Chat Container */
    .chat-container {{
        max-width: 768px;
        margin: 60px auto 0;
        padding: 0 20px 100px;
        min-height: calc(100vh - 160px);
    }}
    
    /* Message Styles */
    .message-wrapper {{
        margin: 16px 0;
        animation: fadeIn 0.3s ease;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .message-content {{
        display: flex;
        gap: 12px;
        padding: 16px 20px;
        border-radius: 12px;
        transition: all 0.2s ease;
    }}
    
    .message-content:hover {{
        background: var(--message-hover);
    }}
    
    .user-message {{
        background: var(--user-msg-bg);
        margin-left: 80px;
        border: 1px solid var(--border);
    }}
    
    .assistant-message {{
        background: var(--assistant-msg-bg);
        margin-right: 80px;
        border: 1px solid var(--border);
    }}
    
    /* Avatar Styles */
    .avatar {{
        width: 36px;
        height: 36px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        color: white;
        flex-shrink: 0;
        box-shadow: 0 2px 4px var(--shadow);
    }}
    
    .user-avatar {{
        background: var(--user-avatar);
    }}
    
    .assistant-avatar {{
        background: var(--assistant-avatar);
    }}
    
    /* Message Text */
    .message-text {{
        flex: 1;
        color: var(--text);
        line-height: 1.7;
        font-size: 15px;
        font-weight: 400;
        letter-spacing: 0.01em;
    }}
    
    .message-text p {{
        margin: 0 0 12px 0;
    }}
    
    .message-text p:last-child {{
        margin-bottom: 0;
    }}
    
    /* Code Blocks */
    .message-text pre {{
        background: var(--code-bg);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 12px;
        overflow-x: auto;
        position: relative;
    }}
    
    .message-text code {{
        background: var(--code-bg);
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 14px;
    }}
    
    /* Copy Button */
    .copy-btn {{
        position: absolute;
        top: 8px;
        right: 8px;
        padding: 4px 8px;
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.2s ease;
    }}
    
    .copy-btn:hover {{
        background: var(--hover);
        transform: scale(1.05);
    }}
    
    /* Message Actions */
    .message-actions {{
        display: flex;
        gap: 8px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--border);
    }}
    
    .action-btn {{
        padding: 4px 12px;
        background: transparent;
        border: 1px solid var(--border);
        border-radius: 4px;
        color: var(--text-secondary);
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    
    .action-btn:hover {{
        background: var(--hover);
        color: var(--text);
        border-color: var(--accent);
    }}
    
    /* Input Container */
    .input-container {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--bg);
        border-top: 1px solid var(--border);
        padding: 16px;
        box-shadow: 0 -2px 10px var(--shadow);
    }}
    
    .input-wrapper {{
        max-width: 768px;
        margin: 0 auto;
        position: relative;
    }}
    
    /* Input Field */
    .stTextArea textarea {{
        background: var(--input-bg);
        border: 1px solid var(--input-border);
        border-radius: 8px;
        color: var(--text);
        padding: 12px 50px 12px 16px;
        font-size: 15px;
        resize: none;
        transition: all 0.2s ease;
        min-height: 50px;
        max-height: 200px;
    }}
    
    .stTextArea textarea:focus {{
        outline: none;
        border-color: var(--accent);
        box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.1);
    }}
    
    /* Send Button */
    .send-button {{
        position: absolute;
        right: 8px;
        bottom: 8px;
        width: 36px;
        height: 36px;
        background: var(--accent);
        border: none;
        border-radius: 6px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    
    .send-button:hover {{
        background: #0d8b6b;
        transform: scale(1.05);
    }}
    
    .send-button:disabled {{
        background: var(--border);
        cursor: not-allowed;
    }}
    
    /* Loading Animation */
    .loading-dots {{
        display: flex;
        gap: 4px;
        padding: 8px;
    }}
    
    .dot {{
        width: 8px;
        height: 8px;
        background: var(--text-secondary);
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out;
    }}
    
    .dot:nth-child(1) {{ animation-delay: -0.32s; }}
    .dot:nth-child(2) {{ animation-delay: -0.16s; }}
    
    @keyframes bounce {{
        0%, 80%, 100% {{
            transform: scale(0.8);
            opacity: 0.5;
        }}
        40% {{
            transform: scale(1);
            opacity: 1;
        }}
    }}
    
    /* Token Counter */
    .token-counter {{
        position: absolute;
        bottom: 52px;
        right: 8px;
        font-size: 12px;
        color: var(--text-secondary);
        background: var(--bg);
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid var(--border);
    }}
    
    /* Settings Panel */
    .settings-panel {{
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }}
    
    .setting-item {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
    }}
    
    .toggle-switch {{
        position: relative;
        width: 48px;
        height: 24px;
        background: var(--border);
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .toggle-switch.active {{
        background: var(--accent);
    }}
    
    .toggle-switch::after {{
        content: '';
        position: absolute;
        width: 20px;
        height: 20px;
        background: white;
        border-radius: 50%;
        top: 2px;
        left: 2px;
        transition: all 0.3s ease;
    }}
    
    .toggle-switch.active::after {{
        transform: translateX(24px);
    }}
    
    /* Welcome Screen - Compact and Elegant */
    .welcome-screen {{
        max-width: 680px;
        margin: 20px auto 40px;
        padding: 0 20px;
    }}
    
    .welcome-title {{
        font-size: 28px;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 12px;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }}
    
    .welcome-subtitle {{
        font-size: 15px;
        color: var(--text-secondary);
        margin-bottom: 32px;
        line-height: 1.5;
        font-weight: 400;
    }}
    
    .feature-pills {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
        margin-bottom: 32px;
    }}
    
    .feature-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 14px;
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: 20px;
        font-size: 13px;
        color: var(--text);
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    
    .feature-pill:hover {{
        background: var(--hover);
        border-color: var(--accent);
        transform: translateY(-1px);
    }}
    
    .feature-pill-icon {{
        font-size: 16px;
    }}
    
    .example-prompts {{
        margin-top: 32px;
    }}
    
    .example-prompts-title {{
        font-size: 13px;
        font-weight: 500;
        color: var(--text-secondary);
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .prompt-suggestions {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 10px;
    }}
    
    .prompt-card {{
        padding: 12px 16px;
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        font-size: 14px;
        color: var(--text);
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: left;
        line-height: 1.4;
    }}
    
    .prompt-card:hover {{
        background: var(--hover);
        border-color: var(--accent);
        transform: translateX(2px);
    }}
    
    .prompt-card-icon {{
        display: inline-block;
        margin-right: 8px;
        color: var(--accent);
    }}
    
    /* Responsive Design */
    @media (max-width: 768px) {{
        .chat-header {{
            padding: 0 16px;
        }}
        
        .chat-container {{
            padding: 70px 12px 90px;
        }}
        
        .user-message, .assistant-message {{
            margin-left: 0;
            margin-right: 0;
        }}
        
        .message-content {{
            padding: 12px;
        }}
        
        .avatar {{
            width: 32px;
            height: 32px;
        }}
        
        .feature-grid {{
            grid-template-columns: 1fr;
        }}
        
        .welcome-title {{
            font-size: 24px;
        }}
        
        .css-1d391kg, [data-testid="stSidebar"] {{
            width: 260px !important;
        }}
    }}
    
    /* Smooth Scrolling */
    html {{
        scroll-behavior: smooth;
    }}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--bg);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--border);
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--text-secondary);
    }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)

# JavaScript for Enhanced Functionality
def load_javascript():
    """Load JavaScript for enhanced functionality."""
    js = """
    <script>
    // Auto-scroll to bottom
    function scrollToBottom() {
        const messages = document.querySelector('.chat-container');
        if (messages) {
            messages.scrollTop = messages.scrollHeight;
        }
    }
    
    // Copy to clipboard
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            // Show feedback
            const btn = event.target;
            const originalText = btn.innerText;
            btn.innerText = 'Copied!';
            setTimeout(() => {
                btn.innerText = originalText;
            }, 2000);
        });
    }
    
    // Initialize on load
    document.addEventListener('DOMContentLoaded', function() {
        scrollToBottom();
        
        // Add copy buttons to code blocks
        document.querySelectorAll('pre').forEach(pre => {
            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.innerText = 'Copy';
            btn.onclick = () => copyToClipboard(pre.innerText);
            pre.appendChild(btn);
        });
    });
    
    // Handle Enter key in textarea
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            const textarea = document.querySelector('textarea');
            if (textarea && textarea === document.activeElement) {
                e.preventDefault();
                // Trigger form submission
                const submitBtn = document.querySelector('[data-testid="stFormSubmitButton"]');
                if (submitBtn) submitBtn.click();
            }
        }
    });
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)

# API Functions
def test_api_connection(api_url: str, api_key: str) -> Dict[str, Any]:
    """Test the API connection."""
    try:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        response = requests.get(
            f"{api_url.rstrip('/')}/health",
            headers=headers,
            timeout=10
        )
        return {
            "status": "connected" if response.status_code == 200 else "error",
            "message": "Connected" if response.status_code == 200 else f"Error: {response.status_code}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_message(message: str, api_url: str, api_key: str, search_type: str, session_id: Optional[str]) -> Dict[str, Any]:
    """Send a message to the API."""
    try:
        payload = {
            "message": message,
            "session_id": session_id,
            "search_type": search_type
        }
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        
        response = requests.post(
            f"{api_url.rstrip('/')}/chat",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_streaming_message(message: str, api_url: str, api_key: str, search_type: str, session_id: Optional[str]):
    """Send a streaming message to the API."""
    try:
        payload = {
            "message": message,
            "session_id": session_id,
            "search_type": search_type
        }
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        
        response = requests.post(
            f"{api_url.rstrip('/')}/chat/stream",
            json=payload,
            headers=headers,
            stream=True,
            timeout=30
        )
        
        return response if response.status_code == 200 else None
    except:
        return None

# UI Components
def render_header():
    """Render the fixed header."""
    header_class = "chat-header dark" if st.session_state.dark_mode else "chat-header"
    st.markdown(f"""
    <div class="{header_class}">
        <div class="header-title">
            <span style="font-size: 18px;">💬</span>
            <span>Riddly AI</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with session management."""
    with st.sidebar:
        # New Chat Button
        if st.button("➕ New Chat", key="new_chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.current_session = st.session_state.session_id
            st.rerun()
        
        st.markdown("---")
        
        # Settings Section
        with st.expander("⚙️ Settings", expanded=False):
            # Theme Toggle
            dark_mode = st.checkbox(
                "Dark Mode",
                value=st.session_state.dark_mode,
                key="dark_mode_toggle"
            )
            if dark_mode != st.session_state.dark_mode:
                st.session_state.dark_mode = dark_mode
                st.rerun()
            
            # Search Type
            st.session_state.search_type = st.selectbox(
                "Search Type",
                options=["hybrid", "vector", "graph"],
                format_func=lambda x: {
                    "hybrid": "🔀 Hybrid (Recommended)",
                    "vector": "📊 Vector Search",
                    "graph": "🕸️ Knowledge Graph"
                }[x],
                index=["hybrid", "vector", "graph"].index(st.session_state.search_type)
            )
            
            # Streaming
            st.session_state.streaming = st.checkbox(
                "Enable Streaming",
                value=st.session_state.streaming
            )
            
            # Auto-scroll
            st.session_state.auto_scroll = st.checkbox(
                "Auto-scroll to Latest",
                value=st.session_state.auto_scroll
            )
            
            # Show Token Count
            st.session_state.show_tokens = st.checkbox(
                "Show Token Counter",
                value=st.session_state.show_tokens
            )
        
        st.markdown("---")
        
        # API Configuration
        with st.expander("🔐 API Configuration", expanded=False):
            st.session_state.api_url = st.text_input(
                "API URL",
                value=st.session_state.api_url,
                type="default"
            )
            
            st.session_state.api_key = st.text_input(
                "API Key",
                value=st.session_state.api_key,
                type="password"
            )
            
            if st.button("Test Connection"):
                with st.spinner("Testing..."):
                    result = test_api_connection(
                        st.session_state.api_url,
                        st.session_state.api_key
                    )
                    if result["status"] == "connected":
                        st.success("✅ Connected")
                    else:
                        st.error(f"❌ {result['message']}")
        
        st.markdown("---")
        
        # Session History
        st.markdown("### 📚 Recent Chats")
        
        # Mock session history (replace with actual sessions)
        if st.session_state.sessions:
            for session_id, session_data in list(st.session_state.sessions.items())[-10:]:
                if st.button(
                    f"💬 {session_data.get('title', 'Untitled Chat')[:30]}...",
                    key=f"session_{session_id}"
                ):
                    st.session_state.current_session = session_id
                    st.session_state.messages = session_data.get('messages', [])
                    st.rerun()
        else:
            st.info("No previous chats")
        
        st.markdown("---")
        
        # Clear Chat History
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Current", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.sessions = {}
                st.session_state.messages = []
                st.rerun()

def render_welcome_screen():
    """Render the welcome screen for new users."""
    st.markdown("""
    <div class="welcome-screen">
        <h1 class="welcome-title">Welcome to Riddly AI</h1>
        <p class="welcome-subtitle">
            Your intelligent assistant powered by hybrid search, combining vector embeddings and knowledge graphs.
        </p>
        
        <div class="feature-pills">
            <div class="feature-pill">
                <span class="feature-pill-icon">🔀</span>
                <span>Hybrid Search</span>
            </div>
            <div class="feature-pill">
                <span class="feature-pill-icon">⚡</span>
                <span>Real-time Streaming</span>
            </div>
            <div class="feature-pill">
                <span class="feature-pill-icon">💾</span>
                <span>Session History</span>
            </div>
            <div class="feature-pill">
                <span class="feature-pill-icon">🎨</span>
                <span>Dark Mode</span>
            </div>
        </div>
        
        <div class="example-prompts">
            <div class="example-prompts-title">Try asking</div>
            <div class="prompt-suggestions">
                <div class="prompt-card">
                    <span class="prompt-card-icon">💡</span>
                    Explain quantum computing in simple terms
                </div>
                <div class="prompt-card">
                    <span class="prompt-card-icon">📊</span>
                    Compare vector and graph databases
                </div>
                <div class="prompt-card">
                    <span class="prompt-card-icon">🔍</span>
                    What are the latest AI trends in 2024?
                </div>
                <div class="prompt-card">
                    <span class="prompt-card-icon">🚀</span>
                    Help me build a RAG application
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_message(role: str, content: str, message_id: str = None):
    """Render a chat message with ChatGPT-style formatting."""
    avatar_class = "user-avatar" if role == "user" else "assistant-avatar"
    message_class = "user-message" if role == "user" else "assistant-message"
    avatar_text = "U" if role == "user" else "AI"
    
    # Generate unique ID for message
    if not message_id:
        message_id = hashlib.md5(f"{role}{content}{datetime.now()}".encode()).hexdigest()[:8]
    
    html = f"""
    <div class="message-wrapper" id="msg-{message_id}">
        <div class="message-content {message_class}">
            <div class="avatar {avatar_class}">{avatar_text}</div>
            <div class="message-text">
                {content}
                <div class="message-actions">
                    <button class="action-btn" onclick="copyToClipboard('{content.replace("'", "\\'")}')">
                        📋 Copy
                    </button>
                    {'''<button class="action-btn" onclick="regenerateResponse()">
                        🔄 Regenerate
                    </button>''' if role == "assistant" else ''}
                </div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def render_loading():
    """Render loading animation."""
    st.markdown("""
    <div class="message-wrapper">
        <div class="message-content assistant-message">
            <div class="avatar assistant-avatar">AI</div>
            <div class="loading-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation)."""
    return len(text.split()) * 1.3

# Main Application
def main():
    """Main application logic."""
    # Initialize session state
    init_session_state()
    
    # Load CSS and JavaScript
    load_custom_css()
    load_javascript()
    
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Main chat area
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display welcome screen or messages
    if not st.session_state.messages:
        render_welcome_screen()
    else:
        # Render all messages
        for i, msg in enumerate(st.session_state.messages):
            render_message(
                msg['role'],
                msg['content'],
                message_id=f"{i}"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Placeholder for streaming responses (placed outside chat container)
    response_placeholder = st.empty()
    
    # Input container at the bottom
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)
    
    with st.form("chat_input", clear_on_submit=True):
        col1, col2 = st.columns([10, 1])
        
        with col1:
            user_input = st.text_area(
                "Message",
                placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)",
                height=50,
                key=f"input_{st.session_state.input_key}",
                label_visibility="collapsed"
            )
        
        with col2:
            submit = st.form_submit_button("➤", use_container_width=True)
        
        # Token counter
        if st.session_state.show_tokens and user_input:
            token_count = estimate_tokens(user_input)
            st.markdown(f'<div class="token-counter">~{token_count} tokens</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle message submission
    if submit and user_input.strip():
        # Add user message
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input.strip(),
            'timestamp': datetime.now().isoformat()
        })
        
        # Clear input by incrementing key
        st.session_state.input_key += 1
        
        # Get response
        with response_placeholder.container():
            render_loading()
            
            if st.session_state.streaming:
                # Streaming response
                response = send_streaming_message(
                    user_input.strip(),
                    st.session_state.api_url,
                    st.session_state.api_key,
                    st.session_state.search_type,
                    st.session_state.session_id
                )
                
                if response:
                    full_response = ""
                    message_placeholder = st.empty()
                    
                    try:
                        for line in response.iter_lines():
                            if line:
                                line = line.decode('utf-8')
                                if line.startswith('data: '):
                                    try:
                                        data = json.loads(line[6:])
                                        if data.get('type') == 'text':
                                            full_response += data.get('content', '')
                                            # Update message in real-time
                                            with message_placeholder.container():
                                                render_message('assistant', full_response)
                                        elif data.get('type') == 'session':
                                            st.session_state.session_id = data.get('session_id')
                                        elif data.get('type') == 'end':
                                            break
                                    except json.JSONDecodeError:
                                        continue
                    except Exception as e:
                        st.error(f"Streaming error: {str(e)}")
                        full_response = "Sorry, an error occurred while streaming the response."
                    
                    # Add assistant message
                    if full_response:
                        st.session_state.messages.append({
                            'role': 'assistant',
                            'content': full_response,
                            'timestamp': datetime.now().isoformat()
                        })
                else:
                    st.error("Failed to get streaming response")
            else:
                # Regular response
                result = send_message(
                    user_input.strip(),
                    st.session_state.api_url,
                    st.session_state.api_key,
                    st.session_state.search_type,
                    st.session_state.session_id
                )
                
                if result['status'] == 'success':
                    response_text = result['data'].get('message', 'No response')
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': response_text,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Update session ID if provided
                    if result['data'].get('session_id'):
                        st.session_state.session_id = result['data']['session_id']
                else:
                    st.error(f"Error: {result['message']}")
        
        # Save session
        if st.session_state.session_id and st.session_state.messages:
            if st.session_state.session_id not in st.session_state.sessions:
                st.session_state.sessions[st.session_state.session_id] = {}
            
            # Get title from first message
            title = st.session_state.messages[0]['content'][:50] if st.session_state.messages else "Untitled"
            
            st.session_state.sessions[st.session_state.session_id] = {
                'title': title,
                'messages': st.session_state.messages,
                'timestamp': datetime.now().isoformat()
            }
        
        # Rerun to update UI
        st.rerun()
    
    # Handle regenerate request
    if st.session_state.regenerate_last and st.session_state.messages:
        # Remove last assistant message
        if st.session_state.messages[-1]['role'] == 'assistant':
            st.session_state.messages.pop()
        
        # Get last user message
        last_user_msg = None
        for msg in reversed(st.session_state.messages):
            if msg['role'] == 'user':
                last_user_msg = msg['content']
                break
        
        if last_user_msg:
            # Regenerate response
            st.session_state.regenerate_last = False
            # Trigger new response generation
            # (Implementation would go here)
            st.rerun()

if __name__ == "__main__":
    main()