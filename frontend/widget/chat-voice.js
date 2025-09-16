/**
 * Einbettbares Chat-Widget für Riddly Assistant mit Sprach-Unterstützung
 *
 * Features:
 * - Spracherkennung (Speech-to-Text) für Eingaben
 * - Text-to-Speech für Antworten
 * - Visuelle Feedback während der Aufnahme
 * - Fallback für Browser ohne Web Speech API
 *
 * Usage:
 * <script src="path/to/chat-widget-voice.js"></script>
 * <script>
 *   new ChatWidget({
 *     apiUrl: 'http://localhost:8058',
 *     apiKey: 'your-api-key',
 *     containerId: 'chat-container', // optional
 *     theme: 'light', // 'light' or 'dark'
 *     position: 'bottom-right', // 'bottom-right', 'bottom-left', 'custom'
 *     enableVoice: true, // Enable voice features
 *     autoSpeak: true, // Automatically speak responses
 *     voiceLang: 'de-DE' // Voice language
 *   });
 * </script>
 */

class ChatWidget {
  constructor(config) {
    // Validate configuration first
    this.validateConfig(config);

    this.config = {
      apiUrl: config.apiUrl || 'http://localhost:8058',
      apiKey: config.apiKey,
      containerId: config.containerId,
      theme: config.theme || 'light',
      position: config.position || 'bottom-right',
      width: config.width || '400px',
      height: config.height || '600px',
      title: config.title || 'Riddly Assistant',
      placeholder: config.placeholder || 'Stellen Sie mir eine Frage...',
      welcomeMessage: config.welcomeMessage || 'Hallo! Wie kann ich Ihnen heute helfen?',
      enableVoice: config.enableVoice !== false, // Default true
      autoSpeak: config.autoSpeak !== false, // Default true
      voiceLang: config.voiceLang || 'de-DE', // German by default
      voiceRate: Math.max(0.5, Math.min(2, config.voiceRate || 1.0)), // Speech rate (clamped)
      voicePitch: Math.max(0.5, Math.min(2, config.voicePitch || 1.0)), // Speech pitch (clamped)
      maxMessageLength: config.maxMessageLength || 2000,
      maxRetries: config.maxRetries || 3,
      retryDelay: config.retryDelay || 1000,
      rateLimit: config.rateLimit || { messages: 10, window: 60000 } // 10 messages per minute
    };

    // Security: Allowed domains whitelist
    this.allowedDomains = [
      'localhost',
      '127.0.0.1',
      'riddly.kobra-dataworks.de',
      'kobra-dataworks.de'
    ];

    this.sessionId = null;
    this.isOpen = false;
    this.messages = [];
    this.isStreaming = false;

    // Voice-related properties
    this.isRecording = false;
    this.recognition = null;
    this.synthesis = window.speechSynthesis;
    this.isSpeaking = false;
    this.voiceSupported = this.checkVoiceSupport();

    // Rate limiting
    this.messageTimestamps = [];

    // Event listeners for cleanup
    this.eventListeners = [];
    this.abortController = null;

    // Initialize with error handling
    try {
      this.init();
    } catch (error) {
      console.error('Failed to initialize chat widget:', error);
      this.cleanup();
    }
  }

  validateConfig(config) {
    if (!config.apiUrl) {
      throw new Error('API URL is required');
    }

    // Validate URL format and domain
    try {
      const url = new URL(config.apiUrl);
      const hostname = url.hostname;

      // Check if domain is whitelisted (skip check during construction since allowedDomains not set yet)
      const allowedDomains = [
        'localhost',
        '127.0.0.1',
        'riddly.kobra-dataworks.de',
        'kobra-dataworks.de'
      ];

      const isAllowed = allowedDomains.some(domain =>
        hostname === domain || hostname.endsWith(`.${domain}`)
      );

      if (!isAllowed && !config.skipDomainValidation) {
        throw new Error(`Domain ${hostname} is not in the allowed list`);
      }

      // Force HTTPS in production
      if (hostname !== 'localhost' && hostname !== '127.0.0.1' && url.protocol !== 'https:') {
        console.warn('⚠️ Warning: HTTPS is recommended for production domains');
      }
    } catch (error) {
      throw new Error(`Invalid API URL: ${error.message}`);
    }

    // Warn about API key in frontend
    if (config.apiKey) {
      console.warn('⚠️ Security Warning: API key is exposed in frontend code. Consider using a server-side proxy.');
    }
  }

