/**
 * Embeddable Chat Widget for Agentic RAG System
 * 
 * Usage:
 * <script src="path/to/chat-widget.js"></script>
 * <script>
 *   new ChatWidget({
 *     apiUrl: 'http://localhost:8058',
 *     apiKey: 'your-api-key',
 *     containerId: 'chat-container', // optional
 *     theme: 'light', // 'light' or 'dark'
 *     position: 'bottom-right' // 'bottom-right', 'bottom-left', 'custom'
 *   });
 * </script>
 */

class ChatWidget {
  constructor(config) {
    this.config = {
      apiUrl: config.apiUrl || 'http://localhost:8058',
      apiKey: config.apiKey,
      containerId: config.containerId,
      theme: config.theme || 'light',
      position: config.position || 'bottom-right',
      width: config.width || '400px',
      height: config.height || '600px',
      title: config.title || 'AI Assistant',
      placeholder: config.placeholder || 'Ask me anything...',
      welcomeMessage: config.welcomeMessage || 'Hi! How can I help you today?'
    };

    this.sessionId = null;
    this.isOpen = false;
    this.messages = [];
    this.isStreaming = false;

    this.init();
  }

  init() {
    this.createStyles();
    this.createWidget();
    this.attachEventListeners();
  }

  createStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .chat-widget-container {
        position: fixed;
        z-index: 10000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        ${this.getPositionStyles()}
      }

      .chat-widget-trigger {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s, box-shadow 0.2s;
      }

