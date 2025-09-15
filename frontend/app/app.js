/**
 * Agentic RAG Chat Application
 * Main application logic for the standalone chat interface
 */

class ChatApp {
    constructor() {
        this.config = {
            apiUrl: localStorage.getItem('apiUrl') || 'http://localhost:8058',
            apiKey: localStorage.getItem('apiKey') || '',
            theme: localStorage.getItem('theme') || 'auto',
            streaming: localStorage.getItem('streaming') !== 'false',
            sounds: localStorage.getItem('sounds') === 'true'
        };

        this.sessionId = null;
        this.currentSearch = 'hybrid';
        this.isStreaming = false;
        this.chatHistory = JSON.parse(localStorage.getItem('chatHistory') || '[]');
        this.messages = [];
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.loadSettings();
        this.loadChatHistory();
        this.applyTheme();
        
        // Check server connection
        await this.checkConnection();
        
        // Hide loading overlay
        document.getElementById('loadingOverlay').classList.remove('show');
    }

    setupEventListeners() {
        // Sidebar
        document.getElementById('sidebarToggle').addEventListener('click', () => this.toggleSidebar());
        document.getElementById('newChatBtn').addEventListener('click', () => this.startNewChat());
        
        // Search type
        document.getElementById('searchTypeSelect').addEventListener('change', (e) => {
            this.currentSearch = e.target.value;
            this.updateSessionInfo();
        });
        
        // Chat form
        document.getElementById('chatForm').addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Input handling
        const messageInput = document.getElementById('messageInput');
        messageInput.addEventListener('input', () => this.handleInputChange());
        messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Settings
        document.getElementById('settingsBtn').addEventListener('click', () => this.openSettings());
        document.getElementById('closeSettingsModal').addEventListener('click', () => this.closeSettings());
        document.getElementById('saveSettingsBtn').addEventListener('click', () => this.saveSettings());
        document.getElementById('resetSettingsBtn').addEventListener('click', () => this.resetSettings());
        
        // Export
        document.getElementById('exportBtn').addEventListener('click', () => this.exportChat());
        
        // Theme detection
        if (this.config.theme === 'auto') {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener(() => this.applyTheme());
        }
        
        // Close modal on outside click
        document.getElementById('settingsModal').addEventListener('click', (e) => {
            if (e.target.id === 'settingsModal') {
                this.closeSettings();
            }
        });
    }

    loadSettings() {
        // Update UI with current settings
        document.getElementById('apiUrlInput').value = this.config.apiUrl;
        document.getElementById('apiKeyInput').value = this.config.apiKey;
        document.getElementById('themeSelect').value = this.config.theme;
        document.getElementById('streamingCheckbox').checked = this.config.streaming;
        document.getElementById('soundCheckbox').checked = this.config.sounds;
    }