  sanitizeText(text) {
    if (typeof text !== 'string') return '';

    // Remove potentially dangerous characters and limit length
    return text
      .replace(/[<>]/g, '') // Remove HTML brackets
      .replace(/javascript:/gi, '') // Remove javascript: protocol
      .replace(/on\w+\s*=/gi, '') // Remove inline event handlers
      .substring(0, 500); // Limit length
  }

  sanitizeHTML(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
  }

  checkRateLimit() {
    const now = Date.now();
    const windowStart = now - this.config.rateLimit.window;

    // Clean old timestamps
    this.messageTimestamps = this.messageTimestamps.filter(ts => ts > windowStart);

    if (this.messageTimestamps.length >= this.config.rateLimit.messages) {
      const nextAvailable = this.messageTimestamps[0] + this.config.rateLimit.window;
      const waitTime = Math.ceil((nextAvailable - now) / 1000);
      throw new Error(`Zu viele Nachrichten. Bitte warten Sie ${waitTime} Sekunden.`);
    }

    this.messageTimestamps.push(now);
  }

  checkVoiceSupport() {
    const hasRecognition = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    const hasSynthesis = 'speechSynthesis' in window;
    return {
      recognition: hasRecognition,
      synthesis: hasSynthesis,
      full: hasRecognition && hasSynthesis
    };
  }

  initSpeechRecognition() {
    if (!this.voiceSupported.recognition) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    this.recognition.lang = this.config.voiceLang;
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.maxAlternatives = 1;

    this.recognition.onstart = () => {
      this.isRecording = true;
      this.updateMicrophoneUI(true);
      this.showVoiceFeedback('Ich höre zu...');
    };

    this.recognition.onend = () => {
      this.isRecording = false;
      this.updateMicrophoneUI(false);
      this.hideVoiceFeedback();
    };

    this.recognition.onresult = (event) => {
      const transcript = event.results[event.results.length - 1][0].transcript;
      const isFinal = event.results[event.results.length - 1].isFinal;

      const input = document.getElementById('chat-widget-input');
      input.value = transcript;

      if (isFinal) {
        this.hideVoiceFeedback();
        // Auto-send if final result
        if (transcript.trim()) {
          setTimeout(() => this.handleSubmit(new Event('submit')), 500);
        }
      } else {
        this.showVoiceFeedback(transcript);
      }
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      this.isRecording = false;
      this.updateMicrophoneUI(false);
      this.hideVoiceFeedback();

      let errorMessage = 'Spracherkennung fehlgeschlagen';
      switch(event.error) {
        case 'no-speech':
          errorMessage = 'Keine Sprache erkannt';
          break;
        case 'audio-capture':
          errorMessage = 'Kein Mikrofon gefunden';
          break;
        case 'not-allowed':
          errorMessage = 'Mikrofonzugriff verweigert';
          break;
      }
      this.showVoiceFeedback(errorMessage, true);
      setTimeout(() => this.hideVoiceFeedback(), 3000);
    };
  }

  init() {
    this.createStyles();
    this.createWidget();
    this.attachEventListeners();
    if (this.config.enableVoice && this.voiceSupported.recognition) {
      this.initSpeechRecognition();
    }

    // Set up cleanup on page unload
    const unloadHandler = () => this.cleanup();
    window.addEventListener('beforeunload', unloadHandler);
    this.eventListeners.push({ element: window, event: 'beforeunload', handler: unloadHandler });
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
        color: white;
        font-size: 24px;
        font-weight: bold;
      }

