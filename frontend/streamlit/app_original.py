"""
Moderne Streamlit-Chat-Anwendung für Agentic RAG System
Modern Streamlit Chat Application for Agentic RAG System (German UI)
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Konfiguration
st.set_page_config(
    page_title="🧩 Riddly Chat Agent",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed" if st.session_state.get('is_mobile', False) else "expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/riddly-chat',
        'Report a bug': "https://github.com/your-repo/riddly-chat/issues",
        'About': """
        # 🧩 Riddly Chat Agent
        
        Ein intelligenter KI-Assistent mit hybrider Suche, der Vektor-Einbettungen 
        und Wissensgraphen kombiniert.
        
        **Funktionen:**
        - 🔀 Hybride Suche (Empfohlen)
        - 📊 Vektor-Suche
        - 🕸️ Wissensgraph-Suche
        - 💬 Echtzeit-Streaming
        - 📋 Chat-Verlauf
        - 🎨 Anpassbare Oberfläche
        """
    }
)

# CSS für ChatGPT-ähnliches Design
def load_custom_css():
    st.markdown("""
    <style>
    /* ChatGPT-ähnliche Farbpalette */
    :root {
        --chatgpt-bg: #343541;
        --chatgpt-sidebar: #202123;
        --chatgpt-user-bg: #444654;
        --chatgpt-assistant-bg: #444654;
        --chatgpt-border: #565869;
        --chatgpt-text: #ececf1;
        --chatgpt-text-secondary: #9ca3af;
        --chatgpt-accent: #10a37f;
        --chatgpt-hover: #2a2b32;
        --chatgpt-input-bg: #40414f;
        --chatgpt-white: #ffffff;
        --chatgpt-light-gray: #f7f7f8;
    }
    
    /* Global Streamlit Styling */
    .stApp {
        background-color: var(--chatgpt-bg);
        color: var(--chatgpt-text);
    }
    
    /* Main Container */
    .main .block-container {
        padding-top: 0rem;
        padding-bottom: 2rem;
        max-width: 768px;
        background-color: var(--chatgpt-bg);
    }
    
    /* Remove Streamlit Header */
    header[data-testid="stHeader"] {
        display: none;
    }
    
    /* Hide Streamlit Menu */
    #MainMenu {
        display: none;
    }
    
    /* Hide Streamlit Footer */
    footer {
        display: none;
    }
    
    /* ChatGPT-style Header */
    .chatgpt-header {
        background: var(--chatgpt-bg);
        padding: 1rem 0;
        border-bottom: 1px solid var(--chatgpt-border);
        text-align: center;
        margin-bottom: 0;
    }
    
    .chatgpt-header h1 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--chatgpt-text);
    }
    
    .chatgpt-header p {
        margin: 0.25rem 0 0 0;
        font-size: 0.875rem;
        color: var(--chatgpt-text-secondary);
    }
    
    /* ChatGPT-style Messages */
    .chatgpt-message {
        padding: 1.5rem 0;
        border-bottom: 1px solid var(--chatgpt-border);
        width: 100%;
    }
    
    .chatgpt-message:last-child {
        border-bottom: none;
    }
    
    .chatgpt-message-content {
        display: flex;
        gap: 1rem;
        max-width: 768px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    .chatgpt-avatar {
        width: 30px;
        height: 30px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: 600;
        flex-shrink: 0;
    }
    
    .chatgpt-avatar.user {
        background: var(--chatgpt-accent);
        color: white;
    }
    
    .chatgpt-avatar.assistant {
        background: var(--chatgpt-accent);
        color: white;
    }
    
    .chatgpt-text {
        flex: 1;
        font-size: 1rem;
        line-height: 1.6;
        color: var(--chatgpt-text);
        word-wrap: break-word;
    }
    
    .chatgpt-message.user {
        background: var(--chatgpt-user-bg);
    }
    
    .chatgpt-message.assistant {
        background: var(--chatgpt-assistant-bg);
    }
    
    /* ChatGPT-style Sidebar */
    .stSidebar {
        background-color: var(--chatgpt-sidebar) !important;
    }
    
    .stSidebar .stMarkdown {
        color: var(--chatgpt-text);
    }
    
    .stSidebar .stSelectbox label,
    .stSidebar .stTextInput label,
    .stSidebar .stCheckbox label {
        color: var(--chatgpt-text) !important;
    }
    
    .stSidebar .stSelectbox > div > div,
    .stSidebar .stTextInput > div > div {
        background-color: var(--chatgpt-input-bg);
        border: 1px solid var(--chatgpt-border);
        color: var(--chatgpt-text);
    }
    
    .stSidebar .stSelectbox > div > div > div {
        color: var(--chatgpt-text);
    }
    
    .stSidebar .stTextInput input {
        background-color: var(--chatgpt-input-bg);
        border: 1px solid var(--chatgpt-border);
        color: var(--chatgpt-text);
    }
    
    .stSidebar .stButton > button {
        background-color: var(--chatgpt-input-bg);
        color: var(--chatgpt-text);
        border: 1px solid var(--chatgpt-border);
        border-radius: 6px;
        transition: all 0.2s;
    }
    
    .stSidebar .stButton > button:hover {
        background-color: var(--chatgpt-hover);
    }
    
    /* Message Meta */
    .chatgpt-meta {
        font-size: 0.75rem;
        color: var(--chatgpt-text-secondary);
        margin-top: 0.75rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Tool Badges */
    .chatgpt-tool {
        display: inline-block;
        background: var(--chatgpt-border);
        color: var(--chatgpt-text-secondary);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        margin: 0.25rem 0.25rem 0.25rem 0;
        font-weight: 500;
    }
    
    /* Status Indicators */
    .status-connected {
        color: var(--chatgpt-accent);
        font-weight: 600;
    }
    
    .status-disconnected {
        color: #ef4444;
        font-weight: 600;
    }
    
    .status-warning {
        color: #f59e0b;
        font-weight: 600;
    }
    
    /* ChatGPT Input Area */
    .chatgpt-input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--chatgpt-bg);
        border-top: 1px solid var(--chatgpt-border);
        padding: 1rem;
        z-index: 1000;
    }
    
    .chatgpt-input-wrapper {
        max-width: 768px;
        margin: 0 auto;
        position: relative;
    }
    
    .stForm {
        background: transparent !important;
    }
    
    .stTextArea > div > div > textarea {
        background-color: var(--chatgpt-input-bg) !important;
        border: 1px solid var(--chatgpt-border) !important;
        border-radius: 12px !important;
        color: var(--chatgpt-text) !important;
        padding: 1rem 3rem 1rem 1rem !important;
        resize: none !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
        min-height: 44px !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: var(--chatgpt-accent) !important;
        box-shadow: 0 0 0 1px var(--chatgpt-accent) !important;
        outline: none !important;
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: var(--chatgpt-text-secondary) !important;
    }
    
    /* ChatGPT Send Button */
    .chatgpt-send-btn {
        position: absolute;
        right: 8px;
        bottom: 8px;
        background-color: var(--chatgpt-accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: background-color 0.2s !important;
    }
    
    .chatgpt-send-btn:hover {
        background-color: #0d8b6b !important;
    }
    
    .chatgpt-send-btn:disabled {
        background-color: var(--chatgpt-border) !important;
        cursor: not-allowed !important;
    }
    
    /* Main Chat Area Padding */
    .chatgpt-messages {
        padding-bottom: 120px;
        min-height: calc(100vh - 120px);
        margin-left: 320px; /* Account for sidebar */
    }
    
    /* Form Submit Button */
    .stForm .stButton > button {
        background-color: var(--chatgpt-accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        width: 32px !important;
        height: 32px !important;
        padding: 0 !important;
        position: absolute !important;
        right: 8px !important;
        bottom: 8px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .stForm .stButton > button:hover {
        background-color: #0d8b6b !important;
    }
    
    .stForm .stButton > button:disabled {
        background-color: var(--chatgpt-border) !important;
    }
    
    /* Remove default form styling */
    .stForm {
        border: none !important;
        padding: 0 !important;
    }
    
    /* Enhanced Mobile Responsive Design */
    @media (max-width: 768px) {
        /* Reset main container for mobile */
        .main .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        
        /* Adjust sidebar for mobile */
        .stSidebar {
            width: 260px !important;
            z-index: 999 !important;
        }
        
        /* Hide sidebar by default on mobile (Streamlit handles toggle) */
        [data-testid="stSidebar"][aria-expanded="false"] {
            display: none;
        }
        
        /* Messages container mobile adjustment */
        .chatgpt-messages {
            margin-left: 0 !important;
            padding: 0 0.5rem 120px 0.5rem !important;
            min-height: calc(100vh - 140px) !important;
        }
        
        /* Header mobile adjustments */
        .chatgpt-header {
            padding: 0.75rem 0.5rem !important;
            position: sticky;
            top: 0;
            z-index: 100;
            background: var(--chatgpt-bg) !important;
        }
        
        .chatgpt-header h1 {
            font-size: 1.25rem !important;
        }
        
        .chatgpt-header p {
            font-size: 0.75rem !important;
        }
        
        /* Message content mobile adjustments */
        .chatgpt-message-content {
            padding: 0 0.75rem !important;
            gap: 0.75rem !important;
        }
        
        .chatgpt-message {
            padding: 1rem 0 !important;
        }
        
        .chatgpt-avatar {
            width: 24px !important;
            height: 24px !important;
            font-size: 12px !important;
        }
        
        .chatgpt-text {
            font-size: 0.9rem !important;
            line-height: 1.5 !important;
        }
        
        /* Welcome message mobile */
        .chatgpt-welcome {
            padding: 2rem 1rem !important;
            margin: 2rem auto !important;
        }
        
        .chatgpt-welcome h2 {
            font-size: 1.5rem !important;
        }
        
        .chatgpt-welcome p {
            font-size: 0.95rem !important;
        }
        
        /* Features grid mobile */
        .chatgpt-features {
            grid-template-columns: 1fr !important;
            gap: 0.75rem !important;
        }
        
        .chatgpt-feature {
            padding: 1rem !important;
        }
        
        .chatgpt-feature-icon {
            font-size: 1.5rem !important;
        }
        
        .chatgpt-feature-title {
            font-size: 0.9rem !important;
        }
        
        .chatgpt-feature-desc {
            font-size: 0.8rem !important;
        }
        
        /* Input container mobile */
        .chatgpt-input-container {
            padding: 0.75rem 0.5rem !important;
            bottom: 0 !important;
        }
        
        .chatgpt-input-wrapper {
            padding: 0 !important;
        }
        
        /* Text area mobile adjustments */
        .stTextArea > div > div > textarea {
            font-size: 16px !important; /* Prevents zoom on iOS */
            padding: 0.75rem 2.5rem 0.75rem 0.75rem !important;
            min-height: 40px !important;
        }
        
        /* Send button mobile */
        .stForm .stButton > button {
            width: 28px !important;
            height: 28px !important;
            right: 6px !important;
            bottom: 6px !important;
        }
        
        /* Meta information mobile */
        .chatgpt-meta {
            font-size: 0.65rem !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 0.25rem !important;
        }
        
        /* Tool badges mobile */
        .chatgpt-tool {
            font-size: 0.65rem !important;
            padding: 0.15rem 0.4rem !important;
        }
        
        /* Sidebar content mobile */
        .stSidebar .stButton > button {
            font-size: 0.85rem !important;
            padding: 0.5rem !important;
        }
        
        .stSidebar .stSelectbox label,
        .stSidebar .stTextInput label,
        .stSidebar .stCheckbox label {
            font-size: 0.85rem !important;
        }
    }
    
    /* Small mobile devices (up to 480px) */
    @media (max-width: 480px) {
        .chatgpt-header h1 {
            font-size: 1.1rem !important;
        }
        
        .chatgpt-welcome h2 {
            font-size: 1.25rem !important;
        }
        
        .chatgpt-message-content {
            padding: 0 0.5rem !important;
        }
        
        .chatgpt-text {
            font-size: 0.85rem !important;
        }
        
        /* Even smaller input on very small screens */
        .stTextArea > div > div > textarea {
            padding: 0.5rem 2rem 0.5rem 0.5rem !important;
        }
        
        .stForm .stButton > button {
            width: 24px !important;
            height: 24px !important;
        }
    }
    
    /* Tablet devices (768px to 1024px) */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            max-width: 100% !important;
            padding: 0 1rem !important;
        }
        
        .chatgpt-messages {
            margin-left: 250px !important;
            padding: 0 1rem 120px 1rem !important;
        }
        
        .chatgpt-message-content {
            max-width: 100% !important;
        }
        
        .chatgpt-welcome {
            max-width: 500px !important;
        }
        
        .chatgpt-features {
            grid-template-columns: repeat(2, 1fr) !important;
        }
    }
    
    /* Landscape orientation adjustments */
    @media (max-height: 600px) and (orientation: landscape) {
        .chatgpt-header {
            padding: 0.5rem !important;
        }
        
        .chatgpt-header h1 {
            font-size: 1.2rem !important;
        }
        
        .chatgpt-header p {
            display: none !important;
        }
        
        .chatgpt-messages {
            padding-bottom: 100px !important;
        }
        
        .chatgpt-input-container {
            padding: 0.5rem !important;
        }
        
        .stTextArea > div > div > textarea {
            min-height: 36px !important;
        }
    }
    
    /* Touch device optimizations */
    @media (hover: none) and (pointer: coarse) {
        /* Increase touch targets */
        .stButton > button {
            min-height: 44px !important;
            min-width: 44px !important;
        }
        
        .chatgpt-tool {
            padding: 0.3rem 0.5rem !important;
        }
        
        /* Better spacing for touch */
        .chatgpt-feature {
            padding: 1.25rem !important;
        }
        
        /* Prevent text selection on touch */
        .chatgpt-avatar,
        .chatgpt-meta,
        .chatgpt-feature-icon {
            -webkit-user-select: none !important;
            user-select: none !important;
        }
    }
    
    /* High DPI displays */
    @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
        .chatgpt-message,
        .chatgpt-feature,
        .stTextArea > div > div > textarea {
            border-width: 0.5px !important;
        }
    }
    
    /* ChatGPT Welcome Message */
    .chatgpt-welcome {
        text-align: center;
        padding: 3rem 2rem;
        max-width: 600px;
        margin: 4rem auto;
        color: var(--chatgpt-text);
    }
    
    .chatgpt-welcome h2 {
        color: var(--chatgpt-text);
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .chatgpt-welcome p {
        color: var(--chatgpt-text-secondary);
        font-size: 1.1rem;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    .chatgpt-features {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-top: 2rem;
    }
    
    .chatgpt-feature {
        background: var(--chatgpt-user-bg);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid var(--chatgpt-border);
        text-align: center;
    }
    
    .chatgpt-feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    .chatgpt-feature-title {
        font-weight: 600;
        color: var(--chatgpt-text);
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    
    .chatgpt-feature-desc {
        color: var(--chatgpt-text-secondary);
        font-size: 0.875rem;
        line-height: 1.4;
    }
    
    .welcome-container h2 {
        color: var(--primary-color);
        margin-bottom: 1rem;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .welcome-container p {
        color: #6c757d;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    
    .feature-list {
        display: flex;
        justify-content: space-around;
        flex-wrap: wrap;
        margin-top: 2rem;
        gap: 1rem;
    }
    
    .feature-item {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        flex: 1;
        min-width: 200px;
        border: 1px solid #e9ecef;
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    .feature-title {
        font-weight: 600;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    
    .feature-desc {
        color: #6c757d;
        font-size: 0.9rem;
    }
    
    /* Streaming Indicator */
    .streaming-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--primary-color);
        font-style: italic;
        margin: 1rem 0;
    }
    
    .typing-dots {
        display: flex;
        gap: 0.2rem;
    }
    
    .dot {
        width: 6px;
        height: 6px;
        background: var(--primary-color);
        border-radius: 50%;
        animation: typing 1.4s infinite;
    }
    
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
        30% { transform: translateY(-8px); opacity: 1; }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .user-message, .assistant-message {
            max-width: 95%;
        }
        
        .feature-list {
            flex-direction: column;
        }
        
        .main-header h1 {
            font-size: 2rem;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .chat-container {
            background: #2b2b2b;
            border-color: #404040;
        }
        
        .assistant-message {
            background: #3b3b3b;
            color: #e9ecef;
        }
        
        .feature-item {
            background: #3b3b3b;
            color: #e9ecef;
            border-color: #404040;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Deutsche Texte
TEXTS = {
    "title": "🧩 Riddly Chat Agent",
    "subtitle": "Intelligenter KI-Assistent mit hybrider Suche",
    "welcome_title": "Willkommen beim Riddly Chat Agent! 👋",
    "welcome_text": "Ich bin Ihr intelligenter KI-Assistent mit erweiterten Suchfähigkeiten. Ich kombiniere Vektor-Einbettungen und Wissensgraphen, um Ihnen die besten Antworten zu liefern.",
    "features": {
        "hybrid": {
            "icon": "🔀",
            "title": "Hybride Suche",
            "desc": "Kombiniert Vektor- und Graph-Suche für optimale Ergebnisse"
        },
        "vector": {
            "icon": "📊", 
            "title": "Vektor-Suche",
            "desc": "Semantische Ähnlichkeitssuche durch Dokumente"
        },
        "graph": {
            "icon": "🕸️",
            "title": "Wissensgraph",
            "desc": "Erkundet Beziehungen zwischen Entitäten und Konzepten"
        },
        "streaming": {
            "icon": "⚡",
            "title": "Echtzeit-Antworten",
            "desc": "Live-Streaming für sofortige Reaktionen"
        }
    },
    "sidebar": {
        "title": "⚙️ Einstellungen",
        "api_url": "🌐 API Server URL",
        "api_key": "🔐 API Schlüssel",
        "search_type": "🔍 Suchtyp",
        "streaming": "⚡ Streaming aktivieren",
        "clear_chat": "🗑️ Chat leeren",
        "export_chat": "📥 Chat exportieren",
        "connection_status": "Verbindungsstatus",
        "connected": "✅ Verbunden",
        "disconnected": "❌ Getrennt",
        "testing": "🔄 Teste Verbindung..."
    },
    "search_types": {
        "hybrid": "🔀 Hybrid (Empfohlen)",
        "vector": "📊 Vektor-Suche", 
        "graph": "🕸️ Wissensgraph"
    },
    "chat": {
        "input_placeholder": "Stellen Sie hier Ihre Frage...",
        "send_button": "Senden 📤",
        "typing": "Assistent tippt",
        "error_title": "⚠️ Fehler",
        "no_response": "Keine Antwort vom Server erhalten",
        "tools_used": "Verwendete Tools:",
        "user_label": "Sie",
        "assistant_label": "KI-Assistent",
        "timestamp": "Uhrzeit"
    },
    "messages": {
        "chat_cleared": "✅ Chat wurde geleert",
        "chat_exported": "✅ Chat wurde exportiert", 
        "connection_success": "✅ Verbindung erfolgreich",
        "connection_failed": "❌ Verbindung fehlgeschlagen",
        "api_key_required": "⚠️ API-Schlüssel erforderlich",
        "invalid_url": "⚠️ Ungültige API URL"
    }
}

# Initialisierung der Session State
def init_session_state():
    """Initialisiert den Session State mit Standardwerten."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
        
    if 'api_url' not in st.session_state:
        st.session_state.api_url = "https://riddly.kobra-dataworks.de"
        
    if 'api_key' not in st.session_state:
        st.session_state.api_key = "J_qfzc5WsTZ5GgyyOhFGplfI7zoDSFrY0XqTitDadmE"
        
    if 'search_type' not in st.session_state:
        st.session_state.search_type = "hybrid"
        
    if 'streaming' not in st.session_state:
        st.session_state.streaming = True
        
    if 'connection_status' not in st.session_state:
        st.session_state.connection_status = "unknown"
        
    if 'saved_sessions' not in st.session_state:
        st.session_state.saved_sessions = {}
        
    if 'language_override' not in st.session_state:
        st.session_state.language_override = "auto"

# API Verbindung testen
def test_api_connection(api_url: str, api_key: str) -> Dict[str, Any]:
    """Testet die Verbindung zur API."""
    try:
        headers = {
            "User-Agent": "Riddly-Chat-Agent/1.0"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key.strip()}"
        
        # Debug-Info
        test_url = f"{api_url.rstrip('/')}/health"
        
        response = requests.get(
            test_url,
            headers=headers,
            timeout=15,
            verify=True  # SSL-Verifizierung aktiviert
        )
        
        if response.status_code == 200:
            try:
                health_data = response.json()
                return {
                    "status": "connected",
                    "message": f"Verbunden ({health_data.get('status', 'healthy')})",
                    "data": health_data
                }
            except json.JSONDecodeError:
                return {
                    "status": "connected",
                    "message": "Verbunden (Response erhalten)",
                    "data": {"raw_response": response.text[:200]}
                }
        elif response.status_code == 401:
            return {
                "status": "error",
                "message": "Authentifizierung fehlgeschlagen (HTTP 401) - Prüfen Sie den API-Schlüssel",
                "data": {"status_code": 401, "url": test_url}
            }
        elif response.status_code == 403:
            return {
                "status": "error", 
                "message": "Zugriff verweigert (HTTP 403) - API-Schlüssel ungültig",
                "data": {"status_code": 403, "url": test_url}
            }
        elif response.status_code == 502:
            return {
                "status": "error",
                "message": "Server temporär nicht verfügbar (HTTP 502) - Riddly Server ist offline oder wird gewartet",
                "data": {"status_code": 502, "url": test_url, "info": "Bad Gateway - Der Server ist möglicherweise offline"}
            }
        elif response.status_code == 503:
            return {
                "status": "error",
                "message": "Service nicht verfügbar (HTTP 503) - Server überlastet oder in Wartung",
                "data": {"status_code": 503, "url": test_url}
            }
        elif response.status_code == 504:
            return {
                "status": "error",
                "message": "Gateway Timeout (HTTP 504) - Server antwortet zu langsam",
                "data": {"status_code": 504, "url": test_url}
            }
        else:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.text[:100] if response.text else 'Keine Details'}",
                "data": {"status_code": response.status_code, "url": test_url}
            }
            
    except requests.exceptions.SSLError as e:
        return {
            "status": "error",
            "message": f"SSL-Zertifikatsfehler: {str(e)[:100]}",
            "data": None
        }
    except requests.exceptions.ConnectTimeout:
        return {
            "status": "error",
            "message": "Verbindungs-Timeout (15s überschritten)",
            "data": None
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status": "error",
            "message": f"Verbindungsfehler: {str(e)[:100]}",
            "data": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error", 
            "message": f"Anfragefehler: {str(e)[:100]}",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unerwarteter Fehler: {str(e)[:100]}",
            "data": None
        }

# Sprache erkennen
def detect_language(text: str) -> str:
    """
    Einfache Spracherkennung basierend auf häufigen Wörtern.
    Gibt 'de' für Deutsch, 'en' für Englisch zurück.
    """
    text_lower = text.lower()
    
    # Deutsche Schlüsselwörter
    german_words = {
        'der', 'die', 'das', 'und', 'oder', 'aber', 'mit', 'für', 'auf', 'in', 'von', 'zu', 'bei', 
        'nach', 'über', 'unter', 'zwischen', 'durch', 'gegen', 'ohne', 'um', 'seit', 'während',
        'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'mich', 'dich', 'sich', 'uns', 'euch',
        'ist', 'sind', 'war', 'waren', 'haben', 'hat', 'hatte', 'hatten', 'werden', 'wird', 'wurde',
        'kann', 'kannst', 'könnte', 'sollte', 'möchte', 'würde', 'muss', 'musst', 'soll', 'will',
        'wie', 'was', 'wo', 'wann', 'warum', 'wer', 'welche', 'welcher', 'welches',
        'nicht', 'kein', 'keine', 'auch', 'noch', 'schon', 'immer', 'hier', 'dort', 'dann',
        'hallo', 'danke', 'bitte', 'ja', 'nein', 'gut', 'schlecht', 'groß', 'klein'
    }
    
    # Englische Schlüsselwörter  
    english_words = {
        'the', 'and', 'or', 'but', 'with', 'for', 'on', 'in', 'of', 'to', 'at', 'by',
        'from', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'is', 'are', 'was', 'were', 'have', 'has', 'had', 'will', 'would', 'could', 'should',
        'can', 'may', 'might', 'must', 'shall', 'do', 'does', 'did', 'get', 'got',
        'how', 'what', 'where', 'when', 'why', 'who', 'which', 'whose',
        'not', 'no', 'yes', 'also', 'still', 'already', 'always', 'here', 'there', 'then',
        'hello', 'thanks', 'please', 'good', 'bad', 'big', 'small', 'great', 'nice'
    }
    
    words = text_lower.split()
    german_score = sum(1 for word in words if word in german_words)
    english_score = sum(1 for word in words if word in english_words)
    
    # Bei gleichstand oder kurzen Texten, schaue auf spezielle Indikatoren
    if german_score == english_score or len(words) < 3:
        # Deutsche Umlaute und ß
        if any(char in text for char in ['ä', 'ö', 'ü', 'ß', 'Ä', 'Ö', 'Ü']):
            return 'de'
        # Typisch deutsche Wortendungen
        if any(text_lower.endswith(ending) for ending in ['ung', 'keit', 'heit', 'lich', 'isch', 'chen', 'lein']):
            return 'de'
        # Typisch englische Wortendungen
        if any(text_lower.endswith(ending) for ending in ['ing', 'tion', 'ly', 'ed', 'er', 'est']):
            return 'en'
    
    return 'de' if german_score > english_score else 'en'

def create_language_instruction(message: str, detected_lang: str, language_override: str = "auto") -> str:
    """
    Erstellt eine Sprachanweisung für den AI-Assistenten.
    """
    # Sprach-Override berücksichtigen
    if language_override == "de":
        return f"Bitte antworte immer auf Deutsch. Benutzer-Nachricht: {message}"
    elif language_override == "en":
        return f"Please always respond in English. User message: {message}"
    elif language_override == "auto":
        if detected_lang == 'de':
            return f"Bitte antworte auf Deutsch, es sei denn der Benutzer fragt explizit nach einer anderen Sprache. Benutzer-Nachricht: {message}"
        else:
            return f"Please respond in English unless the user explicitly asks for a different language. User message: {message}"
    
    return message  # Fallback

# Chat-Nachricht senden
def send_message(message: str, api_url: str, api_key: str, search_type: str, session_id: Optional[str]) -> Dict[str, Any]:
    """Sendet eine Nachricht an die API."""
    try:
        # Sprache erkennen und Nachricht anpassen
        detected_lang = detect_language(message)
        enhanced_message = create_language_instruction(message, detected_lang, st.session_state.language_override)
        
        payload = {
            "message": enhanced_message,
            "session_id": session_id,
            "user_id": "streamlit-user",
            "search_type": search_type
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        response = requests.post(
            f"{api_url.rstrip('/')}/chat",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "data": response.json()
            }
        else:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.text}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Anfragefehler: {str(e)}"
        }

# Streaming-Nachricht senden
def send_streaming_message(message: str, api_url: str, api_key: str, search_type: str, session_id: Optional[str]):
    """Sendet eine Streaming-Nachricht an die API."""
    try:
        # Sprache erkennen und Nachricht anpassen
        detected_lang = detect_language(message)
        enhanced_message = create_language_instruction(message, detected_lang, st.session_state.language_override)
        
        payload = {
            "message": enhanced_message,
            "session_id": session_id,
            "user_id": "streamlit-user", 
            "search_type": search_type
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        response = requests.post(
            f"{api_url.rstrip('/')}/chat/stream",
            json=payload,
            headers=headers,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            return response
        else:
            return None
            
    except requests.exceptions.RequestException:
        return None

# Welcome-Nachricht rendern
def render_welcome_message():
    """Rendert die ChatGPT-ähnliche Willkommensnachricht."""
    st.markdown(f"""
    <div class="chatgpt-welcome">
        <h2>{TEXTS['welcome_title']}</h2>
        <p>{TEXTS['welcome_text']}</p>
        
        <div class="chatgpt-features">
            <div class="chatgpt-feature">
                <span class="chatgpt-feature-icon">{TEXTS['features']['hybrid']['icon']}</span>
                <div class="chatgpt-feature-title">{TEXTS['features']['hybrid']['title']}</div>
                <div class="chatgpt-feature-desc">{TEXTS['features']['hybrid']['desc']}</div>
            </div>
            <div class="chatgpt-feature">
                <span class="chatgpt-feature-icon">{TEXTS['features']['vector']['icon']}</span>
                <div class="chatgpt-feature-title">{TEXTS['features']['vector']['title']}</div>
                <div class="chatgpt-feature-desc">{TEXTS['features']['vector']['desc']}</div>
            </div>
            <div class="chatgpt-feature">
                <span class="chatgpt-feature-icon">{TEXTS['features']['graph']['icon']}</span>
                <div class="chatgpt-feature-title">{TEXTS['features']['graph']['title']}</div>
                <div class="chatgpt-feature-desc">{TEXTS['features']['graph']['desc']}</div>
            </div>
            <div class="chatgpt-feature">
                <span class="chatgpt-feature-icon">{TEXTS['features']['streaming']['icon']}</span>
                <div class="chatgpt-feature-title">{TEXTS['features']['streaming']['title']}</div>
                <div class="chatgpt-feature-desc">{TEXTS['features']['streaming']['desc']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Chat-Nachricht rendern (ChatGPT-Stil)
def render_message(role: str, content: str, timestamp: str, tools_used: List[Dict] = None):
    """Rendert eine ChatGPT-ähnliche Nachricht."""
    avatar_text = "U" if role == "user" else "🧩"
    role_label = TEXTS['chat']['user_label'] if role == "user" else TEXTS['chat']['assistant_label']
    
    tools_html = ""
    if tools_used and len(tools_used) > 0:
        tools_badges = "".join([f'<span class="chatgpt-tool">{tool.get("tool_name", "Unknown")}</span>' 
                               for tool in tools_used])
        tools_html = f'<div style="margin-top: 0.75rem;"><small style="color: var(--chatgpt-text-secondary);">{TEXTS["chat"]["tools_used"]}</small><br>{tools_badges}</div>'
    
    st.markdown(f"""
    <div class="chatgpt-message {role}">
        <div class="chatgpt-message-content">
            <div class="chatgpt-avatar {role}">{avatar_text}</div>
            <div class="chatgpt-text">
                {content}
                <div class="chatgpt-meta">
                    <span>{role_label}</span>
                    <span>{timestamp}</span>
                </div>
                {tools_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Session-Management Funktionen
def load_session_history(session_id: str, api_url: str, api_key: str) -> List[Dict]:
    """Lädt den Chat-Verlauf einer Session von der API."""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        response = requests.get(
            f"{api_url.rstrip('/')}/sessions/{session_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            session_data = response.json()
            messages = session_data.get('messages', [])
            
            # Konvertiere API-Format zu App-Format
            formatted_messages = []
            for msg in messages:
                formatted_msg = {
                    'role': msg.get('role', 'unknown'),
                    'content': msg.get('content', ''),
                    'timestamp': msg.get('created_at', datetime.now().isoformat())[:19].split('T')[1] if msg.get('created_at') else datetime.now().strftime('%H:%M:%S'),
                    'tools_used': msg.get('metadata', {}).get('tools_used', []) if msg.get('metadata') else []
                }
                formatted_messages.append(formatted_msg)
            
            return formatted_messages
        else:
            st.error(f"Fehler beim Laden der Session: HTTP {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        st.error(f"Verbindungsfehler beim Laden der Session: {str(e)}")
        return []

def get_recent_sessions(api_url: str, api_key: str, limit: int = 10) -> List[Dict]:
    """Holt die letzten Sessions von der API (falls implementiert)."""
    # Diese Funktion wäre für einen zukünftigen API-Endpoint
    # Derzeit nutzen wir lokale Session-Speicherung
    return []

def save_session_locally(session_id: str, title: str = None):
    """Speichert Session-Info lokal für schnellen Zugriff."""
    if 'saved_sessions' not in st.session_state:
        st.session_state.saved_sessions = {}
    
    if not title and st.session_state.messages:
        # Generiere Titel aus erster Nachricht
        first_user_msg = next((msg for msg in st.session_state.messages if msg['role'] == 'user'), None)
        if first_user_msg:
            title = first_user_msg['content'][:50] + "..." if len(first_user_msg['content']) > 50 else first_user_msg['content']
        else:
            title = f"Chat {datetime.now().strftime('%H:%M')}"
    
    st.session_state.saved_sessions[session_id] = {
        'title': title or f"Session {session_id[:8]}",
        'last_activity': datetime.now().isoformat(),
        'message_count': len(st.session_state.messages)
    }

def load_session_by_id(session_id: str):
    """Lädt eine spezifische Session."""
    if not session_id:
        return False
        
    # Versuche Session-Historie von API zu laden
    messages = load_session_history(session_id, st.session_state.api_url, st.session_state.api_key)
    
    if messages:
        st.session_state.session_id = session_id
        st.session_state.messages = messages
        st.success(f"✅ Session geladen: {len(messages)} Nachrichten")
        return True
    else:
        st.error("❌ Session konnte nicht geladen werden")
        return False

# Chat-Verlauf exportieren
def export_chat():
    """Exportiert den Chat-Verlauf."""
    if not st.session_state.messages:
        st.warning("Keine Nachrichten zum Exportieren vorhanden.")
        return
        
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "session_id": st.session_state.session_id,
        "search_type": st.session_state.search_type,
        "messages": st.session_state.messages,
        "session_info": st.session_state.saved_sessions.get(st.session_state.session_id, {}) if st.session_state.session_id else {}
    }
    
    json_string = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    st.download_button(
        label="💾 JSON herunterladen",
        data=json_string,
        file_name=f"chat-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json",
        mime="application/json"
    )

# Haupt-App
def main():
    """Hauptfunktion der Streamlit-App."""
    # CSS laden
    load_custom_css()
    
    # Session State initialisieren
    init_session_state()
    
    # ChatGPT-style Header
    st.markdown(f"""
    <div class="chatgpt-header">
        <h1>{TEXTS['title']}</h1>
        <p>{TEXTS['subtitle']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar für Einstellungen
    with st.sidebar:
        st.markdown(f"### {TEXTS['sidebar']['title']}")
        
        # API-Konfiguration
        st.session_state.api_url = st.text_input(
            TEXTS['sidebar']['api_url'],
            value=st.session_state.api_url,
            help="URL des Riddly API Servers"
        )
        
        st.session_state.api_key = st.text_input(
            TEXTS['sidebar']['api_key'],
            value=st.session_state.api_key,
            type="password",
            help="Ihr API-Schlüssel für die Authentifizierung"
        )
        
        # Suchtyp
        search_options = {
            "hybrid": TEXTS['search_types']['hybrid'],
            "vector": TEXTS['search_types']['vector'],
            "graph": TEXTS['search_types']['graph']
        }
        
        st.session_state.search_type = st.selectbox(
            TEXTS['sidebar']['search_type'],
            options=list(search_options.keys()),
            format_func=lambda x: search_options[x],
            index=list(search_options.keys()).index(st.session_state.search_type)
        )
        
        # Streaming
        st.session_state.streaming = st.checkbox(
            TEXTS['sidebar']['streaming'],
            value=st.session_state.streaming
        )
        
        # Spracheinstellung
        language_options = {
            "auto": "🌐 Automatisch erkennen",
            "de": "🇩🇪 Immer Deutsch",
            "en": "🇺🇸 Always English"
        }
        
        st.session_state.language_override = st.selectbox(
            "🗣️ Antwort-Sprache",
            options=list(language_options.keys()),
            format_func=lambda x: language_options[x],
            index=list(language_options.keys()).index(st.session_state.language_override),
            help="Bestimmt in welcher Sprache der Assistent antwortet"
        )
        
        st.divider()
        
        # Verbindungsstatus testen
        if st.button("🔄 Verbindung testen"):
            with st.spinner(TEXTS['sidebar']['testing']):
                result = test_api_connection(st.session_state.api_url, st.session_state.api_key)
                st.session_state.connection_status = result['status']
                
                if result['status'] == 'connected':
                    st.success(result['message'])
                    if result.get('data'):
                        with st.expander("🔍 Verbindungsdetails"):
                            st.json(result['data'])
                else:
                    st.error(result['message'])
                    
                    # Debug-Informationen anzeigen
                    with st.expander("🔍 Debug-Informationen"):
                        st.write(f"**URL getestet:** `{st.session_state.api_url}/health`")
                        st.write(f"**API-Schlüssel verwendet:** `{st.session_state.api_key[:10]}...{st.session_state.api_key[-4:] if len(st.session_state.api_key) > 14 else 'kurz'}`")
                        if result.get('data'):
                            st.json(result['data'])
        
        # Status anzeigen
        st.markdown(f"**{TEXTS['sidebar']['connection_status']}:**")
        if st.session_state.connection_status == 'connected':
            st.markdown(f'<span class="status-connected">{TEXTS["sidebar"]["connected"]}</span>', 
                       unsafe_allow_html=True)
        elif st.session_state.connection_status == 'error':
            st.markdown(f'<span class="status-disconnected">{TEXTS["sidebar"]["disconnected"]}</span>', 
                       unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-warning">Unbekannt</span>', 
                       unsafe_allow_html=True)
        
        st.divider()
        
        # Session-Management
        st.markdown("**📚 Session-Verwaltung:**")
        
        # Session ID Eingabe
        session_input = st.text_input(
            "🔗 Session ID laden",
            placeholder="Session-ID eingeben...",
            help="Geben Sie eine Session-ID ein, um eine vorherige Unterhaltung zu laden"
        )
        
        if st.button("📂 Session laden") and session_input.strip():
            if load_session_by_id(session_input.strip()):
                st.rerun()
        
        # Aktuelle Session Info
        if st.session_state.session_id:
            st.info(f"**Aktuelle Session:** {st.session_state.session_id[:8]}...")
            if st.session_state.session_id in st.session_state.saved_sessions:
                session_info = st.session_state.saved_sessions[st.session_state.session_id]
                st.caption(f"📝 {session_info['title']}")
                st.caption(f"💬 {session_info['message_count']} Nachrichten")
        
        # Gespeicherte Sessions
        if st.session_state.saved_sessions:
            st.markdown("**📋 Kürzliche Sessions:**")
            for session_id, info in list(st.session_state.saved_sessions.items())[-5:]:
                if st.button(
                    f"📁 {info['title'][:30]}{'...' if len(info['title']) > 30 else ''}",
                    key=f"load_session_{session_id}",
                    help=f"Nachrichten: {info['message_count']}, Zuletzt: {info['last_activity'][:16]}"
                ):
                    if load_session_by_id(session_id):
                        st.rerun()
        
        st.divider()
        
        # Chat-Aktionen
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(TEXTS['sidebar']['clear_chat']):
                # Session lokal speichern bevor sie geleert wird
                if st.session_state.session_id and st.session_state.messages:
                    save_session_locally(st.session_state.session_id)
                
                st.session_state.messages = []
                st.session_state.session_id = None
                st.success(TEXTS['messages']['chat_cleared'])
                st.rerun()
        
        with col2:
            if st.button(TEXTS['sidebar']['export_chat']):
                export_chat()
    
    # Haupt-Chat-Bereich (ChatGPT-Stil)
    st.markdown('<div class="chatgpt-messages">', unsafe_allow_html=True)
    
    # Welcome-Nachricht anzeigen wenn keine Nachrichten
    if not st.session_state.messages:
        render_welcome_message()
    else:
        # Chat-Nachrichten anzeigen
        for msg in st.session_state.messages:
            render_message(
                msg['role'],
                msg['content'], 
                msg['timestamp'],
                msg.get('tools_used', [])
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ChatGPT-style Input
    st.markdown('<div class="chatgpt-input-container">', unsafe_allow_html=True)
    st.markdown('<div class="chatgpt-input-wrapper">', unsafe_allow_html=True)
    
    # Form für Input-Handling
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            label="Nachricht",
            placeholder=TEXTS['chat']['input_placeholder'],
            height=44,
            label_visibility="hidden"
        )
        
        send_clicked = st.form_submit_button(
            "➤",
            help=TEXTS['chat']['send_button']
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Nachricht verarbeiten
    if send_clicked and user_input.strip():
        if not st.session_state.api_key:
            st.error(TEXTS['messages']['api_key_required'])
            return
            
        # Sprache erkennen für Anzeige
        detected_lang = detect_language(user_input.strip())
        lang_emoji = "🇩🇪" if detected_lang == 'de' else "🇺🇸"
        
        # Benutzernachricht hinzufügen
        user_msg = {
            'role': 'user',
            'content': user_input.strip(),
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'tools_used': [],
            'detected_lang': detected_lang
        }
        st.session_state.messages.append(user_msg)
        
        # Spracherkennung anzeigen (kurz)
        if st.session_state.language_override == "auto":
            st.info(f"{lang_emoji} Sprache erkannt: {'Deutsch' if detected_lang == 'de' else 'English'}")
        
        # Antwort von API erhalten
        if st.session_state.streaming:
            # Streaming-Antwort
            with st.spinner(f"{TEXTS['chat']['typing']}..."):
                response = send_streaming_message(
                    user_input.strip(),
                    st.session_state.api_url,
                    st.session_state.api_key,
                    st.session_state.search_type,
                    st.session_state.session_id
                )
                
                if response:
                    # Placeholder für Streaming-Nachricht
                    placeholder = st.empty()
                    full_response = ""
                    tools_used = []
                    
                    # Streaming-Anzeige
                    placeholder.markdown(f"""
                    <div class="streaming-indicator">
                        <div class="typing-dots">
                            <div class="dot"></div>
                            <div class="dot"></div>
                            <div class="dot"></div>
                        </div>
                        <span>{TEXTS['chat']['typing']}...</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Stream verarbeiten
                    try:
                        for line in response.iter_lines():
                            if line:
                                line = line.decode('utf-8')
                                if line.startswith('data: '):
                                    try:
                                        data = json.loads(line[6:])
                                        
                                        if data.get('type') == 'session':
                                            new_session_id = data.get('session_id')
                                            if new_session_id != st.session_state.session_id:
                                                st.session_state.session_id = new_session_id
                                                # Neue Session - speichere sie lokal
                                                save_session_locally(st.session_state.session_id)
                                        elif data.get('type') == 'text':
                                            full_response += data.get('content', '')
                                            # Live-Update der Antwort
                                            placeholder.markdown(f"""
                                            <div class="assistant-message">
                                                {full_response}
                                                <div class="streaming-indicator">
                                                    <div class="typing-dots">
                                                        <div class="dot"></div>
                                                        <div class="dot"></div>
                                                        <div class="dot"></div>
                                                    </div>
                                                    <span>{TEXTS['chat']['typing']}...</span>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        elif data.get('type') == 'tools':
                                            tools_used = data.get('tools', [])
                                        elif data.get('type') == 'end':
                                            break
                                    except json.JSONDecodeError:
                                        continue
                    except Exception as e:
                        st.error(f"Streaming-Fehler: {str(e)}")
                        full_response = "Entschuldigung, beim Streaming ist ein Fehler aufgetreten."
                    
                    # Placeholder leeren und finale Nachricht hinzufügen
                    placeholder.empty()
                    
                    if full_response:
                        assistant_msg = {
                            'role': 'assistant',
                            'content': full_response,
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'tools_used': tools_used
                        }
                        st.session_state.messages.append(assistant_msg)
                        
                        # Session-Info aktualisieren
                        if st.session_state.session_id:
                            save_session_locally(st.session_state.session_id)
                    else:
                        st.error(TEXTS['chat']['no_response'])
                else:
                    st.error("Fehler beim Senden der Streaming-Anfrage")
        else:
            # Normale Antwort
            with st.spinner(f"{TEXTS['chat']['typing']}..."):
                result = send_message(
                    user_input.strip(),
                    st.session_state.api_url,
                    st.session_state.api_key,
                    st.session_state.search_type,
                    st.session_state.session_id
                )
                
                if result['status'] == 'success':
                    data = result['data']
                    
                    # Session ID aktualisieren und speichern
                    if data.get('session_id'):
                        if data['session_id'] != st.session_state.session_id:
                            st.session_state.session_id = data['session_id']
                            # Neue Session - speichere sie lokal
                            save_session_locally(st.session_state.session_id)
                    
                    # Assistant-Nachricht hinzufügen
                    assistant_msg = {
                        'role': 'assistant',
                        'content': data.get('message', 'Keine Antwort erhalten'),
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'tools_used': data.get('tools_used', [])
                    }
                    st.session_state.messages.append(assistant_msg)
                    
                    # Session-Info aktualisieren
                    if st.session_state.session_id:
                        save_session_locally(st.session_state.session_id)
                else:
                    st.error(f"{TEXTS['chat']['error_title']}: {result['message']}")
        
        # Seite neu laden um neue Nachrichten anzuzeigen
        st.rerun()

if __name__ == "__main__":
    main()