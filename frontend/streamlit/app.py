"""
Streamlit Chat Application with Tailwind CSS
Clean, modern ChatGPT-style interface using Tailwind utility classes
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

# Page Configuration
st.set_page_config(
    page_title="Riddly AI",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
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
        'input_counter': 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Tailwind CSS and Custom Styles
def load_tailwind_css():
    """Load Tailwind CSS via CDN with custom configuration."""
    
    dark_mode_class = "dark" if st.session_state.dark_mode else ""
    
    st.markdown(f"""
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    animation: {{
                        'fade-in': 'fadeIn 0.5s ease-in-out',
                        'slide-up': 'slideUp 0.3s ease-out',
                        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                    }},
                    keyframes: {{
                        fadeIn: {{
                            '0%': {{ opacity: '0' }},
                            '100%': {{ opacity: '1' }},
                        }},
                        slideUp: {{
                            '0%': {{ transform: 'translateY(10px)', opacity: '0' }},
                            '100%': {{ transform: 'translateY(0)', opacity: '1' }},
                        }}
                    }}
                }}
            }}
        }}
    </script>
    
    <style>
        /* Root element dark mode */
        .stApp {{
            background: transparent;
        }}
        
        /* Hide Streamlit defaults */
        #MainMenu, footer, header {{
            display: none !important;
        }}
        
        /* Remove Streamlit padding */
        .main > div {{
            padding: 0 !important;
        }}
        
        .block-container {{
            padding: 0 !important;
            max-width: 100% !important;
        }}
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background: transparent !important;
            padding-top: 0 !important;
        }}
        
        [data-testid="stSidebar"] > div {{
            background: transparent !important;
        }}
        
        /* Message hover effects */
        .message-bubble {{
            transition: all 0.2s ease;
        }}
        
        .message-bubble:hover {{
            transform: translateX(2px);
        }}
        
        /* Smooth scrolling */
        html {{
            scroll-behavior: smooth;
        }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #cbd5e1;
            border-radius: 3px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #94a3b8;
        }}
        
        .dark ::-webkit-scrollbar-thumb {{
            background: #475569;
        }}
        
        .dark ::-webkit-scrollbar-thumb:hover {{
            background: #64748b;
        }}
        
        /* Input field focus */
        textarea:focus {{
            outline: none !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5) !important;
        }}
    </style>
    
    <div class="{dark_mode_class}">
    """, unsafe_allow_html=True)

# API Functions
def test_connection(api_url: str, api_key: str) -> bool:
    """Test API connection."""
    try:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        response = requests.get(f"{api_url.rstrip('/')}/health", headers=headers, timeout=5)
        return response.status_code == 200
    except:
        return False

def send_message(message: str, api_url: str, api_key: str, search_type: str, session_id: Optional[str]) -> Dict[str, Any]:
    """Send message to API."""
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
    """Send streaming message to API."""
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
    """Render minimal header."""
    return """
    <div class="fixed top-0 left-0 right-0 h-14 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 z-50 backdrop-blur-lg bg-opacity-90">
        <div class="flex items-center justify-center h-full px-4">
            <div class="flex items-center space-x-2">
                <span class="text-2xl">💬</span>
                <span class="text-lg font-semibold text-gray-900 dark:text-white">Riddly AI</span>
            </div>
        </div>
    </div>
    """

def render_sidebar():
    """Render clean sidebar with Tailwind styling."""
    with st.sidebar:
        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()
        
        st.divider()
        
        # Settings Section
        with st.expander("⚙️ Settings", expanded=False):
            # Dark Mode Toggle
            dark_mode = st.checkbox("🌙 Dark Mode", value=st.session_state.dark_mode)
            if dark_mode != st.session_state.dark_mode:
                st.session_state.dark_mode = dark_mode
                st.rerun()
            
            # Search Type Selection
            st.session_state.search_type = st.selectbox(
                "🔍 Search Type",
                ["hybrid", "vector", "graph"],
                format_func=lambda x: {
                    "hybrid": "🔀 Hybrid (Recommended)",
                    "vector": "📊 Vector Search",
                    "graph": "🕸️ Knowledge Graph"
                }[x],
                index=["hybrid", "vector", "graph"].index(st.session_state.search_type)
            )
            
            # Streaming Toggle
            st.session_state.streaming = st.checkbox(
                "⚡ Enable Streaming", 
                value=st.session_state.streaming
            )
        
        # API Configuration
        with st.expander("🔐 API Configuration", expanded=False):
            st.session_state.api_url = st.text_input(
                "API URL", 
                value=st.session_state.api_url
            )
            st.session_state.api_key = st.text_input(
                "API Key", 
                value=st.session_state.api_key, 
                type="password"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Test", use_container_width=True):
                    if test_connection(st.session_state.api_url, st.session_state.api_key):
                        st.success("✅ Connected")
                    else:
                        st.error("❌ Failed")
            
            with col2:
                connection_status = "🟢" if test_connection(st.session_state.api_url, st.session_state.api_key) else "🔴"
                st.write(f"Status: {connection_status}")
        
        st.divider()
        
        # Chat History
        st.subheader("📚 Chat History")
        
        if st.session_state.sessions:
            for sid, session in list(st.session_state.sessions.items())[-5:]:
                title = session.get('title', 'Untitled Chat')
                if len(title) > 30:
                    title = title[:30] + "..."
                
                if st.button(f"💬 {title}", key=f"load_{sid}", use_container_width=True):
                    st.session_state.messages = session.get('messages', [])
                    st.session_state.session_id = sid
                    st.rerun()
        else:
            st.info("💡 No previous chats")
        
        # Clear History
        if st.session_state.sessions:
            if st.button("🗑️ Clear All History", use_container_width=True, type="secondary"):
                st.session_state.sessions = {}
                st.success("History cleared!")
                st.rerun()

def render_welcome():
    """Render welcome screen with Tailwind."""
    st.markdown("""
    <div class="flex flex-col items-center justify-center min-h-[60vh] px-4 animate-fade-in">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-3">Welcome to Riddly AI</h1>
        <p class="text-gray-600 dark:text-gray-400 text-center max-w-md mb-8">
            Your intelligent assistant powered by hybrid search, combining vector embeddings and knowledge graphs.
        </p>
        
        <div class="flex flex-wrap gap-2 justify-center mb-8">
            <span class="px-3 py-1.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium">
                🔀 Hybrid Search
            </span>
            <span class="px-3 py-1.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full text-sm font-medium">
                ⚡ Real-time Streaming
            </span>
            <span class="px-3 py-1.5 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full text-sm font-medium">
                💾 Session History
            </span>
            <span class="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-full text-sm font-medium">
                🎨 Dark Mode
            </span>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full">
            <div class="group p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-all duration-200 hover:shadow-md border hover:border-blue-300">
                <div class="flex items-start space-x-3">
                    <span class="text-blue-500 mt-0.5">💡</span>
                    <p class="text-sm text-gray-700 dark:text-gray-300">Explain quantum computing in simple terms</p>
                </div>
            </div>
            <div class="group p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-all duration-200 hover:shadow-md border hover:border-green-300">
                <div class="flex items-start space-x-3">
                    <span class="text-green-500 mt-0.5">📊</span>
                    <p class="text-sm text-gray-700 dark:text-gray-300">Compare vector and graph databases</p>
                </div>
            </div>
            <div class="group p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-all duration-200 hover:shadow-md border hover:border-purple-300">
                <div class="flex items-start space-x-3">
                    <span class="text-purple-500 mt-0.5">🔍</span>
                    <p class="text-sm text-gray-700 dark:text-gray-300">What are the latest AI trends?</p>
                </div>
            </div>
            <div class="group p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-all duration-200 hover:shadow-md border hover:border-orange-300">
                <div class="flex items-start space-x-3">
                    <span class="text-orange-500 mt-0.5">🚀</span>
                    <p class="text-sm text-gray-700 dark:text-gray-300">Help me build a RAG application</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_message(role: str, content: str, timestamp: str = None):
    """Render a message with Tailwind styling and proper HTML rendering."""
    import html
    import re
    
    is_user = role == "user"
    
    if not timestamp:
        timestamp = datetime.now().strftime("%H:%M")
    
    alignment = "justify-end" if is_user else "justify-start"
    bg_color = "bg-blue-500 text-white" if is_user else "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
    avatar = "👤" if is_user else "🤖"
    
    # Convert markdown to HTML if this is an assistant message
    if not is_user:
        # Basic markdown to HTML conversion for common patterns
        # Bold text
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        
        # Headers
        content = re.sub(r'^### (.*?)$', r'<h3 class="text-lg font-semibold mt-3 mb-2">\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'<h2 class="text-xl font-semibold mt-4 mb-2">\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.*?)$', r'<h1 class="text-2xl font-bold mt-4 mb-3">\1</h1>', content, flags=re.MULTILINE)
        
        # Lists (simple conversion)
        content = re.sub(r'^- (.*?)$', r'<li class="ml-4">\1</li>', content, flags=re.MULTILINE)
        content = re.sub(r'^(\d+)\. (.*?)$', r'<li class="ml-4">\2</li>', content, flags=re.MULTILINE)
        
        # Wrap consecutive <li> elements in <ul>
        content = re.sub(r'(<li.*?</li>(?:\s*<li.*?</li>)*)', r'<ul class="list-disc ml-4 mb-2">\1</ul>', content, flags=re.DOTALL)
        
        # Code blocks (basic)
        content = re.sub(r'`([^`]+)`', r'<code class="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-sm font-mono">\1</code>', content)
        
        # Line breaks
        content = re.sub(r'\n', '<br>', content)
    else:
        # For user messages, just escape HTML and preserve line breaks
        content = html.escape(content)
        content = re.sub(r'\n', '<br>', content)
    
    st.markdown(f"""
    <div class="flex {alignment} mb-4 animate-slide-up">
        <div class="flex items-start space-x-2 max-w-2xl">
            {'<div class="order-2">' if is_user else ''}
            <div class="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-sm">
                {avatar}
            </div>
            {'</div>' if is_user else ''}
            
            <div class="message-bubble {bg_color} rounded-2xl px-4 py-2.5 shadow-sm {'order-1' if is_user else ''}">
                <div class="text-sm {'whitespace-pre-wrap' if is_user else ''}">{content}</div>
                <div class="text-xs {'text-blue-100' if is_user else 'text-gray-500 dark:text-gray-400'} mt-1">
                    {timestamp}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_loading():
    """Render loading indicator."""
    st.markdown("""
    <div class="flex justify-start mb-4">
        <div class="flex items-start space-x-2 max-w-2xl">
            <div class="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-sm">
                🤖
            </div>
            <div class="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-3 shadow-sm">
                <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main Application
def main():
    """Main application."""
    # Initialize
    init_session_state()
    
    # Load Tailwind CSS
    load_tailwind_css()
    
    # Create main layout container
    st.markdown(f"""
    <div class="min-h-screen bg-white dark:bg-gray-900 transition-colors duration-200">
        {render_header()}
        <div class="pt-14 pb-24">
            <div class="max-w-4xl mx-auto px-4 py-6" id="chat-messages">
    """, unsafe_allow_html=True)
    
    # Render sidebar
    render_sidebar()
    
    # Main chat content
    if not st.session_state.messages:
        render_welcome()
    else:
        for msg in st.session_state.messages:
            render_message(
                msg['role'],
                msg['content'],
                msg.get('timestamp', datetime.now().strftime("%H:%M"))
            )
    
    # Close chat messages container
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Response placeholder (outside main container to avoid layout issues)
    response_placeholder = st.empty()
    
    # Input area
    st.markdown("""
        <div class="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4">
            <div class="max-w-4xl mx-auto">
    """, unsafe_allow_html=True)
    
    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([11, 1])
        
        with col1:
            user_input = st.text_area(
                "Message",
                placeholder="Type your message... (Press Ctrl+Enter to send)",
                height=50,
                key=f"input_{st.session_state.input_counter}",
                label_visibility="collapsed"
            )
        
        with col2:
            submit = st.form_submit_button(
                "➤",
                use_container_width=True,
                help="Send message"
            )
    
    # Close input area containers
    st.markdown("</div></div></div>", unsafe_allow_html=True)
    
    # Handle message submission
    if submit and user_input.strip():
        # Add user message
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input.strip(),
            'timestamp': datetime.now().strftime("%H:%M")
        })
        
        # Increment input counter to clear field
        st.session_state.input_counter += 1
        
        # Generate session ID if needed
        if not st.session_state.session_id:
            st.session_state.session_id = str(uuid.uuid4())
        
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
                        full_response = "Sorry, an error occurred."
                    
                    if full_response:
                        st.session_state.messages.append({
                            'role': 'assistant',
                            'content': full_response,
                            'timestamp': datetime.now().strftime("%H:%M")
                        })
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
                        'timestamp': datetime.now().strftime("%H:%M")
                    })
                    
                    if result['data'].get('session_id'):
                        st.session_state.session_id = result['data']['session_id']
                else:
                    st.error(f"Error: {result['message']}")
        
        # Save session
        if st.session_state.session_id and st.session_state.messages:
            # Get title from first message
            title = st.session_state.messages[0]['content'][:50] if st.session_state.messages else "Untitled"
            
            st.session_state.sessions[st.session_state.session_id] = {
                'title': title,
                'messages': st.session_state.messages,
                'timestamp': datetime.now().isoformat()
            }
        
        # Rerun to update
        st.rerun()

if __name__ == "__main__":
    main()