      .chat-widget-trigger:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
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
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .voice-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4caf50;
        display: none;
        animation: pulse 1.5s infinite;
      }

      .voice-indicator.active {
        display: inline-block;
      }

      @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.1); }
        100% { opacity: 1; transform: scale(1); }
      }

      .chat-widget-close {
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        color: ${this.config.theme === 'dark' ? '#888' : '#666'};
        font-size: 18px;
        font-weight: bold;
        line-height: 1;
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
        position: relative;
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

      .speak-button {
        position: absolute;
        top: -8px;
        right: -8px;
        background: ${this.config.theme === 'dark' ? '#333' : 'white'};
        border: 1px solid ${this.config.theme === 'dark' ? '#555' : '#ddd'};
        border-radius: 50%;
        width: 28px;
        height: 28px;
        cursor: pointer;
        display: none;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
        font-size: 14px;
      }

      .chat-message.assistant:hover .speak-button {
        display: flex;
      }

      .speak-button:hover {
        background: ${this.config.theme === 'dark' ? '#444' : '#f5f5f5'};
      }

      .speak-button.speaking {
        display: flex;
        background: #4caf50;
        border-color: #4caf50;
      }


      .chat-widget-input-container {
        padding: 16px;
        border-top: 1px solid ${this.config.theme === 'dark' ? '#333' : '#e1e5e9'};
        background: ${this.config.theme === 'dark' ? '#1a1a1a' : 'white'};
      }

      .voice-feedback {
        background: ${this.config.theme === 'dark' ? '#2a2a2a' : '#f0f0f0'};
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 12px;
        color: ${this.config.theme === 'dark' ? '#aaa' : '#666'};
        display: none;
        align-items: center;
        gap: 8px;
      }

      .voice-feedback.active {
        display: flex;
      }

      .voice-feedback.error {
        background: #fee;
        color: #c53030;
        border: 1px solid #fed7d7;
      }

      .voice-wave {
        display: flex;
        align-items: center;
        gap: 2px;
        height: 16px;
      }

      .voice-wave-bar {
        width: 3px;
        background: #667eea;
        border-radius: 3px;
        animation: wave 0.5s ease-in-out infinite;
      }

      .voice-wave-bar:nth-child(1) { animation-delay: 0s; height: 8px; }
      .voice-wave-bar:nth-child(2) { animation-delay: 0.1s; height: 12px; }
      .voice-wave-bar:nth-child(3) { animation-delay: 0.2s; height: 16px; }
      .voice-wave-bar:nth-child(4) { animation-delay: 0.3s; height: 12px; }
      .voice-wave-bar:nth-child(5) { animation-delay: 0.4s; height: 8px; }

      @keyframes wave {
        0%, 100% { transform: scaleY(0.5); }
        50% { transform: scaleY(1); }
      }

      .chat-widget-input-form {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .chat-widget-input {
        width: 100%;
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
        box-sizing: border-box;
      }

      .chat-widget-input:focus {
        border-color: #667eea;
      }

      .input-buttons {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
        align-items: center;
      }

      .chat-widget-mic {
        background: ${this.config.theme === 'dark' ? '#2a2a2a' : 'white'};
        border: 1px solid ${this.config.theme === 'dark' ? '#444' : '#ddd'};
        border-radius: 50%;
        width: 40px;
        height: 40px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
        font-size: 20px;
        color: ${this.config.theme === 'dark' ? '#aaa' : '#666'};
      }

      .chat-widget-mic:hover {
        background: ${this.config.theme === 'dark' ? '#333' : '#f5f5f5'};
        transform: scale(1.05);
      }

      .chat-widget-mic.recording {
        background: #f44336;
        border-color: #f44336;
        animation: recording-pulse 1.5s infinite;
      }

      @keyframes recording-pulse {
        0% { box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(244, 67, 54, 0); }
        100% { box-shadow: 0 0 0 0 rgba(244, 67, 54, 0); }
      }

      .chat-widget-mic.recording {
        color: white;
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
        color: white;
        font-size: 18px;
        font-weight: bold;
      }

      .chat-widget-send:hover {
        transform: scale(1.05);
      }

      .chat-widget-send:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
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

      .voice-not-supported {
        background: #fff3cd;
        color: #856404;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 12px;
        border: 1px solid #ffeeba;
        margin-bottom: 8px;
      }

      /* Visually hidden but accessible to screen readers */
      .visually-hidden {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border-width: 0;
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

    const micButton = this.config.enableVoice && this.voiceSupported.recognition ? `
      <button type="button" class="chat-widget-mic" id="chat-widget-mic" title="Sprachaufnahme">🎤</button>
    ` : '';

    const voiceIndicator = this.config.enableVoice ? '<span class="voice-indicator" id="voice-indicator"></span>' : '';

    widget.innerHTML = `
      <button class="chat-widget-trigger" id="chat-widget-trigger">💬</button>
      <div class="chat-widget-panel" id="chat-widget-panel">
        <div class="chat-widget-header">
          <h3 class="chat-widget-title">
            ${this.config.title}
            ${voiceIndicator}
          </h3>
          <button class="chat-widget-close" id="chat-widget-close">×</button>
        </div>
        <div class="chat-widget-messages"
             id="chat-widget-messages"
             role="log"
             aria-live="polite"
             aria-label="Chat-Nachrichten"></div>
        <div class="chat-widget-input-container">
          <div class="voice-feedback" id="voice-feedback" role="status" aria-live="polite">
            <div class="voice-wave" aria-hidden="true">
              <div class="voice-wave-bar"></div>
              <div class="voice-wave-bar"></div>
              <div class="voice-wave-bar"></div>
              <div class="voice-wave-bar"></div>
              <div class="voice-wave-bar"></div>
            </div>
            <span id="voice-feedback-text"></span>
          </div>
          <form class="chat-widget-input-form" id="chat-widget-form">
            <label for="chat-widget-input" class="visually-hidden">Nachricht eingeben</label>
            <textarea
              class="chat-widget-input"
              id="chat-widget-input"
              placeholder="${this.sanitizeHTML(this.config.placeholder)}"
              rows="1"
              aria-label="Nachricht eingeben"
              maxlength="${this.config.maxMessageLength}"></textarea>
            <div class="input-buttons">
              ${micButton}
              <button type="submit"
                      class="chat-widget-send"
                      id="chat-widget-send"
                      aria-label="Nachricht senden">→</button>
            </div>
          </form>
        </div>
      </div>
    `;

    container.appendChild(widget);

    // Add welcome message
    this.addMessage('assistant', this.config.welcomeMessage);

    // Show voice support notice
    if (this.config.enableVoice && !this.voiceSupported.full) {
      this.showVoiceNotice();
    }
  }

  showVoiceNotice() {
    const messagesContainer = document.getElementById('chat-widget-messages');
    const notice = document.createElement('div');
    notice.className = 'voice-not-supported';

    if (!this.voiceSupported.recognition && !this.voiceSupported.synthesis) {
      notice.textContent = 'Sprachfunktionen werden von Ihrem Browser nicht unterstützt. Bitte verwenden Sie Chrome oder Edge.';
    } else if (!this.voiceSupported.recognition) {
      notice.textContent = 'Spracherkennung wird nicht unterstützt. Text-to-Speech ist verfügbar.';
    } else if (!this.voiceSupported.synthesis) {
      notice.textContent = 'Text-to-Speech wird nicht unterstützt. Spracherkennung ist verfügbar.';
    }

    messagesContainer.appendChild(notice);
  }

  attachEventListeners() {
    const trigger = document.getElementById('chat-widget-trigger');
    const panel = document.getElementById('chat-widget-panel');
    const closeBtn = document.getElementById('chat-widget-close');
    const form = document.getElementById('chat-widget-form');
    const input = document.getElementById('chat-widget-input');
    const micButton = document.getElementById('chat-widget-mic');

    if (trigger) {
      const triggerHandler = () => this.toggleWidget();
      trigger.addEventListener('click', triggerHandler);
      this.eventListeners.push({ element: trigger, event: 'click', handler: triggerHandler });
    }

    if (closeBtn) {
      const closeHandler = () => this.closeWidget();
      closeBtn.addEventListener('click', closeHandler);
      this.eventListeners.push({ element: closeBtn, event: 'click', handler: closeHandler });
    }

    if (form) {
      const submitHandler = (e) => this.handleSubmit(e);
      form.addEventListener('submit', submitHandler);
      this.eventListeners.push({ element: form, event: 'submit', handler: submitHandler });
    }

    if (input) {
      // Auto-resize textarea
      const inputHandler = (e) => {
        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px';
      };
      input.addEventListener('input', inputHandler);
      this.eventListeners.push({ element: input, event: 'input', handler: inputHandler });

      // Handle Enter key
      const keydownHandler = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleSubmit(e);
        }
      };
      input.addEventListener('keydown', keydownHandler);
      this.eventListeners.push({ element: input, event: 'keydown', handler: keydownHandler });
    }

    // Voice input button
    if (micButton && this.voiceSupported.recognition) {
      const micHandler = () => this.toggleVoiceRecording();
      micButton.addEventListener('click', micHandler);
      this.eventListeners.push({ element: micButton, event: 'click', handler: micHandler });
    }

    // Keyboard navigation
    const escapeHandler = (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.closeWidget();
      }
    };
    document.addEventListener('keydown', escapeHandler);
    this.eventListeners.push({ element: document, event: 'keydown', handler: escapeHandler });
  }

  toggleVoiceRecording() {
    if (!this.recognition) return;

    if (this.isRecording) {
      this.recognition.stop();
    } else {
      if (this.isSpeaking) {
        this.stopSpeaking();
      }
      try {
        this.recognition.start();
      } catch (error) {
        console.error('Failed to start recognition:', error);
        this.showVoiceFeedback('Fehler beim Starten der Spracherkennung', true);
      }
    }
  }

  updateMicrophoneUI(isRecording) {
    const micButton = document.getElementById('chat-widget-mic');
    const voiceIndicator = document.getElementById('voice-indicator');

    if (micButton) {
      if (isRecording) {
        micButton.classList.add('recording');
      } else {
        micButton.classList.remove('recording');
      }
    }

    if (voiceIndicator) {
      if (isRecording) {
        voiceIndicator.classList.add('active');
      } else {
        voiceIndicator.classList.remove('active');
      }
    }
  }

  showVoiceFeedback(text, isError = false) {
    const feedback = document.getElementById('voice-feedback');
    const feedbackText = document.getElementById('voice-feedback-text');

    if (feedback && feedbackText) {
      feedbackText.textContent = text;
      feedback.classList.add('active');

      if (isError) {
        feedback.classList.add('error');
      } else {
        feedback.classList.remove('error');
      }
    }
  }

  hideVoiceFeedback() {
    const feedback = document.getElementById('voice-feedback');
    if (feedback) {
      feedback.classList.remove('active', 'error');
    }
  }

  toggleWidget() {
    const panel = document.getElementById('chat-widget-panel');
    const trigger = document.getElementById('chat-widget-trigger');
    this.isOpen = !this.isOpen;

    if (panel && trigger) {
      if (this.isOpen) {
        panel.classList.add('open');
        panel.setAttribute('aria-hidden', 'false');
        trigger.setAttribute('aria-expanded', 'true');
        const input = document.getElementById('chat-widget-input');
        if (input) input.focus();
      } else {
        panel.classList.remove('open');
        panel.setAttribute('aria-hidden', 'true');
        trigger.setAttribute('aria-expanded', 'false');
      }
    }
  }

  closeWidget() {
    const panel = document.getElementById('chat-widget-panel');
    const trigger = document.getElementById('chat-widget-trigger');
    this.isOpen = false;

    if (panel) {
      panel.classList.remove('open');
      panel.setAttribute('aria-hidden', 'true');
    }

    if (trigger) {
      trigger.setAttribute('aria-expanded', 'false');
    }

    // Stop any ongoing speech or recording
    if (this.isSpeaking) {
      this.stopSpeaking();
    }
    if (this.isRecording && this.recognition) {
      this.recognition.stop();
    }
  }

  validateMessage(message) {
    if (typeof message !== 'string') return false;
    if (message.length === 0) return false;
    if (message.length > this.config.maxMessageLength) return false;

    // Check for common XSS patterns
    const dangerousPatterns = [
      /<script/i,
      /javascript:/i,
      /on\w+\s*=/i,
      /<iframe/i,
      /<object/i,
      /<embed/i
    ];

    for (const pattern of dangerousPatterns) {
      if (pattern.test(message)) {
        console.warn('Potentially dangerous content detected in message');
        return false;
      }
    }

    return true;
  }

  async handleSubmit(e) {
    e.preventDefault();

    if (this.isStreaming) return;

    const input = document.getElementById('chat-widget-input');
    if (!input) return;

    const message = input.value.trim();

    // Validate message
    if (!this.validateMessage(message)) {
      if (message.length > this.config.maxMessageLength) {
        this.showVoiceFeedback(`Nachricht zu lang (max ${this.config.maxMessageLength} Zeichen)`, true);
      }
      return;
    }

    if (!message) return;

    // Check rate limit
    try {
      this.checkRateLimit();
    } catch (error) {
      this.showRateLimitWarning(error.message);
      return;
    }

    // Stop any ongoing speech or recording
    if (this.isSpeaking) {
      this.stopSpeaking();
    }
    if (this.isRecording) {
      this.recognition.stop();
    }

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
      this.addMessage('assistant', 'Entschuldigung, es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.');
      this.addError(`Error: ${error.message}`);
    }
  }

  async sendMessage(message, retryCount = 0) {
    this.isStreaming = true;

    // Create abort controller for this request
    this.abortController = new AbortController();

    const payload = {
      message: this.sanitizeText(message),
      session_id: this.sessionId,
      user_id: 'widget-user',
      search_type: 'hybrid'
    };

    try {
      const response = await fetch(`${this.config.apiUrl}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify(payload),
        signal: this.abortController.signal
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
                    // Auto-speak the response if enabled
                    if (this.config.autoSpeak && fullResponse) {
                      this.speak(fullResponse);
                    }
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
        this.abortController = null;
      }

      // Add speak button for manual playback
      if (this.voiceSupported.synthesis && fullResponse) {
        this.addSpeakButton(messageContainer, fullResponse);
      }

      // Add tools info if any were used
      if (tools && tools.length > 0) {
        const toolInfo = document.createElement('div');
        toolInfo.className = 'chat-widget-tools';
        toolInfo.textContent = `Verwendete Tools: ${tools.map(t => this.sanitizeText(t.tool_name)).join(', ')}`;
        messageContainer.appendChild(toolInfo);
      }

      this.scrollToBottom();

    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request was aborted');
        return;
      }

      // Retry logic
      if (retryCount < this.config.maxRetries) {
        console.log(`Retrying... (${retryCount + 1}/${this.config.maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, this.config.retryDelay * (retryCount + 1)));
        return this.sendMessage(message, retryCount + 1);
      }

      throw error;
    }
  }

  addSpeakButton(messageContainer, text) {
    const button = document.createElement('button');
    button.className = 'speak-button';
    button.title = 'Nachricht vorlesen';
    button.innerHTML = '🔊';

    button.addEventListener('click', (e) => {
      e.stopPropagation();
      if (this.isSpeaking && button.classList.contains('speaking')) {
        this.stopSpeaking();
      } else {
        this.speak(text, button);
      }
    });

    const contentElement = messageContainer.querySelector('.chat-message-content');
    contentElement.appendChild(button);
  }

  speak(text, button = null) {
    if (!this.voiceSupported.synthesis) return;

    // Stop any ongoing speech
    this.stopSpeaking();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = this.config.voiceLang;
    utterance.rate = this.config.voiceRate;
    utterance.pitch = this.config.voicePitch;

    // Find the best German voice if available
    const voices = this.synthesis.getVoices();
    const germanVoice = voices.find(voice =>
      voice.lang.startsWith('de') && voice.localService
    ) || voices.find(voice => voice.lang.startsWith('de'));

    if (germanVoice) {
      utterance.voice = germanVoice;
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
      if (button) {
        button.classList.add('speaking');
      }
      // Stop recording if active
      if (this.isRecording) {
        this.recognition.stop();
      }
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      if (button) {
        button.classList.remove('speaking');
      }
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      this.isSpeaking = false;
      if (button) {
        button.classList.remove('speaking');
      }
    };

    this.currentUtterance = utterance;
    this.synthesis.speak(utterance);
  }

  stopSpeaking() {
    if (this.synthesis.speaking) {
      this.synthesis.cancel();
    }
    this.isSpeaking = false;

    // Remove speaking class from all buttons
    const speakButtons = document.querySelectorAll('.speak-button.speaking');
    speakButtons.forEach(button => button.classList.remove('speaking'));
  }

  addMessage(role, content) {
    const messagesContainer = document.getElementById('chat-widget-messages');
    if (!messagesContainer) return null;

    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'chat-message-avatar';
    avatar.setAttribute('aria-hidden', 'true');
    avatar.textContent = role === 'user' ? 'Sie' : 'R';

    const messageContent = document.createElement('div');
    messageContent.className = 'chat-message-content';
    messageContent.textContent = this.sanitizeText(content);

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
    avatar.textContent = 'R';

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

  cleanup() {
    console.log('Cleaning up chat widget...');

    // Stop speech recognition
    if (this.recognition) {
      try {
        this.recognition.stop();
        this.recognition.onstart = null;
        this.recognition.onend = null;
        this.recognition.onresult = null;
        this.recognition.onerror = null;
      } catch (e) {
        // Ignore errors during cleanup
      }
    }

    // Stop speech synthesis
    this.stopSpeaking();

    // Abort any ongoing requests
    if (this.abortController) {
      this.abortController.abort();
    }

    // Remove all event listeners
    this.eventListeners.forEach(({ element, event, handler }) => {
      if (element) {
        element.removeEventListener(event, handler);
      }
    });
    this.eventListeners = [];

    // Remove widget from DOM
    const container = document.querySelector('.chat-widget-container');
    if (container) {
      container.remove();
    }

    // Remove styles
    const styles = document.getElementById('chat-widget-styles');
    if (styles) {
      styles.remove();
    }
  }

  // Public method to destroy the widget
  destroy() {
    this.cleanup();
  }
}

// Auto-initialize if config is provided
if (typeof window !== 'undefined' && window.ChatWidgetConfig) {
  new ChatWidget(window.ChatWidgetConfig);
}