    applyTheme() {
        const isDark = this.config.theme === 'dark' || 
            (this.config.theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
        
        if (isDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    }

    loadChatHistory() {
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';
        
        this.chatHistory.forEach(chat => {
            const item = this.createHistoryItem(chat);
            historyList.appendChild(item);
        });
    }

    createHistoryItem(chat) {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.dataset.sessionId = chat.sessionId;
        
        const title = chat.title || 'New Conversation';
        const date = new Date(chat.updatedAt).toLocaleDateString();
        const time = new Date(chat.updatedAt).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        item.innerHTML = `
            <div class="history-title">${title}</div>
            <div class="history-meta">
                <span>${chat.messageCount} messages</span>
                <span>${date} ${time}</span>
            </div>
        `;
        
        item.addEventListener('click', () => this.loadChat(chat.sessionId));
        
        return item;
    }

    async checkConnection() {
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        
        try {
            const response = await fetch(`${this.config.apiUrl}/health`, {
                headers: this.config.apiKey ? {
                    'Authorization': `Bearer ${this.config.apiKey}`
                } : {}
            });
            
            if (response.ok) {
                const health = await response.json();
                statusDot.className = 'status-dot connected';
                statusText.textContent = `Connected (${health.status})`;
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            statusDot.className = 'status-dot error';
            statusText.textContent = `Connection failed: ${error.message}`;
            console.error('Connection check failed:', error);
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const isOpen = sidebar.classList.contains('open');
        
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('open');
        } else {
            sidebar.classList.toggle('collapsed');
        }
    }

    startNewChat() {
        this.sessionId = null;
        this.messages = [];
        this.clearMessages();
        this.showWelcomeMessage();
        this.updateChatTitle('AI Assistant', 'Ready to help');
        
        // Clear active history item
        document.querySelectorAll('.history-item').forEach(item => {
            item.classList.remove('active');
        });
    }

    async loadChat(sessionId) {
        try {
            const response = await fetch(`${this.config.apiUrl}/sessions/${sessionId}`, {
                headers: {
                    'Authorization': `Bearer ${this.config.apiKey}`
                }
            });
            
            if (!response.ok) throw new Error('Failed to load chat');
            
            const session = await response.json();
            this.sessionId = sessionId;
            this.messages = session.messages || [];
            
            this.clearMessages();
            this.renderMessages();
            this.updateChatTitle(session.title || 'Conversation', `${this.messages.length} messages`);
            
            // Mark as active
            document.querySelectorAll('.history-item').forEach(item => {
                item.classList.toggle('active', item.dataset.sessionId === sessionId);
            });
            
        } catch (error) {
            console.error('Failed to load chat:', error);
            this.showError('Failed to load conversation');
        }
    }

    updateChatTitle(title, info) {
        document.getElementById('chatTitle').textContent = title;
        document.getElementById('sessionInfo').textContent = info;
    }

    updateSessionInfo() {
        const searchType = this.currentSearch;
        const searchNames = {
            hybrid: '🔀 Hybrid Search',
            vector: '📊 Vector Search',
            graph: '🕸️ Knowledge Graph'
        };
        
        if (this.sessionId) {
            document.getElementById('sessionInfo').textContent = 
                `Session active • ${searchNames[searchType]}`;
        } else {
            document.getElementById('sessionInfo').textContent = 
                `Ready to help • ${searchNames[searchType]}`;
        }
    }

    handleInputChange() {
        const input = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const charCount = document.getElementById('charCount');
        
        const length = input.value.length;
        charCount.textContent = length;
        
        // Enable/disable send button
        sendBtn.disabled = length === 0 || this.isStreaming;
        
        // Auto-resize textarea
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 150) + 'px';
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleSubmit(e);
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.isStreaming) return;
        
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Clear input
        input.value = '';
        input.style.height = 'auto';
        this.handleInputChange();
        
        // Hide welcome message if visible
        this.hideWelcomeMessage();
        
        // Add user message
        this.addMessage('user', message);
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            if (this.config.streaming) {
                await this.sendStreamingMessage(message);
            } else {
                await this.sendMessage(message);
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
            this.showError(`Error: ${error.message}`);
            console.error('Message send failed:', error);
        }
    }

    async sendMessage(message) {
        this.isStreaming = true;
        
        const payload = {
            message: message,
            session_id: this.sessionId,
            user_id: 'web-user',
            search_type: this.currentSearch
        };

        const response = await fetch(`${this.config.apiUrl}/chat`, {
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

        const result = await response.json();
        
        this.hideTypingIndicator();
        this.isStreaming = false;
        
        // Update session ID
        if (result.session_id && result.session_id !== this.sessionId) {
            this.sessionId = result.session_id;
            this.updateSessionInfo();
        }
        
        // Add assistant message
        this.addMessage('assistant', result.message, result.tools_used);
        
        // Update chat history
        this.updateChatHistory(message);
        
        // Play sound if enabled
        if (this.config.sounds) {
            this.playNotificationSound();
        }
    }

    async sendStreamingMessage(message) {
        this.isStreaming = true;
        
        const payload = {
            message: message,
            session_id: this.sessionId,
            user_id: 'web-user',
            search_type: this.currentSearch
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
        const messageElement = this.addMessage('assistant', '');
        const contentElement = messageElement.querySelector('.message-bubble');
        
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
                                    if (data.session_id !== this.sessionId) {
                                        this.sessionId = data.session_id;
                                        this.updateSessionInfo();
                                    }
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

        // Update message with tools if any were used
        this.updateMessageTools(messageElement, tools);
        
        // Update chat history
        this.updateChatHistory(message);
        
        // Play sound if enabled
        if (this.config.sounds) {
            this.playNotificationSound();
        }
        
        this.scrollToBottom();
    }

    addMessage(role, content, tools = []) {
        const messagesContainer = document.getElementById('chatMessages');
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${role}`;
        
        const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageElement.innerHTML = `
            <div class="message-avatar">${role === 'user' ? 'U' : 'AI'}</div>
            <div class="message-content">
                <div class="message-bubble">${content}</div>
                <div class="message-meta">
                    <span>${timestamp}</span>
                    ${tools.length > 0 ? `
                        <div class="tools-used">
                            ${tools.map(tool => `<span class="tool-badge">${tool.tool_name}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
        
        return messageElement;
    }

    updateMessageTools(messageElement, tools) {
        if (!tools || tools.length === 0) return;
        
        const metaElement = messageElement.querySelector('.message-meta');
        const toolsHtml = `
            <div class="tools-used">
                ${tools.map(tool => `<span class="tool-badge">${tool.tool_name}</span>`).join('')}
            </div>
        `;
        metaElement.innerHTML += toolsHtml;
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        
        const typingElement = document.createElement('div');
        typingElement.className = 'message assistant';
        typingElement.id = 'typing-indicator';
        
        typingElement.innerHTML = `
            <div class="message-avatar">AI</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingElement);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    showWelcomeMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'block';
        }
    }

    hideWelcomeMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
    }

    clearMessages() {
        const messagesContainer = document.getElementById('chatMessages');
        const messages = messagesContainer.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
        
        const typingIndicator = messagesContainer.querySelector('#typing-indicator');
        if (typingIndicator) typingIndicator.remove();
    }

    renderMessages() {
        if (this.messages.length === 0) {
            this.showWelcomeMessage();
            return;
        }
        
        this.messages.forEach(message => {
            this.addMessage(message.role, message.content, message.tools_used || []);
        });
    }

    updateChatHistory(lastMessage) {
        if (!this.sessionId) return;
        
        // Find existing chat or create new one
        let chat = this.chatHistory.find(c => c.sessionId === this.sessionId);
        
        if (!chat) {
            chat = {
                sessionId: this.sessionId,
                title: this.generateChatTitle(lastMessage),
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
                messageCount: 0
            };
            this.chatHistory.unshift(chat);
        }
        
        chat.updatedAt = new Date().toISOString();
        chat.messageCount = this.messages.length + 2; // +2 for current user and assistant messages
        
        // Keep only last 50 chats
        this.chatHistory = this.chatHistory.slice(0, 50);
        
        // Save to localStorage
        localStorage.setItem('chatHistory', JSON.stringify(this.chatHistory));
        
        // Update UI
        this.loadChatHistory();
    }

    generateChatTitle(message) {
        // Generate a title from the first message
        const words = message.split(' ').slice(0, 5);
        return words.join(' ') + (message.split(' ').length > 5 ? '...' : '');
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showError(message) {
        // You could implement a toast notification system here
        console.error('App Error:', message);
    }

    playNotificationSound() {
        // Simple notification sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
            
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.1, audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.2);
        } catch (error) {
            console.warn('Could not play notification sound:', error);
        }
    }

    // Settings Management
    openSettings() {
        document.getElementById('settingsModal').classList.add('show');
    }

    closeSettings() {
        document.getElementById('settingsModal').classList.remove('show');
    }

    saveSettings() {
        // Get values from form
        const apiUrl = document.getElementById('apiUrlInput').value.trim();
        const apiKey = document.getElementById('apiKeyInput').value.trim();
        const theme = document.getElementById('themeSelect').value;
        const streaming = document.getElementById('streamingCheckbox').checked;
        const sounds = document.getElementById('soundCheckbox').checked;
        
        // Validate API URL
        try {
            new URL(apiUrl);
        } catch {
            alert('Please enter a valid API URL');
            return;
        }
        
        // Update config
        this.config.apiUrl = apiUrl;
        this.config.apiKey = apiKey;
        this.config.theme = theme;
        this.config.streaming = streaming;
        this.config.sounds = sounds;
        
        // Save to localStorage
        localStorage.setItem('apiUrl', apiUrl);
        localStorage.setItem('apiKey', apiKey);
        localStorage.setItem('theme', theme);
        localStorage.setItem('streaming', streaming.toString());
        localStorage.setItem('sounds', sounds.toString());
        
        // Apply changes
        this.applyTheme();
        this.checkConnection();
        
        // Close modal
        this.closeSettings();
    }

    resetSettings() {
        if (confirm('Reset all settings to defaults? This will clear your API key and chat history.')) {
            localStorage.clear();
            location.reload();
        }
    }

    exportChat() {
        if (this.messages.length === 0) {
            alert('No messages to export');
            return;
        }
        
        const chatData = {
            sessionId: this.sessionId,
            exportedAt: new Date().toISOString(),
            messages: this.messages,
            searchType: this.currentSearch
        };
        
        const blob = new Blob([JSON.stringify(chatData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});