      .chat-widget-trigger:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
      }

      .chat-widget-trigger svg {
        width: 24px;
        height: 24px;
        fill: white;
      }

      .chat-widget-panel {
        position: absolute;
        bottom: 70px;
        right: 0;
        width: ${this.config.width};
        height: ${this.config.height};
        background: ${this.config.theme === 'dark' ? '#1a1a1a' : 'white'};
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        border: 1px solid ${this.config.theme === 'dark' ? '#333' : '#e1e5e9'};
        display: none;
        flex-direction: column;
        overflow: hidden;
      }

      .chat-widget-panel.open {
        display: flex;
      }

      .chat-widget-header {
        padding: 16px 20px;
        background: ${this.config.theme === 'dark' ? '#2a2a2a' : '#f8f9fa'};
        border-bottom: 1px solid ${this.config.theme === 'dark' ? '#333' : '#e1e5e9'};
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .chat-widget-title {
        font-weight: 600;
        font-size: 16px;
        color: ${this.config.theme === 'dark' ? 'white' : '#1a1a1a'};
        margin: 0;
      }

      .chat-widget-close {
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        color: ${this.config.theme === 'dark' ? '#888' : '#666'};
      }

      .chat-widget-close:hover {
        background: ${this.config.theme === 'dark' ? '#333' : '#e9ecef'};
      }

      .chat-widget-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .chat-message {
        display: flex;
        align-items: flex-start;
        gap: 8px;
      }

      .chat-message.user {
        flex-direction: row-reverse;
      }

      .chat-message-content {
        max-width: 80%;
        padding: 12px 16px;
        border-radius: 18px;
        font-size: 14px;
        line-height: 1.4;
        word-wrap: break-word;
      }

      .chat-message.user .chat-message-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }

      .chat-message.assistant .chat-message-content {
        background: ${this.config.theme === 'dark' ? '#2a2a2a' : '#f1f3f5'};
        color: ${this.config.theme === 'dark' ? 'white' : '#1a1a1a'};
      }

      .chat-message-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 600;
        flex-shrink: 0;
      }

      .chat-message.user .chat-message-avatar {
        background: #e9ecef;
        color: #495057;
      }

      .chat-message.assistant .chat-message-avatar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }

      .chat-widget-input-container {
        padding: 16px;
        border-top: 1px solid ${this.config.theme === 'dark' ? '#333' : '#e1e5e9'};
        background: ${this.config.theme === 'dark' ? '#1a1a1a' : 'white'};
      }

      .chat-widget-input-form {
        display: flex;
        gap: 8px;
        align-items: flex-end;
      }

      .chat-widget-input {
        flex: 1;
        border: 1px solid ${this.config.theme === 'dark' ? '#333' : '#ced4da'};
        border-radius: 20px;
        padding: 12px 16px;
        font-size: 14px;
        background: ${this.config.theme === 'dark' ? '#2a2a2a' : 'white'};
        color: ${this.config.theme === 'dark' ? 'white' : '#1a1a1a'};
        resize: none;
        min-height: 20px;
        max-height: 100px;
        outline: none;
        font-family: inherit;
      }

      .chat-widget-input:focus {
        border-color: #667eea;
      }

      .chat-widget-send {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.1s;
      }

      .chat-widget-send:hover {
        transform: scale(1.05);
      }

      .chat-widget-send:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
      }

      .chat-widget-send svg {
        width: 16px;
        height: 16px;
        fill: white;
      }

      .chat-typing-indicator {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 12px 16px;
        background: ${this.config.theme === 'dark' ? '#2a2a2a' : '#f1f3f5'};
        border-radius: 18px;
        max-width: 80px;
      }

      .typing-dot {
        width: 6px;
        height: 6px;
        background: ${this.config.theme === 'dark' ? '#888' : '#666'};
        border-radius: 50%;
        animation: typing 1.4s infinite;
      }

      .typing-dot:nth-child(2) { animation-delay: 0.2s; }
      .typing-dot:nth-child(3) { animation-delay: 0.4s; }

      @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
        30% { transform: translateY(-10px); opacity: 1; }
      }

      .chat-widget-tools {
        font-size: 12px;
        color: ${this.config.theme === 'dark' ? '#888' : '#666'};
        margin-top: 4px;
        font-style: italic;
      }

      .chat-widget-error {
        background: #fee;
        color: #c53030;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 12px;
        border: 1px solid #fed7d7;
      }
    `;

    if (this.config.position === 'bottom-left') {
      style.textContent += `
        .chat-widget-panel {
          right: auto;
          left: 0;
        }
      `;
    }

    document.head.appendChild(style);
  }

  getPositionStyles() {
    if (this.config.containerId) {
      return 'position: relative; bottom: auto; right: auto;';
    }

    switch (this.config.position) {
      case 'bottom-left':
        return 'bottom: 20px; left: 20px;';
      case 'bottom-right':
      default:
        return 'bottom: 20px; right: 20px;';
    }
  }

  createWidget() {
    const container = this.config.containerId ? 
      document.getElementById(this.config.containerId) : 
      document.body;

    const widget = document.createElement('div');
    widget.className = 'chat-widget-container';
    widget.innerHTML = `
      <button class="chat-widget-trigger" id="chat-widget-trigger">
        <svg viewBox="0 0 24 24">
          <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
        </svg>
      </button>
      <div class="chat-widget-panel" id="chat-widget-panel">
        <div class="chat-widget-header">
          <h3 class="chat-widget-title">${this.config.title}</h3>
          <button class="chat-widget-close" id="chat-widget-close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        <div class="chat-widget-messages" id="chat-widget-messages"></div>
        <div class="chat-widget-input-container">
          <form class="chat-widget-input-form" id="chat-widget-form">
            <textarea
              class="chat-widget-input"
              id="chat-widget-input"
              placeholder="${this.config.placeholder}"
              rows="1"
            ></textarea>
            <button type="submit" class="chat-widget-send" id="chat-widget-send">
              <svg viewBox="0 0 24 24">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </form>
        </div>
      </div>
    `;

    container.appendChild(widget);

    // Add welcome message
    this.addMessage('assistant', this.config.welcomeMessage);
  }

  attachEventListeners() {
    const trigger = document.getElementById('chat-widget-trigger');
    const panel = document.getElementById('chat-widget-panel');
    const closeBtn = document.getElementById('chat-widget-close');
    const form = document.getElementById('chat-widget-form');
    const input = document.getElementById('chat-widget-input');

    trigger.addEventListener('click', () => this.toggleWidget());
    closeBtn.addEventListener('click', () => this.closeWidget());
    form.addEventListener('submit', (e) => this.handleSubmit(e));

    // Auto-resize textarea
    input.addEventListener('input', (e) => {
      e.target.style.height = 'auto';
      e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px';
    });

    // Handle Enter key (but allow Shift+Enter for new line)
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleSubmit(e);
      }
    });
  }

  toggleWidget() {
    const panel = document.getElementById('chat-widget-panel');
    this.isOpen = !this.isOpen;
    
    if (this.isOpen) {
      panel.classList.add('open');
      document.getElementById('chat-widget-input').focus();
    } else {
      panel.classList.remove('open');
    }
  }

  closeWidget() {
    const panel = document.getElementById('chat-widget-panel');
    this.isOpen = false;
    panel.classList.remove('open');
  }

  async handleSubmit(e) {
    e.preventDefault();
    
    if (this.isStreaming) return;

    const input = document.getElementById('chat-widget-input');
    const message = input.value.trim();
    
    if (!message) return;

    // Clear input
    input.value = '';
    input.style.height = 'auto';

    // Add user message
    this.addMessage('user', message);
    
    // Show typing indicator
    this.showTypingIndicator();

    try {
      await this.sendMessage(message);
    } catch (error) {
      this.hideTypingIndicator();
      this.addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
      this.addError(`Error: ${error.message}`);
    }
  }

  async sendMessage(message) {
    this.isStreaming = true;
    
    const payload = {
      message: message,
      session_id: this.sessionId,
      user_id: 'widget-user',
      search_type: 'hybrid'
    };

    const response = await fetch(`${this.config.apiUrl}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config.apiKey}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    this.hideTypingIndicator();
    
    // Create assistant message container
    const messageContainer = this.addMessage('assistant', '');
    const contentElement = messageContainer.querySelector('.chat-message-content');
    
    let fullResponse = '';
    let tools = [];

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              switch (data.type) {
                case 'session':
                  this.sessionId = data.session_id;
                  break;
                  
                case 'text':
                  fullResponse += data.content;
                  contentElement.textContent = fullResponse;
                  this.scrollToBottom();
                  break;
                  
                case 'tools':
                  tools = data.tools;
                  break;
                  
                case 'error':
                  throw new Error(data.content);
                  
                case 'end':
                  break;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', parseError);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
      this.isStreaming = false;
    }

    // Add tools info if any were used
    if (tools && tools.length > 0) {
      const toolInfo = document.createElement('div');
      toolInfo.className = 'chat-widget-tools';
      toolInfo.textContent = `Used tools: ${tools.map(t => t.tool_name).join(', ')}`;
      messageContainer.appendChild(toolInfo);
    }

    this.scrollToBottom();
  }

  addMessage(role, content) {
    const messagesContainer = document.getElementById('chat-widget-messages');
    
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'chat-message-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'AI';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'chat-message-content';
    messageContent.textContent = content;
    
    messageElement.appendChild(avatar);
    messageElement.appendChild(messageContent);
    
    messagesContainer.appendChild(messageElement);
    this.scrollToBottom();
    
    return messageElement;
  }

  addError(message) {
    const messagesContainer = document.getElementById('chat-widget-messages');
    
    const errorElement = document.createElement('div');
    errorElement.className = 'chat-widget-error';
    errorElement.textContent = message;
    
    messagesContainer.appendChild(errorElement);
    this.scrollToBottom();
  }

  showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-widget-messages');
    
    const typingElement = document.createElement('div');
    typingElement.className = 'chat-message assistant';
    typingElement.id = 'typing-indicator';
    
    const avatar = document.createElement('div');
    avatar.className = 'chat-message-avatar';
    avatar.textContent = 'AI';
    
    const indicator = document.createElement('div');
    indicator.className = 'chat-typing-indicator';
    indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    
    typingElement.appendChild(avatar);
    typingElement.appendChild(indicator);
    messagesContainer.appendChild(typingElement);
    
    this.scrollToBottom();
  }

  hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
      indicator.remove();
    }
  }

  scrollToBottom() {
    const messagesContainer = document.getElementById('chat-widget-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

// Auto-initialize if config is provided
if (typeof window !== 'undefined' && window.ChatWidgetConfig) {
  new ChatWidget(window.ChatWidgetConfig);
}